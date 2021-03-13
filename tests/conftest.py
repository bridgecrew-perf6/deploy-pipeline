import pytest
import os


def config_dir():
    return os.path.join(os.path.dirname(__file__), "etc")


@pytest.fixture
def host_data():
    return {
        "ora-del-sup-001": {
            "labels": {
                "pogo.deploy.environment": "prod-aws",
                "pogo.deploy.stage": 0,
                "pogo.test.data": "True",
            },
            "name": "ORA_DEL_SUP_001",
            "packages": ["property01", "property07", "property13", "property19", "property25", "property31"]
        },
        "ora-del-sup-007": {
            "labels": {
                "pogo.deploy.environment": "prod-aws",
                "pogo.deploy.stage": 1,
                "pogo.test.data": "True",
            },
            "name": "ORA_DEL_SUP_007",
            "packages": ["property01", "property07", "property13", "property19", "property25", "property31"]
        },
        "orb-del-sup-001": {
            "labels": {
                "pogo.deploy.environment": "prod-aws",
                "pogo.deploy.stage": 0,
                "pogo.test.data": "True",
            },
            "name": "ORB_DEL_SUP_001",
            "packages": ["property01", "property07", "property13", "property19", "property25", "property31"]
        },
        "orc-del-sup-001": {
            "labels": {
                "pogo.deploy.environment": "prod-aws",
                "pogo.deploy.stage": 1,
            },
            "name": "ORC_DEL_SUP_001",
            "packages": ["property01", "property07", "property13", "property19", "property25", "property31"]
        },
        "se3-del-sup-001": {
            "labels": {
                "pogo.deploy.environment": "prod-se3",
                "pogo.deploy.stage": 0,
            },
            "name": "SE3_DEL_SUP_001",
            "packages": ["property01", "property07", "property13", "property19", "property25", "property31"]
        },
        "se3-del-sup-007": {
            "labels": {
                "pogo.deploy.environment": "prod-se3",
                "pogo.deploy.stage": 1,
            },
            "name": "SE3_DEL_SUP_007",
            "packages": ["property01", "property07", "property13", "property19", "property25", "property31"]
        },
    }


@pytest.fixture
def pipeline_phases():
    return ["pre", "changebroker", "partition"]


@pytest.fixture
def pipeline_stages():
    return [0, 1, 2]


@pytest.fixture
def pipeline_jobs():
    return {
        "job-changebroker": {
            "phase": "changebroker"
        },
        "job-partition": {
            "phase": "partition"
        }
    }
