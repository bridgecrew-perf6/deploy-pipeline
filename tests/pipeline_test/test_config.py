import pytest
import os
import deploy_pipeline.pipeline.config as deploy_config
from tests.conftest import config_dir
from deploy_pipeline.pipeline.utils import FileNotFoundException
from functools import partial


@pytest.mark.parametrize("fn_inputs,fn_to_call", [
    (
            {
                "host": [{"key": "key", "operator": "In", "values": ["values_1"]}]
            },
            deploy_config.validate_selectors
    ),
    (
            {
                "job_1": {
                    "phase": "phase_1",
                    "variables": {
                        "type": "var_type"
                    },
                    "template": os.path.join(config_dir(), "valid_file"),
                    "selectors": {
                        "host": [{"key": "key", "operator": "In", "values": ["values_1"]}]
                    }
                }
            },
            deploy_config.validate_jobs
    ),
    (
            {
                'phases': ['phase_1'],
                "template": os.path.join(config_dir(), "valid_file"),
                "host_order_label": "foo",
                "includes": [],
                "jobs": {
                    "job_1": {
                        "phase": "phase_1",
                        "variables": {
                            "type": "var_type"
                        },
                        "template": os.path.join(config_dir(), "valid_file"),
                        "selectors": {
                            "host": [{"key": "key", "operator": "In", "values": ["values_1"]}]
                        }
                    }
                }
            },
            deploy_config.validate_pipeline
    ),
    (
            {
                'phases': ['phase_1'],
                "template": os.path.join(config_dir(), "valid_file"),
                "host_order_label": "foo",
                "includes": [],
                "selectors": {
                    "host": [],
                    "package": [],
                },
                "jobs": {
                    "job_1": {
                        "phase": "phase_1",
                        "variables": {
                            "type": "var_type"
                        },
                        "template": os.path.join(config_dir(), "valid_file"),
                        "selectors": {
                            "host": [{"key": "key", "operator": "In", "values": ["values_1"]}]
                        }
                    }
                }
            },
            deploy_config.validate_pipeline
    )
])
def test_valid_config(fn_inputs, fn_to_call):
    assert fn_to_call(fn_inputs) == fn_inputs


@pytest.mark.parametrize("fn_input,fn_to_call,throws", [
    (
            "a string",
            deploy_config.validate_selectors,
            deploy_config.SelectorValidationException
    ),
    (
            {
                "host": {}
            },
            deploy_config.validate_selectors,
            deploy_config.SelectorValidationException
    ),
    (
            {
                "host": [{"key_invalid": "key", "operator": "In", "values": ["values_1"]}],
                "package": [{"key": "key_2", "operator": "In", "values": ["values_2"]}]
            },
            deploy_config.validate_selectors,
            deploy_config.SelectorValidationException
    ),
    (
            {
                "job_1": {
                    "phase": "missing_required_key_template",
                    "variables": {
                        "type": "var_type"
                    },
                    "selectors": {
                        "host": [{"key": "key", "operator": "In", "values": ["values_1"]}]
                    }
                }
            },
            deploy_config.validate_jobs,
            deploy_config.JobValidationException
    ),
    (
            {
                "job_1": {
                    "phase": "phase_1",
                    "variables": {
                        "type": "var_type"
                    },
                    "template": "invalid_file_path",
                    "selectors": {
                        "host": [{"key": "key", "operator": "In", "values": ["values_1"]}]
                    }
                }
            },
            deploy_config.validate_jobs,
            FileNotFoundException
    ),
    (
            {
                "template": os.path.join(config_dir(), "valid_file"),
                "host_order_label": "foo",
                "includes": [],
                "selectors": {
                    "host": [],
                    "package": [],
                },
                "jobs": {
                    "job_1": {
                        "phase": "phase_1",
                        "variables": {
                            "type": "var_type"
                        },
                        "template": os.path.join(config_dir(), "valid_file"),
                        "selectors": {
                            "host": [{"key": "key", "operator": "In", "values": ["values_1"]}]
                        }
                    }
                }
            },
            deploy_config.validate_pipeline,
            deploy_config.RootValidationException
    ),
    (
            {
                'phases': ['phase_1'],
                "host_order_label": "foo",
                "includes": [],
                "selectors": {
                    "host": [],
                    "package": [],
                },
                "jobs": {
                    "job_1": {
                        "phase": "phase_1",
                        "variables": {
                            "type": "var_type"
                        },
                        "template": os.path.join(config_dir(), "valid_file"),
                        "selectors": {
                            "host": [{"key": "key", "operator": "In", "values": ["values_1"]}]
                        }
                    }
                }
            },
            deploy_config.validate_pipeline,
            deploy_config.RootValidationException
    )
])
def test_invalid_config(fn_input, fn_to_call, throws):
    with pytest.raises(throws):
        fn_to_call(fn_input)
