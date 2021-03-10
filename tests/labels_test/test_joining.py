import pytest
from deploy_pipeline.labels.joining import LabelJoin


@pytest.mark.parametrize("left,left_join_key,right,right_join_key,expected", [
    (
            {"key_1": {}}, None,
            {"key_2": {"joiner": ["key_1"]}}, "joiner",
            {"key_1": {"key_2"}}
    ),
    (
            {"key_2": {"joiner": ["key_1"]}}, "joiner",
            {"key_1": {}}, None,
            {"key_2": {"key_1"}}
    ),
    (
            {"key_1": {"joiner": ["key_3"]}}, "joiner",
            {"key_2": {"joiner": ["key_3"]}}, "joiner",
            {"key_1": {"key_2"}}
    ),
    (
            {"key_2": {"joiner": ["key_3"]}}, "joiner",
            {"key_1": {"joiner": ["key_3"]}}, "joiner",
            {"key_2": {"key_1"}}
    ),
])
def test_joining(left, left_join_key, right, right_join_key, expected):
    joiner = LabelJoin(left, left_join_key).match(right, right_join_key)
    assert joiner == expected
