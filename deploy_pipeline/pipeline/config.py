from copy import deepcopy
from typing import Dict, Set, Tuple
from deploy_pipeline.labels.matching import query_from_object
from deploy_pipeline.pipeline.utils import with_full_path


def copy_and_init_path(func):
    def wrapped_func(*args):
        # don't modify the caller's data, this could get EXPENSIVE if we are called lots of times with giant
        # pipelines it doesn't seem likely but i'm just pointing it out.
        inputs = deepcopy(args[0])
        # provides a way to debug if necessary
        path_keys = args[1] if len(args) > 1 else ("<root>",)
        return func(inputs, path_keys)

    return wrapped_func


@copy_and_init_path
def validate_pipeline(pipeline_template: Dict, path_keys: Tuple) -> Dict:
    # 'the key at this level': True (required to be present) or False (optional)
    level_keys = {
        'phases': True, 'template': True, 'includes': False,
        'selectors': False, 'host_order_label': True, 'jobs': True
    }

    if missing_keys := _validate_keys(
            _filter_required_keys(level_keys),
            _filter_present_keys(pipeline_template)
    ):
        raise RootValidationException(f"Missing Required Key(s): {','.join(missing_keys)}", path_keys)

    # phases needs to be an List
    #
    # look i know that duck typing should be used here, but given that a screw up in the pipeline could an outage,
    # i am trying to make things as *safe* as possible.
    if type(pipeline_template['phases']) is not list:
        raise RootValidationException(f'Invalid phases Key: List is Required', path_keys)

    # template needs to be present
    pipeline_template['template'] = with_full_path(pipeline_template['template'])

    # if provided, includes should be valid file paths
    pipeline_template['includes'] = [with_full_path(i) for i in pipeline_template.get('includes', [])]

    # if provided, selectors should be valid
    if selectors := pipeline_template.get('selectors', {}):
        pipeline_template['selectors'] = validate_selectors(selectors, path_keys)

    # jobs should be a dict
    pipeline_template['jobs'] = validate_jobs(pipeline_template['jobs'], path_keys + ('jobs',))

    return pipeline_template


@copy_and_init_path
def validate_jobs(jobs: Dict, path_keys: Tuple) -> Dict:
    # jobs should be a dict
    if type(jobs) is not dict:
        raise JobValidationException(f'Invalid Key: Dict is Required', path_keys)

    # validate the individual jobs
    for job_k, job_v in jobs.items():
        jobs[job_k] = validate_job(job_v, path_keys + (job_k,))

    return jobs


@copy_and_init_path
def validate_job(job: Dict, path_keys: Tuple) -> Dict:
    level_keys = {'phase': True, 'var_key': True, 'template': True, 'selectors': True}

    if missing_job_keys := _validate_keys(_filter_required_keys(level_keys), _filter_present_keys(job)):
        raise JobValidationException(f"Missing Job Key(s): {', '.join(missing_job_keys)}", path_keys)

    # validate the job template can be found
    job['template'] = with_full_path(job['template'])

    job['selectors'] = validate_selectors(job['selectors'], path_keys + ('selectors',))

    return job


@copy_and_init_path
def validate_selectors(selectors: Dict, path_keys: Tuple) -> Dict:
    level_keys = {'host': False, 'package': False}

    # selectors should be a dict
    if type(selectors) is not dict:
        raise SelectorValidationException(f"Invalid Selectors: Dict is Required", path_keys)

    if missing_keys := _validate_keys(_filter_required_keys(level_keys), _filter_present_keys(selectors)):
        raise SelectorValidationException(f"Missing Required Selector(s): {', '.join(missing_keys)}", path_keys)

    # host and package should be a list
    for level_key in level_keys:
        if type(selectors.get(level_key, [])) is not list:
            raise SelectorValidationException(f"Invalid Selector: Expected '{level_key}' List", path_keys)

    # generates a pretty-ish
    for selector_key, selector_query in (
            (selector_type, selector_query)
            for selector_type, selector_type_value in selectors.items() for selector_query in selector_type_value
    ):
        validate_formed_selectors(selector_query, path_keys + (selector_key,))

    return selectors


@copy_and_init_path
def validate_formed_selectors(selector: Dict, path_keys: Tuple) -> Dict:
    # shove the selector into the query_from_object function which should validate it enough for our purposes
    # it does do minor object construction, but it's a namedtuple for right now which should be pretty lightweight
    try:
        query_from_object(selector)
    except KeyError:
        # query from object just just calls __get__ on whatever is passed in and throws a key error if it's not found
        # we should handle the exception and add some additional context so finding the error isn't a pita.
        raise SelectorValidationException(f'Malformed Selector: {selector}', path_keys) from None

    return selector


def _validate_keys(required: Set, present: Set) -> Set:
    return required - present


def _filter_present_keys(present: Dict) -> Set:
    return {p for p in present.keys() if not p.startswith('.')}


def _filter_required_keys(required: Dict) -> Set:
    return {k for k, v in required.items() if v}


class PipelineValidationException(Exception):
    def __init__(self, msg: str, key_path: Tuple):
        super().__init__(f"{msg} [Path: {'->'.join(key_path)}]")
    pass


class RootValidationException(PipelineValidationException):
    pass


class JobValidationException(PipelineValidationException):
    pass


class SelectorValidationException(PipelineValidationException):
    pass
