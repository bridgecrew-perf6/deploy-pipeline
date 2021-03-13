from collections import defaultdict
from itertools import product
from typing import Dict, List, Union, Tuple, Iterable


# a job is tied to a phase, and even though a phase can only exist once, that doesn't mean a job will run only once.
# the job will run 1 * number of stages (which is a cartesian product of stages and phases, i.e. 0-changebroker,
# 0-partition, etc).
class Job:
    _job_name: str

    phase: str
    template: str
    var_key: Union[str, None]

    host_selectors: List
    package_selectors: List

    @property
    def name(self):
        return self._job_name

    def __init__(self, job_name: str, phase_name: str):
        if not job_name:
            raise JobException(f'Job Name is Required')

        self._job_name = job_name

        self.phase = phase_name
        self.template = ""
        self.var_key = None

        # strictly speaking nothing super bad will happen if the selectors are duplicated, ya we have to do more work
        # parsing the same thing over and over again, but the world won't end (like in the case of the order of phases).
        #
        # avoid the un-necessary overhead of getters and settings (not really pythonic) and just allow access to the
        # mutable lists.
        self.host_selectors = []
        self.package_selectors = []


# a pipeline is the wrapper around phases and jobs.  it is responsible for creating the stages (remember the product of
# stage and phase).
class Pipeline:
    _phases: List

    _job_names: Dict[str, Job]
    _job_phases: Dict[str, List[Job]]

    template: str
    includes: List
    host_selectors = List
    package_selectors = List

    def __init__(self):
        self._phases = []

        # see the explanation in the add_job
        self._job_names = {}
        self._job_phases = defaultdict(list)

        self.template = ""
        self.includes = []
        self.host_selectors = []
        self.package_selectors = []

    def add_job(self, job: Job) -> "Pipeline":
        # there should be a question here as to why uniqueness is being enforced on the job name and really the only
        # answers I can come up with is:
        # 1. Gitlab does it that way (the main reason)
        # 2. The setup of the wrapper yaml (the pipeline) kinda mandates a unique name since the jobs are put under the
        #    same key, rather than being split into their appropriate phase.
        if job.name in self._job_names:
            raise JobException(f'Duplicate Job Name: {job.name}')

        # a job should belong to a pre-existing phase
        if job.phase not in self._phases:
            raise InvalidPhaseException(f'Invalid Phase Name: {job.phase}')

        # store the job and the phase
        self._job_names[job.name] = job
        self._job_phases[job.phase].append(job)

        return self

    def get_jobs_by_phase(self, phase_name) -> Iterable[Job]:
        yield from self._job_phases[phase_name]

    def add_phase(self, phase_name: str) -> "Pipeline":
        # validate the phase name is unique (we shouldn't have ANY duplicates)
        if phase_name in self._phases:
            raise DuplicatePhaseException(f'Duplicate Phase Name: {phase_name}')

        self._phases.append(phase_name)
        return self

    def get_phases(self) -> Iterable[str]:
        yield from self._phases


# a stage represents a resolved stage + phase.
class Stage:
    _pipeline: Pipeline
    _order_groups: List

    def __init__(self, pipeline: Pipeline, order_groups: Iterable, reverse: bool = False):
        self._pipeline = pipeline
        self._order_groups = sorted(order_groups, reverse=reverse)

    def _get_stages(self) -> Tuple[str, str, str]:
        for stage, phase_name in product(self._order_groups, self._pipeline.get_phases()):
            yield stage, phase_name, f'{stage}-{phase_name}'

    def get_stages(self) -> str:
        for _, _, stage in self._get_stages():
            yield stage

    def get_stage_jobs(self) -> Tuple[str, str, str, Job]:
        for stage, phase_name, stage_name in self._get_stages():
            for job in self._pipeline.get_jobs_by_phase(phase_name):
                yield stage, phase_name, stage_name, job


def load_pipeline_from_config(pipeline_config: Dict) -> Pipeline:
    # instantiate a new pipeline
    pipeline = Pipeline()

    pipeline.template = pipeline_config['template']
    pipeline.includes = pipeline_config.get('includes', [])

    # load all of the phases for this pipeline
    for phase in pipeline_config['phases']:
        pipeline.add_phase(phase)

    # load all of the jobs
    for job_name, job_v in pipeline_config['jobs'].items():
        job = Job(job_name, job_v['phase'])
        job.template = job_v['template']
        job.var_key = job_v['var_key']

        # make the author be EXPLICIT about the selectors they want to use (otherwise bad things can happen),
        # if they want to include all packages, just pass an empty array for a selector
        job.host_selectors.extend(job_v['selectors']['host'])
        job.package_selectors.extend(job_v['selectors']['package'])

        pipeline.add_job(job)

    return pipeline


class PhaseException(Exception):
    pass


class DuplicatePhaseException(PhaseException):
    pass


class InvalidPhaseException(PhaseException):
    pass


class JobException(Exception):
    pass


class InvalidJobTemplateException(JobException):
    pass
