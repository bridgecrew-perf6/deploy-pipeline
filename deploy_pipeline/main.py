import argparse
import logging as log
import os
import sys
import yaml
from itertools import chain
from deploy_pipeline import __cli_name__
import deploy_pipeline.vars.parsers as varp
from deploy_pipeline.labels.matching import query_from_string, query_from_object, new_query, Operator, LabelMatch
from deploy_pipeline.labels.utils import with_data
from deploy_pipeline.labels.joining import LabelJoin
from deploy_pipeline.labels.grouping import LabelGroup
from deploy_pipeline.pipeline.config import validate_pipeline
from deploy_pipeline.pipeline.pipeline import load_pipeline_from_config, Stage
from deploy_pipeline.pipeline.templates import get_template


CLI_NAME = __cli_name__
logger = log.getLogger(CLI_NAME)

DEFAULT_CONFIG = {
    'global': {
        'general': {'log_level': 'DEBUG', 'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'},
    }
}


def deploy_pipeline(args: dict) -> int:
    # config shim
    config = DEFAULT_CONFIG

    # init the logger
    logger.setLevel(config['global']['general']['log_level'])

    # stdout log handler
    handler = log.StreamHandler(sys.stdout)
    handler.setFormatter(log.Formatter(config['global']['general']['log_format']))

    # attach stdout handler
    logger.addHandler(handler)

    logger.info(f"Starting {CLI_NAME}")
    # echo out the arguments, cause its SUPER hard to find the provided args in gitlab pipelines
    for arg_k, arg_v in args.items():
        logger.debug(f"Captured Argument '{arg_k}': {arg_v}")

    # suck the deploy configs into the config dict
    logger.info("Parsing Additional Config")
    for config_f in args.get('config', []):
        with open(config_f) as f:
            config.update(yaml.safe_load(f))
    logger.debug("Completed Parsing Additional Config")

    # suck in the variables
    # going full steam ahead on a functional paradigm apparently, i wouldn't think the number of variables parsed
    # would be an issue for all the merging but time will tell.
    logger.info(f"Parsing Input Variables")
    variables = {}
    # files first
    for var_file in args['var_files']:
        variables = varp.with_var_file(var_file, variables)

    # then cli vars
    for var in args['vars']:
        variables = varp.with_var(var, variables)

    # then environment vars
    for env_var in (k for k in os.environ if k.startswith(varp.ENV_VAR_PREFIX)):
        variables = varp.with_env_var(env_var, variables)

    logger.info(f"Parsing Pipeline File: {args['pipeline']}")

    # read and validate our pipeline config file
    with open(args['pipeline']) as f:
        pipeline_config = validate_pipeline(yaml.safe_load(f), ("foo",))

    # attempt at the single responsibility principle.  this makes the pipeline loader responsible for parsing out
    # the pipeline yaml into the pipeline object (a little factory).  this frees the pipeline object from having to
    # maintain any knowledge of the pipeline yaml.
    pipeline = load_pipeline_from_config(pipeline_config)

    # do any initial host queries
    host_queries = filter(None, chain(
        # take advantage of the fact that currently "host_order_label" is required in the pipeline yaml
        # to make sure we don't completely bork an environment by doing *everything* at once, it just so happens
        # that host-order-label is simply an exists query of the host labels.
        [query_from_string(pipeline_config['host_order_label'])],
        # add in any pipeline level host queries
        [query_from_object(hq_pipe) for hq_pipe in pipeline_config.get('selectors', {}).get('host', [])],
        # add in any queries supplied at the command line
        [query_from_string(hq_arg) for hq_arg in args['host_selector']]
    ))

    host_query = LabelMatch(config['hosts'], 'labels')
    host_query.add_queries(host_queries)
    matched_hosts = with_data(host_query.do(), config['hosts'])
    if not matched_hosts:
        logger.error("No Host(s) Matching Label Query")
        return 1

    # do any initial package queries
    package_queries = filter(None, chain(
        # filer anything passed in via the command line
        [query_from_string(q) for q in args['package_selector']],
        # filter out any pipeline level package queries
        [query_from_object(pq_pipe) for pq_pipe in pipeline_config.get('selectors', {}).get('package', [])]
    ))

    package_query = LabelMatch(config['packages'], 'labels')
    package_query.add_queries(package_queries)
    matched_packages = package_query.do()
    if not matched_packages:
        logger.error("No Package(s) Matched Label Query")
        return 1

    # now join the resolved hosts and packages, arguably I should create a super class or extend the LabelMatch
    # but the compartmentalized functions seem to work for now.
    host_packages = LabelJoin(matched_hosts, 'packages').match(matched_packages)

    # groups joined hosts and packages by the specified label. sigh, I'm using were using a bunch of with_data which
    # is just a thin wrapper around a dict comprehension, this could lead to performance issues if I am not careful
    host_order = LabelGroup(
        with_data(host_packages.keys(), config['hosts']),
        "labels"
    ).group(pipeline_config['host_order_label'])
    if not host_order:
        logger.error("Unable to Determine Group(s)")
        return 1

    job_stages = Stage(pipeline, host_order.keys())

    # attempting to avoid useless layers of abstraction by leaving the pipeline vars a plain old dict
    pipeline_template = get_template(pipeline.template)
    pipeline_template_vars = {
        'stages': [],
        'includes': pipeline_config.get('includes', []),
        'jobs': [],
        'vars': variables,
    }

    # put here for logging purposes, otherwise we could just use a list comprehension in the template variables
    for s in job_stages.get_stages():
        logger.info(f'Processing Stage: {s}')
        pipeline_template_vars['stages'].append(s)

    # provide fully hydrated dicts to allow per stage lookups
    matched_hosts = with_data(host_packages.keys(), config['hosts'])
    matched_packages = with_data({p for pg in host_packages.values() for p in pg}, config['packages'])

    for stage, phase_name, stage_name, job in job_stages.get_stage_jobs():
        logger.info(f'Processing Stage: {stage_name} - Job: {job.name}')

        # load the template associated with this stage
        stage_template = get_template(job.template)

        # at this point we have probably narrowed down the list of hosts and packages we are going to install to,
        # however we need to take it a step further.  by default the job query
        # each job provides the ability to add host and package selectors
        # of their own to be able to include (or exclude) hosts and packages at that particular phase.
        matched_stage_hosts = LabelMatch(matched_hosts, 'labels').add_queries(chain(
            [new_query(pipeline_config['host_order_label'], Operator.In, [stage])],
            [query_from_object(hq) for hq in job.host_selectors]
        )).do()

        if not matched_stage_hosts:
            logger.info(f'No Matched Hosts for {stage_name}: {job.name}')

        # narrow the scope to only the packages included in this phase
        matched_stage_packages = LabelMatch(matched_packages, 'labels').add_queries([
            query_from_object(pq) for pq in job.package_selectors
        ]).do()

        if not matched_stage_packages:
            logger.info(f'No Matched Packages for {stage_name}: {job.name}')

        # join the packages and hosts to ensure we only get supported host/package combinations
        #
        # doing the queries separately cuts down on the complexity of the query system in general (not having to
        # worry about joining things and taking a union), but in a way it cuts down on testability.  we can (and should)
        # test the individual components, but any extension of this system needs to take into account that you *MUST*
        # join hosts and packages to do anything useful with them.
        stage_hosts_packages = LabelJoin(
            with_data(matched_stage_hosts, matched_hosts), 'packages'
        ).match(matched_stage_packages)

        for hostname, packages in stage_hosts_packages.items():
            logger.info(f'Rendering Job Template for {hostname}: {", ".join(packages)}')

            # setup the variables that will be shared with the template, for right now these are all of the variables
            # that *any* job would need. i am explicitly providing key/value pairs here for the most part so the
            # underlying jinja templates don't need to change if the domain object signature changes.  heh, this shows
            # how much faith i have in the initial design.
            pipeline_template_vars['jobs'].append(stage_template.render({
                "stagename": stage_name,
                "jobname": job.name,
                "hostname": hostname,
                "packages": sorted(packages),
                "vars": variables.get(job.var_key, {})
            }))

    # write to a file if specified, otherwise go ahead and dump it to stdout
    rendered_pipeline = pipeline_template.render(pipeline_template_vars).strip()
    if args['output']:
        logger.info(f'Writing Pipeline File: {args["output"]}')
        with open(args['output'], 'w') as f:
            f.write(rendered_pipeline)
    else:
        print(rendered_pipeline)

    return 0


def main():
    # input arguments
    parser = argparse.ArgumentParser()

    parser.add_argument('--pipeline', metavar='<path to pipeline config>.yml',
                        help='path to the deployment pipeline config yaml file', required=True)

    parser.add_argument('--output', metavar='<path to gitlab-ci compatible yml',
                        help='path to the produced gitlab ci yml file')

    parser.add_argument('--config', metavar='<path to host and package config>.yml',
                        help='path to the host and package config yaml files (used for label selectors)', required=True,
                        nargs='+')

    parser.add_argument('--host-selector', metavar="<label query>",
                        help='initial host selector(s)',
                        nargs='+', default=[])

    parser.add_argument('--package-selector', metavar="<label query>", help='initial package selector(s)',
                        nargs='+', default=[])

    parser.add_argument('--vars', metavar="key=value", help='variables to pass',
                        nargs='+', default=[])

    parser.add_argument('--var-files', metavar="<path to var file>.json", help='path to a variable file in json format',
                        nargs='+', default=[])

    args = parser.parse_args()
    exit(int(deploy_pipeline(vars(args))))
