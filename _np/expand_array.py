"""

smpel scale up a 3d list [1,[2,3],4] to [[1,2,4], [1,3,4]
programatically and modlar with np -> convert to list valid for any emelemt datatypes e.g. [(1,2), [(3,4),(5,6)],(7,7)]

"""
from itertools import product

def expand_structure(struct):
    def as_choices(x):
        # REMOVED tuple from the check
        # Only a list represents a "menu" of options
        return x if isinstance(x, list) else [x]

    choices = [as_choices(e) for e in struct]
    return list(map(list, product(*choices)))


