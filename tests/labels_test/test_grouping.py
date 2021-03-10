import pytest
from deploy_pipeline.labels.grouping import LabelGroup


@pytest.mark.parametrize("source,sub_key,group_label,expected", [
    (
            {
                "key_1": {"labels": {"group_label": 1}},
                "key_2": {"labels": {"group_label": 1}},
            },
            "labels", "group_label",
            {
                1: {"key_1", "key_2"}
            }
    ),
    (
            {
                "key_1": {"labels": {"group_label": 1}},
                "key_2": {"labels": {"group_label": 1}},
                "key_3": {"labels": {"group_label": 2}},
                "key_4": {"labels": {"group_label": 2}},
            },
            "labels", "group_label",
            {
                1: {"key_1", "key_2"},
                2: {"key_3", "key_4"}
            }
    ),
    (
            {
                "key_5": {"group_label": 1},
                "key_6": {"group_label": 1},
                "key_7": {"group_label": 2},
                "key_8": {"group_label": 2},
                "key_9": {"group_label": 3},
            },
            None, "group_label",
            {
                1: {"key_5", "key_6"},
                2: {"key_7", "key_8"},
                3: {"key_9"}
            }
    )
])
def test_grouping(source, sub_key, group_label, expected):
    assert LabelGroup(source, sub_key).group(group_label) == expected
