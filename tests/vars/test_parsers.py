import pytest
import os
import deploy_pipeline.vars.parsers as parsers
from tests.conftest import config_dir


@pytest.mark.parametrize("source,inputs,fn_to_call,expected", [
    (
        'foo=bar', None, parsers.with_var, {'foo': 'bar'},
    ),
    (
        'foo=bar', {'bar': 'baz'}, parsers.with_var, {'foo': 'bar', 'bar': 'baz'},
    ),
    (
        'foo={"bar": "baz"}', None, parsers.with_var, {'foo': {'bar': 'baz'}}
    ),
    (
        'foo={"bar": "baz"}', {'alpha': {'beta': 'delta'}}, parsers.with_var, {'foo': {'bar': 'baz'}, 'alpha': {'beta': 'delta'}}
    )
])
def test_valid_variables(source, inputs, fn_to_call, expected):
    assert fn_to_call(source, inputs) == expected


@pytest.mark.parametrize("source,inputs,expected", [
    (
        "variable_test.json",
        None,
        {
            "partition": {"actions": ["stop", "install", "start"], "types": ["binary", "index", "config"]}
        }
    ),
    (
        "variable_test.json",
        {"collator": {"actions": ["stop", "install", "start"], "types": ["binary"]}},
        {
            "partition": {"actions": ["stop", "install", "start"], "types": ["binary", "index", "config"]},
            "collator": {"actions": ["stop", "install", "start"], "types": ["binary"]}
        }
    )
])
def test_valid_files(source, inputs, expected):
    assert parsers.with_var_file(os.path.join(config_dir(), source), inputs) == expected
