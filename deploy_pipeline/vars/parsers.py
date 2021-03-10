from typing import Dict
import json
import os

ENV_VAR_PREFIX = "DEPLOY_VAR_"


def with_env_var(variable_name: str, input_dict: Dict = None) -> Dict:
    new_var = {variable_name.replace(ENV_VAR_PREFIX, ""): os.environ[variable_name]}

    if input_dict:
        return {**input_dict, **new_var}

    return new_var


def with_var(new_variable: str, input_dict: Dict = None) -> Dict:
    k, v = new_variable.split('=', 2)
    new_var = {k: v}

    if input_dict:
        return {**input_dict, **new_var}

    return new_var


def with_var_file(input_file: str, input_dict: Dict = None) -> Dict:
    with open(input_file) as f:
        new_vars = json.load(f)

    if input_dict:
        return {**input_dict, **new_vars}

    return new_vars
