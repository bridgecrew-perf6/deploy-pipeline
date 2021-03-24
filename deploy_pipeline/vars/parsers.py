from typing import Dict, Union
import json
import os

ENV_VAR_PREFIX = "DEPLOY_VAR_"


def with_var(new_variable: str, inputs: Dict = None) -> Dict:
    # try to load json first
    if _is_json(new_variable):
        return _merge_inputs(json.loads(new_variable), inputs)

    # load plain old key/value pairs
    k, v = new_variable.split('=', 2)
    return _merge_inputs(with_key_value(k, v), inputs)


def with_env_var(variable_name: str, inputs: Dict = None) -> Dict:
    # decode json
    if _is_json(os.environ[variable_name]):
        return _merge_inputs(json.loads(os.environ[variable_name]), inputs)

    # remove ENV_VAR_PREFIX from the key name (since environment variables are global) and
    # merge them as a key/value pair
    return _merge_inputs(with_key_value(variable_name.replace(ENV_VAR_PREFIX, ""), os.environ[variable_name]), inputs)


def with_var_file(input_file: str, inputs: Dict = None) -> Dict:
    with open(input_file) as f:
        return _merge_inputs(json.load(f), inputs)


def with_key_value(k: str, v: str) -> Dict:
    return {k.strip(): v}


def _merge_inputs(new_values: Dict, inputs: Dict = None) -> Dict:
    return {**inputs, **new_values} if inputs else new_values


def _is_json(input_value: str) -> bool:
    return input_value.startswith('{')
