import json
import os
import time
from tempfile import TemporaryDirectory

from typing import List

import networkx as nx

from qf_core_base.qf_utils.all_subs import ALL_SUBS, ALL_SUBS_LOWER
import queue

from utils._np.serialize_complex import check_serialize_dict
from utils.graph.visual import create_g_visual
from utils.logger import LOGGER
from utils.manipulator import Manipulator
from utils.queue_handler import QueueHandler
from utils.utils import Utils

class GUtils(Utils):
    """
    Handles State G local and 
    History G through DataManager
    
    ALERT:
    DB Pushs need to be ahndled externally (DBManager -> _google) 
    """

    def __init__(
            self,
            user_id,
            G=None,
            g_from_path=None,
            nx_only=False,
            # queue: queue.Queue or None = None,
            enable_data_store=True,
            history_types=None,
            file_store=None
    ):
        super().__init__()
        self.G = None
        self.enable_data_store = enable_data_store
        self.g_from_path = g_from_path
        self.get_nx_graph(G)
        self.nx_only = nx_only
        self.history = {}
        self.user_id=user_id

        self.manipulator = Manipulator()
        self.q_handler = QueueHandler(queue)

        if self.enable_data_store is True:
            self.datastore = nx.Graph()
            self.history_types = history_types  # list of nodetypes captured by dataqstore  ALL_SUBS + ["ENV"]
        self.file_store=file_store or TemporaryDirectory()

        self.metadata_fields = [
            "graph_item",
            "index",
            "entry_index",
            "time",
        ]
        # Sim timestep must be updated externally for each loop
        self.timestep = None
        self.key_map = set()
        self.id_map = set()
        self.schemas = {}
        """table_name: {
        "schema": {},
        "rows": [],
        "id_map": set(),
        },"""

        #print("GUtils initialized")

    ####################################
    # CORE                             #
    ####################################

    def add_node(self, attrs: dict, timestep=None, flatten=False):
        attrs = self.manipulator.clean_attr_keys(attrs, flatten)
        if attrs.get("type") is None:
            print("NEW NODE ATTRS")
            # pprint.pp(attrs)

        attrs["type"] = attrs["type"].upper()
        nid = attrs["id"]
        # #print(">>NODE FILTERED")
        # #print(f"Add {attrs['id']} -> layer: {attrs['type']}")
        """if single_upsert is True:
            await self.g.upsert_row(
                table=f"{edge_attrs['src_layer'].upper()}_{edge_attrs['rel']}_{edge_attrs['trgt_layer'].upper()}",
                batch_chunk=[edge_attrs])"""

        if self.nx_only is False:
            self.local_batch_loader(attrs)
        self.G.add_node(nid, **{k: v for k, v in attrs.items() if k != "id"})

        # Add history entry
        self.h_entry(nid, {k: v for k, v in attrs.items() if k != "id"})

        # Extedn keys
        self._extend_key_map(attrs)
        self._extend_id_map(nid)
        return True

    def h_entry(self, nid, attrs, timestep=None, graph_item="node"):
        ntype = attrs.get("type", "")
        if ntype is None:
            ntype = graph_item  # -> SET EDGE

        #print(f"Add {graph_item} h_entry", nid)
        if self.enable_data_store is True:
            if timestep is None:
                timestep = attrs.get("time", 0)

            history_id = f"{nid}_{int(time.time())}_{timestep}"

            len_type_entries = len(
                [
                    (inid, iattrs)
                    for inid, iattrs in self.datastore.nodes(data=True) if
                    iattrs.get("type", "0").upper() == attrs.get("type", "1").upper()
                ]
            )

            attrs = dict(
                type=nid,
                entry_index=len_type_entries,
                graph_item=graph_item,
                base_type=ntype,
                **{k: v for k, v in attrs.items() if k not in ["id", "type"]}
            )

            #print("Add H Entry:")
            #pprint.pp(attrs)

            # Extedn keys
            self._extend_key_map(attrs)
            self._extend_id_map(nid)

            self.datastore.add_node(
                history_id,
                **attrs
            )
            #print("H entry node added", self.datastore.nodes[history_id])
        else:
            raise ValueError("Invalid data!!!!", nid, attrs)
    def add_edge(self, src=None, trt=None, attrs: dict or None = None, flatten=False, timestep=None, index=None):
        # pprint.pp(attrs)
        #print(f"Add edge {src}->{attrs.get('rel')}->{trt}")
        # todo externa nd intern couplings no edge id after creation

        # Color
        color = None

        # Check
        """if attrs.get("id") is None:
            #print(">>>EDGE ATTRS NONE:", attrs)
        """
        if index is None:
            index = attrs.get("index", None)
        if index is not None:
            color = f"rgb({index + .5}, {index + .5}, {index + .5})"
        # #print("color set:", color)

        try:
            src_layer = self.manipulator.replace_special_chars(attrs.get("src_layer")).upper()
            trgt_layer = self.manipulator.replace_special_chars(attrs.get("trgt_layer")).upper()

            # #print("src_layer", src_layer)
            # #print("trgt_layer", trgt_layer)
            if src is None:
                src = attrs.get("src")
            if trt is None:
                trt = attrs.get("trt")

            if src and trt and src_layer and trgt_layer:
                if isinstance(src, int):
                    src = str(src)
                if isinstance(trt, int):
                    trt = str(trt)
                # #print("int conv...")

                attrs = self.manipulator.clean_attr_keys(attrs, flatten)
                # #print("attrs_new", attrs )
                rel = attrs["rel"].lower().replace(" ", "_")

                edge_id = f"{src}_{rel}_{trt}"

                attrs = {
                    **attrs,
                    "src": src,
                    "trgt": trt,
                    "id": edge_id,
                    "color": color,
                }

                # Add keys
                self._extend_key_map(attrs)
                self._extend_id_map(attrs["id"])

                # #print(f"ids {src} -> {trt}; Layer {src_layer} -> {trgt_layer}")
                edge_table_name = f"{src_layer}_{rel}_{trgt_layer}"
                attrs["type"] = edge_table_name

                src_node_attr = {"id": src, "type": src_layer}
                trgt_node_attr = {"id": trt, "type": trgt_layer}
                # #print(f"Add {src} -> trgt: {trt}")

                if self.nx_only is False:
                    # todo run in executor
                    # #print("Upsert Local Batch Loader")
                    self.local_batch_loader(src_node_attr)
                    self.local_batch_loader(trgt_node_attr)
                    self.local_batch_loader(attrs)

                # #print("Upsert to NX")
                self.G.add_edge(src, trt, **{k: v for k, v in attrs.items()})
                self.G.add_node(src, **src_node_attr)
                self.G.add_node(trt, **trgt_node_attr)

                # Add history entry
                self.h_entry(
                    nid=attrs["id"],
                    attrs={k: v for k, v in attrs.items() if k != "id"},
                    graph_item="edge"
                )
                #print(f"Edge added ")
                #print(self.G.get_edge_data(src, trt))
            else:
                raise ValueError(f"Wrong edge fromat")

        except Exception as e:
            raise ValueError(f"Skipping link src: {src} -> trgt: {trt} cause:", e, attrs)

    def _extend_key_map(self, attrs):
        for k in list(attrs.keys()):
            if k not in self.key_map:
                self.key_map.add(k)


    def _extend_id_map(self, nid):
        if nid not in self.id_map:
            self.id_map.add(nid)

    def get_edges(self, datastroe=True):
        if datastroe is False:
            return [{"src": src, "trgt": trgt, "attrs": attrs} for src, trgt, attrs in self.G.edges(data=True)]
        else:
            return [{"attrs": attrs} for eid, attrs in self.datastore.edges(data=True) if
                    attrs.get("graph_item").lower() == "edge"]

    def update_node(self, attrs):
        nid = attrs.get("id")
        node_attrs = self.G.nodes[nid]
        if node_attrs is None:
            print("Node couldnt be updated...")
            return

        attrs = check_serialize_dict(attrs, [k for k in attrs.keys()])

        # Add keys
        self._extend_key_map(attrs)

        self.G.nodes[nid].update(attrs)

        if self.enable_data_store is True:
            # Add history entry
            self.h_entry(
                attrs["id"],
                {k: v for k, v in attrs.items() if k != "id"},
                graph_item="node"
            )

    def update_edge(self, src, trgt, attrs, rels: str or list = None, ):
        # rel = attrs.get("rel", "").lower().replace(" ", "_")
        """
        src_layer = attrs.get("src_layer").upper()
        trgt_layer = attrs.get("trgt_layer").upper()
        table_name = f"{src_layer}_{rel}_{trgt_layer}
        """
        

        # serialize attrs
        attrs = check_serialize_dict(attrs, [k for k in attrs.keys()])

        # Add keys
        self._extend_key_map(attrs)

        # Update nx
        if "MultiGraph" in str(type(self.G)):
            for key, edge in self.G.get_edge_data(src, trgt).items():
                erel = edge.get("rel")
                if erel in rels:
                    if self.enable_data_store is True:
                        edge_id = f"{src}_{erel}_{trgt}"
                        self.h_entry(
                            edge_id,
                            {k: v for k, v in attrs.items() if k != "id"},
                            graph_item="edge"
                        )
                    self.G.edges[src, trgt, key].update(attrs)
        else:
            if self.enable_data_store is True:
                edge_id = self.G.edges[src, trgt]["id"]
                self.h_entry(
                    edge_id,
                    {k: v for k, v in attrs.items() if k != "id"},
                    graph_item="edge"
                )
            self.G.edges[src, trgt].update(attrs)

        # todo handle async rt spanner || fbrtdb

    ####################################
    # HELPER
    ####################################

    def get_nx_graph(self, G):
        if self.g_from_path is not None:
            if os.path.exists(self.g_from_path):
                self.load_graph()
        if G is not None:
            self.G = G
        elif self.G is None:
            self.G = nx.Graph()  # normaler G da gluon -> gluon sonst explodieren würde
        #print("Local Graph loaded")

    def save_graph(self, dest_file, ds=False):
        print("Save Gs")
        if ds is True:
            G=self.datastore
        else:
            G=self.G
        self._link_safe(
            G,
            dest_file
        )
        print(f"G data written to :{dest_file}")


    def _link_safe(self, G, dest_name):
        self.check_serilize(G)
        data = nx.node_link_data(G)

        with open(f"{dest_name}", "w") as f:
            json.dump(data, f)

    def check_serilize(self, G):
        # srialize
        for nid, attrs in G.nodes(data=True):
            G.nodes[nid].update(
                check_serialize_dict(
                    attrs,
                    [k for k in attrs.keys()],
                )
            )
        for src, trgt, attrs in G.edges(data=True):
            G.edges[src, trgt].update(
                check_serialize_dict(
                    attrs,
                    [k for k in attrs.keys()],
                )
            )
        return G


    def load_graph(self, local_g_path=None):
        if local_g_path is None:
            local_g_path = self.g_from_path
        """Loads the networkx graph from a JSON file."""
        LOGGER.info(f"📂 Loading graph from {local_g_path}...")
        with open(local_g_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)  # Use json.load() for files, not json.loads()
        self.G = nx.node_link_graph(graph_data)
        LOGGER.info(f"✅ Graph loaded! {len(self.G.nodes)} nodes, {len(self.G.edges)} edges.")

    def print_status_G(self):
        print("STATUS:", self.G)
        everything = {}
        for k, v in self.G.nodes(data=True):
            ntype = v.get("type")
            if ntype not in everything:
                everything[ntype] = 0
            everything[ntype] += 1

        for k, v in everything.items():
            print(f"{k}:{v}")

    def local_batch_loader(self, args):
        table_name = args.get("type")
        row_id = args["id"]
        if table_name:
            if table_name not in self.schemas:
                self.schemas[table_name] = {
                    "schema": {},
                    "rows": [],
                    "id_map": set(),
                }
                #print(f"Added {table_name} to schema")

            if row_id not in [item for item in self.schemas[table_name]["id_map"]]:
                # #print(f"Insert {row_id} into {table_name}")
                self.schemas[table_name]["rows"].append(args)
                self.schemas[table_name]["id_map"].add(row_id)
            # else:
            # #print(f"{row_id} already in schema")
        # #print("Added args")

    def get_single_neighbor_nx(self, node, target_type):
        # #print("Node", node)
        if isinstance(node, tuple):
            node = node[0]
        for neighbor in self.G.neighbors(node):
            if self.G.nodes[neighbor].get('type') == target_type:
                return neighbor, self.G.nodes[neighbor]
        return None, None  # No neighbor of that type found

    def get_neighbor_list(
            self,
            node,
            target_type: str or list or None = None,
            just_id=False,
            trgt_rel: str or list or None = None
    ) -> List[tuple] or None:
        ##print(f"# Get neighbors from {node}")
        neighbors = []

        # Filter Input
        if isinstance(target_type, str):
            target_type = [target_type]
        if isinstance(trgt_rel, str):
            trgt_rel = [trgt_rel]

        #print("trgt_rel:", trgt_rel)
        #print("target_type:", target_type)

        for neighbor in self.G.neighbors(node):
            # #print("get_neighbor_list neighbors:", neighbor)
            # Get neighbor from type
            nattrs = self.G.nodes[neighbor]
            if target_type is not None:
                # #print("get_neighbor_list nattrs", nattrs)
                if nattrs.get('type') in [t.upper() for t in target_type]:
                    if just_id is True:
                        neighbors.append(neighbor)
                    else:
                        neighbors.append((neighbor, nattrs.copy()))

            # Get neighbor from rel
            elif trgt_rel is not None:
                if isinstance(self.G, (nx.MultiGraph, nx.MultiDiGraph)):
                    for key, edge_attrs in self.G.get_edge_data(node, neighbor):
                        if edge_attrs.get("rel") in trgt_rel:
                            if just_id is True:
                                neighbors.append(neighbor)
                            else:
                                neighbors.append((neighbor, nattrs.copy()))
                            break
                else:
                    edge_attrs = self.G.get_edge_data(node, neighbor)
                    #print("edge_attrs:", edge_attrs)
                    if edge_attrs.get("rel").lower() in [rel.lower() for rel in trgt_rel]:
                        if just_id is True:
                            neighbors.append(neighbor)
                        else:
                            neighbors.append((neighbor, nattrs.copy()))

        # #print(f"Neighbors extracted: {neighbors}")
        return neighbors

    def remove_node(self, node_id, ntype):
        for row in self.schemas[ntype]["rows"]:
            if row["id"] == node_id:
                self.schemas[ntype]["rows"].remove(row)
                break
        self.G.remove_node(node_id)

    def cleanup_self_schema(self):
        # #print("Cleanup schema")
        for k, v in self.schemas.items():
            v["rows"] = []

    def build_G_from_data(
            self,
            initial_data,
            env_id=None
    ):
        # --- Graph aufbauen ---
        env = None
        data_keys = [k for k in initial_data.keys()]
        LOGGER.info(f"INITIAL DATA KEYS: {data_keys}")

        for node_type, node_id_data in initial_data.items():
            # Just get valid
            nupper = node_type.upper()
            valid_types = [*ALL_SUBS, "PIXEL", "ENV", "EDGES"]
            nupper_valid_t = nupper in valid_types

            LOGGER.info(f"{nupper} valid: {nupper_valid_t}")

            if nupper_valid_t:
                if isinstance(node_id_data, dict):  # Sicherstellen, dass es ein Dictionary ist
                    for nid, attrs in node_id_data.items():
                        # LOGGER.info(f">>>NID, {nid}")
                        if node_type.lower() == "edges":
                            parts = nid.split(f"_{attrs.get('rel')}_")
                            # LOGGER.info("parts", parts)
                            # check 2 ids in id and
                            if len(parts) >= 2:
                                self.add_edge(
                                    parts[0],
                                    parts[1],
                                    attrs=attrs
                                )
                            else:
                                print("something else!!!")

                        elif node_type == "ENV":
                            LOGGER.info("Env recognized")
                            env = attrs
                            env_id = nid  # Speichern Sie die env_id, falls benötigt
                            self.add_node(
                                attrs=attrs,
                            )
                        else:
                            self.add_node(
                                attrs=attrs,
                            )
                else:
                    LOGGER.info(f"DATA NOT A DICT:{node_type}:{node_id_data}")
                    # pprint.pp(node_id_data)
                # time.sleep(10)

            else:
                LOGGER.info(f"TYPE NOT VALID:{node_type}")

        LOGGER.info(f"Graph successfully build: {self.G}")
        return env, env_id, self.G

    def delete_node(self, delid):
        if delid and self.G.has_node(delid):
            #print(f"Del node {delid}")
            self.G.remove_node(delid)
        else:
            print(f"Couldnt delete since {delid} doesnt exists")
    
    
    def get_node_pos(self, G=None):
        if G==None:
            G = self.G
        serializable_node_copy = []
        valid_types = [*ALL_SUBS, "PIXEL"]
        for nid, attrs in G.nodes(data=True):
            ntype = attrs.get("type")
            if ntype in valid_types:
                # todo single subs
                serializable_node_copy.append(
                    {
                        "id": nid,
                        "pos": attrs.get("pos")
                    }
                )
        return serializable_node_copy


    def get_nodes(self, filter_key=None, filter_value:str or list=None):
        nodes = self.G.nodes(data=True)
        if filter_key is not None and filter_value is not None:
            new_nodes = []
            if not isinstance(filter_value, str):
                filter_value = [filter_value]

            for nid, attrs in nodes:
                if attrs.get(filter_key) == filter_value:
                    new_nodes.append((nid, attrs))
            nodes = new_nodes
        return nodes

    
    def get_edges_src_trgt_pos(self, G=None, get_pos=False) -> list[dict]:
        if G==None:
            G = self.G
        edges=[]
        valid_types = [*ALL_SUBS, "PIXEL"]
        for src, trgt, attrs in G.edges(data=True):
            src_attrs = G.nodes[src]
            trgt_attrs = G.nodes[trgt]

            src_type = src_attrs["type"]
            trgt_type = trgt_attrs["type"]

            if src_type in valid_types and trgt_type in valid_types:
                if get_pos is True:
                    src_pos = src_attrs["pos"]
                    trgt_pos = trgt_attrs["pos"]

                    # todo calc weight based on
                    edges.append(
                        dict(
                            src=src_pos,
                            trgt=trgt_pos
                        )
                    )
                else:
                    edges.append(
                        dict(
                            src=src,
                            trgt=trgt
                        )
                    )
        #print(f"edge src trgt pos set: {edges}")
        return edges

    def create_html(self):
        save_path = os.path.join(
            self.file_store.name,
            "graph.html",
        )
        html = create_g_visual(self.datastore, dest_path=None)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML Graph was written to: {save_path}")





    def categorize_nodes_in_types(self, valid_ntypes=ALL_SUBS) -> dict[list]:
        categorized = {}
        for nid, attrs in self.G.nodes(data=True):
            ntype = attrs.get("type")
            if ntype:
                ntype=ntype.upper()
            if ntype in [n.upper() for n in valid_ntypes]:
                if ntype not in categorized:
                    categorized[ntype] = []
                categorized[ntype].append(
                    (nid, attrs)
                )
        print("Nodes in types categorized")
        return categorized

    def categorize_nodes_in_qfns(self) -> dict[list[tuple]]:
        categorized = {}
        points = [(nid, attrs) for nid, attrs in self.G.nodes(data=True) if attrs.get("type") == "PIXEL"]

        for qfn in points:
            qfn_id = qfn[0]
            categorized[qfn_id] = self.get_neighbor_list(qfn_id, trgt_rel="has_field")

        print("Nodes in PIXELs categorized")
        return categorized








"""


initial_frontend_data[node_type].update(
{
attrs.get("id", edge_id): {
"src": parts[0],
"trgt": parts[1],
"color": attrs.get("color")
}
}
)


"""