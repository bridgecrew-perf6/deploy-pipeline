from deploy_pipeline.pipeline.config import Pipeline, Stage, Job


def test_stage_generation(pipeline_phases, pipeline_stages):
    pipeline = Pipeline()

    for pipeline_phase in pipeline_phases:
        pipeline.add_phase(pipeline_phase)

    job_stages = Stage(pipeline, pipeline_stages)
    stages = [stage for stage in job_stages.get_stages()]
    assert stages == ["0-pre", "0-changebroker", "0-partition",
                      "1-pre", "1-changebroker", "1-partition",
                      "2-pre", "2-changebroker", "2-partition"]


def test_job_generation(pipeline_phases, pipeline_stages, pipeline_jobs):
    pipeline = Pipeline()

    for pipeline_phase in pipeline_phases:
        pipeline.add_phase(pipeline_phase)

    for job_k, job_v in pipeline_jobs.items():
        job = Job(job_k, job_v['phase'])
        pipeline.add_job(job)

    stages = Stage(pipeline, pipeline_stages)
    jobs = [(stage, phase, stage_name, job.name) for stage, phase, stage_name, job in stages.get_stage_jobs()]

    assert jobs == [(0, 'changebroker', '0-changebroker', 'job-changebroker'),
                    (0, 'partition', '0-partition', 'job-partition'),
                    (1, 'changebroker', '1-changebroker', 'job-changebroker'),
                    (1, 'partition', '1-partition', 'job-partition'),
                    (2, 'changebroker', '2-changebroker', 'job-changebroker'),
                    (2, 'partition', '2-partition', 'job-partition')]
