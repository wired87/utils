from bm.settings import TEST_USER_ID
from itertools import chain, combinations

from physics import STANDARD_MODELC, CORE_LAWS_C, POSC, GRAVITYC
from physics.putils.calculator import Calculator


def powerset_of_keysets(dict1, dict2):
    all_keys = list(dict1.keys()) + list(dict2.keys())
    return list(chain.from_iterable(combinations(all_keys, r) for r in range(len(all_keys) + 1)))


class QFHandler:

    """
    This creates a graph of a lot of charged particles
    and let them interact following the core laws of physics

    How these particles are ordered and interact,
    this is the memory
    Like 8k forming a ring shape and create a field.

    """

    def __init__(self, g, user_id=TEST_USER_ID):
        # Core physics content
        self.user_id = user_id
        # Utility classes
        self.calculator = Calculator(
            g,
            calculations=list(
                # QF Equations
                STANDARD_MODELC +

                # Particle Equations
                CORE_LAWS_C +
                POSC +
                GRAVITYC

            )
        )
        self.g = g

    async def update(self, nid, args):
        # Run all equations against
        # todo added nodes while loop jsut added after finish -> check after each iter for changes -> continue loop with switched G
        stuff = [(nnid, attrs) for nnid, attrs in self.g.G.nodes(data=True)]
        # todo later available params define the entry for the eq graph
        len_stuff = len(stuff)

        index = 0
        while index < len_stuff:
            updated_len_stuff = len(stuff)
            if len_stuff < updated_len_stuff:
                index -= (updated_len_stuff - len_stuff)
            nnid, nargs = stuff[index]
            if nid != nnid:

                env_id, env_attrs = self.g.get_single_neighbor_nx(
                    nnid, # -> id doesnt matter -> same env everywhere
                    "ENV",
                )

                print("env_id", env_id)

                edge_attrs = self.g.G.edges[nid, nnid]
                print("edge_attrs", edge_attrs)

                # run equations
                args = self.calculator.main(
                    parent=args,
                    child=nargs,
                    edge_attrs=edge_attrs,
                    env_attrs=env_attrs
                )

                self.g.G.nodes[nid].update(args)
            index += 1





