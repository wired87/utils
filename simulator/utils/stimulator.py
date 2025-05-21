import numpy as np

from _google.graph.g_utils import GGraphUtils
from utils.logger import LOGGER


class SimLogger:

    """
    Schritte nachvollziehen,
    Daten speichern (delta storage) -> G -> gleich GNN format

    Each ENV = Node
    Each session (after a reset) = Node -> If user breaks sim and continues it later it will be added to the existing node
    Edge: ENV -> Each session


    """

    def __init__(self, loader_g):
        self.logger = LOGGER
        self.g = loader_g
        self.data_graph = GGraphUtils(

        )

    def log(self, **kwargs):
        self.logger.log(**kwargs)




class Stimulator:



    def __init__(self, g:GGraphUtils):
        self.g = g
        self.layer="STIMULATOR"
        self.possible_stm_types= {
            "field_amplitudes":["psi",
            "phi", "H", "A_mu", "W_mu", "W_mu_plus", "W_mu_minus", "Z_mu",
            "u", "d", "nu_L", "e", "X", "bsm_scalar_field_X"],

            "coupling_constants":[
              "g", "lambda_H", "lambda", "yukawa", "g_XH", "g_s", "bsm_fermion_sm_fermion_coupling",
              "bsm_fermion_higgs_yukawa"
            ],

            "mass":[
              "g", "lambda_H", "lambda", "yukawa", "g_XH", "g_s", "bsm_fermion_sm_fermion_coupling",
              "bsm_fermion_higgs_yukawa"
            ],

            "initial_gradient": [
              "dmu_psi", "dmu_phi", "dmu_W", "dmu_X", "dmu_nu", "d_mu", "D_mu"
            ],

            "vacuum_expectation": [
                "v_higgs", "v_squared", "phi"
            ]
        }
        self.single_stim_cfg={
            "category": [k for k in self.possible_stm_types.keys()][0], # one of them
            "value_change_type": "increase", # or decrease
            "change_keys": [], # any keys:trgt_value form self.possible_stm_types
            "change": .1, # add additional increase or decrease
            "duration": 0.1, # s
            "pos": [0.0,0.0,0.0,],
            "radius": 5,
            "node_ids": [], # -> todo remove later when nodes move/change
            "color": (255,0,0,.2),
            "time_step_progress": 0.0, # current time # the step width is set in env_cfg
            "multiplier_per_step": 1.1
            # todo uniform stimuli für partikel als auch qfns
        }

        self.stim_queue=[]



    def select_nodes_in_area(self, center, radius=1):
        """
        As part of the sim area picker, get all nodes within a specific radius based on conter (start pos)
        :returns: List of node ids
        """
        return [n for n, attrs in self.g.G.nodes(data=True) if np.linalg.norm(np.array(n.pos[:2]) - np.array(center)) <= radius]


    def validate_stim_color(self, key):
        # run against possible_stm_types parent keys and choose color
        return (255,0,0,.2)


    def add_stimuli(self, stim_cfg):
        cat = stim_cfg["category"]
        pos = stim_cfg["pos"]
        radius = stim_cfg["radius"]
        duration = stim_cfg["duration"]

        # Set id
        stim_node_id = f"{cat}_{pos}_{radius}_{duration}"

        # Get overlapping neighbors
        nodes = self.select_nodes_in_area(center=pos, radius=radius)

        stim_cfg["color"] = self.validate_stim_color(key=stim_node_id)

        self.g.add_node(
            attrs=dict(
                id=stim_node_id,
                type=self.layer,
                **stim_cfg
            )
        )

        # connect stim to nodes
        for node_id in nodes:
            self.g.add_edge(
                stim_node_id,
                node_id,
                attrs=dict(
                    rel="stimulates",
                    src_layer=self.layer,
                    trgt_layer="QFN",
                )
            )




    def update_stim(self, node_ids:list, env_attrs):
        def apply_stimuli(node_attrs, change_keys, sim_cfg):
            for change_key in change_keys:
                for k, v in self.possible_stm_types.items():
                    if change_key in v:
                        self.sl.log(f"Stim {change_key}")
                        if not isinstance(node_attrs[change_key], (int, float)):
                            try:
                                node_attrs[change_key] = float(node_attrs[change_key])
                            except Exception as e:
                                print(f"Could not convert {change_key} to numeric:", e)
                                continue
                        if sim_cfg["type"] == "increase":
                            node_attrs[change_key] += sim_cfg["change"]
                        else:
                            node_attrs[change_key] -= sim_cfg["change"]
            return node_attrs

        all_stims = [(n, attrs) for n, attrs in self.g.G.nodes(data=True) if attrs.get("type") == self.layer]

        for node_id, stim_cfg in all_stims:
            neighbors = self.g.get_neighbor_list(node_id, target_type="QFN")
            for n in neighbors:
                neighbor_id = n[0]
                neighbor_attrs = n[1]
                change_keys = stim_cfg["change_keys"]

                # Update ndoe attrs
                neighbor_attrs = apply_stimuli(neighbor_attrs, change_keys, stim_cfg)

                # Save changes
                self.g.G.nodes[neighbor_id].update(neighbor_attrs)

                # Update sim_cfg -> todo move in TimeStepUpdator
                stim_cfg["time_step_progress"] += env_attrs["time_step"]
                if stim_cfg["time_step_progress"] < stim_cfg["duration"]:
                    self.g.G.nodes[node_id].update({
                        stim_cfg
                    })
                else:
                    self.g.remove_node(node_id, "QFN")






class TimeStepUpdator:


    def __init__(self):
        pass


