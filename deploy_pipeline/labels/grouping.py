from collections import defaultdict
from typing import Dict, Set


class LabelGroup:
    _source: Dict
    _sub_key: str

    # it isn't lost on me that all of this stuff falls on its face if we need to nest further than one element into the
    # dict (i.e. { "foo": { "bar": { "baz": { "tag_key": "tag_value", "tag_key_1": "tag_value_1" } } } }, where the
    # nested foo["bar"]["baz"] is the source for the labels.  might need to be changed, even providing the option to
    # query based on sub-key is over-engineering (if it can even be called that), cause everything is under "labels"
    # currently.
    def __init__(self, source: Dict, sub_key: str = None):
        self._source = source
        self._sub_key = sub_key

    def group(self, group_label: str) -> Dict[str, Set]:
        # for future me, I chose this route due to code clarity.  if the data were laid out differently we could use
        # something like utilize itertools.groupby, but as it stands we are currently getting data fed in via a dict,
        # and we're grouping by a sub-key, so it seemed more straight forward to do this.
        #
        # originally i was going to do some fun list comprehensions mixed with sorting of tuples (required by groupby)
        # and then feed that into itertools.groupby to get the grouped result, but that just seemed convoluted and since
        # the performance isn't a concern right now, I won't pre-maturely optimize
        result = defaultdict(set)
        for source_k, source_v in self._source.items():
            group_k = source_v[self._sub_key][group_label] if self._sub_key else source_v[group_label]
            result[group_k].add(source_k)

        return result
