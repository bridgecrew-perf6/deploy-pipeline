import pytest
from deploy_pipeline.labels.utils import with_data


@pytest.mark.parametrize("keys,data,expected", [
    (
            set(),
            {
                "key_1": {"name": "Key 1"},
                "key_2": {"name": "Key 2"},
                "key_3": {"name": "Key 3"}
            },
            {}
    ),
    (
            {"key_1"},
            {
                "key_1": {"name": "Key 1"},
                "key_2": {"name": "Key 2"},
                "key_3": {"name": "Key 3"}
            },
            {
                "key_1": {"name": "Key 1"}
            }
    ),
    (
            {"key_1", "key_2"},
            {
                "key_1": {"name": "Key 1"},
                "key_2": {"name": "Key 2"},
                "key_3": {"name": "Key 3"}
            },
            {
                "key_1": {"name": "Key 1"},
                "key_2": {"name": "Key 2"}
            }
    ),
])
def test_with_data(keys, data, expected):
    assert with_data(keys, data) == expected
