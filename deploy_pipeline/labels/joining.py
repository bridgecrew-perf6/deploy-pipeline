from typing import Dict, Union, Iterable
from collections import defaultdict


class LabelJoin:
    # i should note that the type hint for "right" of Dict OR Iterable will fall on its face if join_key is provided
    # and the variable passed in doesn't implement __get__.  It'll thrown an exception so you'll know right away if you
    # have a problem
    def __init__(self, left: Union[Dict, Iterable], join_key: str = None):
        self._left = left
        self._left_key = join_key

    # see type hint warning above
    def match(self, right: Union[Dict, Iterable], join_key: str = None):
        # holds the matched map of {left_key_1: {matched_right_key_1, matched_right_key_n}}
        result = defaultdict(set)

        # iterate over the left dict, as keys and values
        for left_k in self._left:
            # if a left key is supplied, use it as the join key, if not just use the left dicts subkey(s) for joining
            left_join_keys = set(self._left[left_k][self._left_key]) if self._left_key else {left_k}
            # iterate over the right dict, again as keys and values
            # we're doing all this nonsense to support lookups of nested keys (one level currently, since that is all
            # that is needed)
            for right_k in right:
                # extract the join key
                right_join_keys = set(right[right_k][join_key]) if join_key else {right_k}
                # determine if there is any overlap between the keys, if there is we should count this as a match,
                # implementation detail here, we could iterate over left or right join keys and do an if/match/break
                # this is at least done in C: https://github.com/python/cpython/blob/master/Objects/setobject.c#L1166
                if len(right_join_keys & left_join_keys) > 0:
                    result[left_k].add(right_k)

        return result
