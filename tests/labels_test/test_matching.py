import pytest
from deploy_pipeline.labels.matching import LabelMatch, new_query, Operator, query_from_object, query_from_string, LabelQuery


@pytest.mark.parametrize("key,operator,value,expected", [
    ('pogo.deploy.stage', Operator.In, (0,), {'ora-del-sup-001', 'orb-del-sup-001', 'se3-del-sup-001'}),
    ('pogo.deploy.stage', Operator.In, (2,), set()),
    ('pogo.deploy.environment', Operator.NotIn, ('prod-aws',), {'se3-del-sup-001', 'se3-del-sup-007'}),
    ('pogo.deploy.environment', Operator.NotIn, ('prod-aws', 'prod-se3'), set()),
    ('pogo.test.data', Operator.Exists, ('',), {'ora-del-sup-001', 'orb-del-sup-001', 'ora-del-sup-007'}),
    ('pogo.test.data2', Operator.Exists, ('',), set()),
    ('pogo.test.data', Operator.DoesNotExist, ('',), {'orc-del-sup-001', 'se3-del-sup-001', 'se3-del-sup-007'}),
    ('pogo.deploy.stage', Operator.DoesNotExist, ('',), set())
])
def test_query_result(host_data, key, operator, value, expected):
    in_result = LabelMatch(host_data, 'labels').add_query(new_query(key, operator, value)).do()
    assert in_result == expected


@pytest.mark.parametrize("object_query,expected", [
    (
            {"key": "key_1", "operator": "In", "values": ["value_1"]},
            LabelQuery(key="key_1", operator=Operator.In, values=("value_1",))
    ),
    (
            {"key": "key_1", "operator": "In", "values": ["value_1", "value_1_1"]},
            LabelQuery(key="key_1", operator=Operator.In, values=("value_1", "value_1_1"))
    ),
    (
            {"key": "key_2", "operator": "NotIn", "values": ["value_2"]},
            LabelQuery(key="key_2", operator=Operator.NotIn, values=("value_2",))
    ),
    (
            {"key": "key_2", "operator": "NotIn", "values": ["value_2", "value_2_1", "value_2_2"]},
            LabelQuery(key="key_2", operator=Operator.NotIn, values=("value_2", "value_2_1", "value_2_2"))
    ),
    (
            {"key": "key_3", "operator": "Exists"},
            LabelQuery(key="key_3", operator=Operator.Exists, values=tuple())
    ),
    (
            {"key": "key_4", "operator": "DoesNotExist"},
            LabelQuery(key="key_4", operator=Operator.DoesNotExist, values=tuple())
    ),
])
def test_query_from_object(object_query, expected):
    assert query_from_object(object_query) == expected


@pytest.mark.parametrize("string_query,expected", [
    (
            "key_2=value_1",
            LabelQuery(key="key_2", operator=Operator.In, values=("value_1",))
    ),
    (
            "key_2!=value_1",
            LabelQuery(key="key_2", operator=Operator.NotIn, values=("value_1",))
    ),
    (
            "key_2 in (value_1)",
            LabelQuery(key="key_2", operator=Operator.In, values=("value_1",))
    ),
    (
            "key_2 in (value_1, value_2)",
            LabelQuery(key="key_2", operator=Operator.In, values=("value_1", "value_2"))
    ),
    (
            "key_2 notin (value_1)",
            LabelQuery(key="key_2", operator=Operator.NotIn, values=("value_1",))
    ),
    (
            "key_2 notin (value_1, value_2)",
            LabelQuery(key="key_2", operator=Operator.NotIn, values=("value_1", "value_2"))
    ),
    (
            "key_2",
            LabelQuery(key="key_2", operator=Operator.Exists, values=tuple())
    ),
    (
            "!key_2",
            LabelQuery(key="key_2", operator=Operator.DoesNotExist, values=tuple())
    ),
])
def test_query_from_string(string_query, expected):
    assert query_from_string(string_query) == expected
