from enum import Enum
from collections import defaultdict
from typing import Dict, Any, NamedTuple, Tuple, Iterable, Set, Union


class Operator(Enum):
    In = 1
    NotIn = 2
    Exists = 3
    DoesNotExist = 4


LabelQuery = NamedTuple('LabelQuery', (
    ('key', str),
    ('operator', Operator),
    ('values', Iterable)
))


class LabelMatch:
    _source: Dict[str, Any]
    _sub_key: str
    _queries: Set[LabelQuery]

    _index_complete: bool
    _label_index: Union[Dict[Tuple, Set], None]

    def __init__(self, source: Dict[str, Any], sub_key: str = None):
        self._source = source
        self._sub_key = sub_key

        self._queries = set()

        # build an inverted index of (<label>) and (<label>, <value>)
        # to facilitate key-based lookups
        self._label_index = None

    def add_query(self, query: LabelQuery) -> "LabelMatch":
        self._queries.add(query)
        return self

    def add_queries(self, queries: Iterable[LabelQuery]) -> "LabelMatch":
        for query in queries:
            self._queries.add(query)

        return self

    def _get_index(self) -> Dict[Tuple, Set]:
        # the label index will only be None if it isn't built yet
        if self._label_index is not None:
            return self._label_index

        # nuke the existing index if it's there (shouldn't be)
        self._label_index = defaultdict(set)

        # note the reverse index here isn't super kind to memory, in fact it's pretty verbose.  the trade-off here
        # is that it should be kinder in the long run to CPU.  the reverse index allows dictionary matches which are
        # implemented in C (ok, duck typing could make that not the case, i.e. someone passes in a Dict-like object
        # that sub-classes UserDict where the C optimizations aren't present, but i have to draw the line somewhere)
        # re-thought if memory becomes an issue (right now it isn't), but it this makes the subsequent query code
        # *WAY* more simple
        for k, v in self._source.items():
            # allows the user to specify a sub key, or just use the dict by itself
            l_source = v.get(self._sub_key, {}) if self._sub_key else v
            for l_k, l_value in l_source.items():
                # facilitate exists and doesnotexist lookups
                self._label_index[(l_k,)].add(k)
                # facilitate in and not in lookups
                self._label_index[(l_k, l_value)].add(k)

        return self._label_index

    def do(self) -> Set:
        # fetch the index
        label_index = self._get_index()

        # in python3 keys returns a memory view which is a set like object and is perfect for us since we for
        # simplicity we assume the result set starts at *everything* and is narrowed down via the queries
        # the first iteration of the query loop will return a new set of filtered results, thus not needing to
        # write back to the original (which isn't supported by a memory view).
        index_keys = label_index.keys()
        matched_keys = self._source.keys()
        for query in self._queries:
            found = set()

            # this could use come clean-up
            if query.operator == Operator.In:
                for search_key in set((query.key, f) for f in query.values):
                    if search_key in index_keys:
                        found.update(label_index[search_key])

                matched_keys = matched_keys & found

            if query.operator == Operator.NotIn:
                for search_key in set((query.key, f) for f in query.values):
                    if search_key in index_keys:
                        found.update(label_index[search_key])

                matched_keys = matched_keys - found

            if query.operator == Operator.Exists:
                if (query.key,) in index_keys:
                    found.update(label_index[(query.key,)])

                matched_keys = matched_keys & found

            if query.operator == Operator.DoesNotExist:
                if (query.key,) in index_keys:
                    found.update(label_index[(query.key,)])

                matched_keys = matched_keys - found

            if not found:
                break

        # return the matched keys
        return matched_keys


def new_query(key: str, operator: Operator, values: Iterable = None) -> LabelQuery:
    return LabelQuery(
        key=key,
        operator=operator,
        values=tuple(sorted(set(values))) if values else tuple()
    )


def query_from_object(obj_query: Dict) -> LabelQuery:
    return new_query(
        obj_query['key'],
        getattr(Operator, obj_query['operator']),
        obj_query.get('values', tuple())
    )


def query_from_string(str_query: str) -> LabelQuery:
    # not equal
    if '!=' in str_query:
        key, value = str_query.split('!=', 2)
        return new_query(key, Operator.NotIn, [value])

    # equal
    if '=' in str_query:
        key, value = str_query.split('=', 2)
        return new_query(key, Operator.In, [value])

    # in
    if ' in (' in str_query:
        key, values = str_query.rstrip(')').split(' in (', 2)
        return new_query(key.strip(), Operator.In, [v.strip() for v in values.split(',')])

    # not in
    if ' notin (' in str_query:
        key, values = str_query.rstrip(')').split(' notin (', 2)
        return new_query(key, Operator.NotIn, [v.strip() for v in values.split(',')])

    # not exists
    if str_query.startswith('!'):
        return new_query(str_query[1:], Operator.DoesNotExist)

    # exists
    return new_query(str_query, Operator.Exists)
