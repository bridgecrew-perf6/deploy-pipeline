from typing import Dict, Set


# might want to investigate how to do this as a generator, that way we don't take the memory penalty when all we want
# is access to the labels
def with_data(matched_keys: Set, source_data: Dict) -> Dict:
    return {matched_key: source_data[matched_key] for matched_key in matched_keys}
