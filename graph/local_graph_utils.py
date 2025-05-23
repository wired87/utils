import asyncio
import json
import os
import pprint
import re
import time
from typing import List

import networkx as nx

from _google.firebase.real_time_database import FirebaseRTDBManager
from bm.settings import TEST_USER_ID
from utils.file.flatten_dict import flatten_attributes

from bm.logging_custom import cpr
from utils.gnn.processing.graph_manipulator import Manipulator
from utils.queue_handler import QueueHandler
from utils.utils import Utils
import queue


class LocalGraphUtils(Utils):

    def __init__(
            self,
            user_id=TEST_USER_ID,
            env_id="env_bare_rajtigesomnlhfyqzbvx",
            G=None,
            g_from_path=None,
            nx_only=False,
            upload_to: str = "bq",  # bq || sp || fb
            loop:asyncio.AbstractEventLoop=None,
            database=None,
            queue: queue.Queue or None = None,
            **args
    ):
        super().__init__()
        self.G = None
        self.g_from_path=g_from_path
        self.get_nx_graph(G)
        self.nx_only = nx_only
        self.loop=loop

        if upload_to == "fb":
            self.firebase = FirebaseRTDBManager(base_path=database)

        self.manipulator = Manipulator()
        self.q_handler = QueueHandler(queue)

        #history: list[dict[id: list[history]]]
        self.history = {}

        self.upload_to=upload_to
        self.schemas = {}
        """table_name: {
        "schema": {},
        "rows": [],
        "id_map": set(),
        },"""

    ####################################
    # CORE
    ####################################

    def add_node(self, attrs: dict, flatten=False, single_upsert=False, timestep=None):
        attrs = self.clean_attr_keys(attrs, flatten)
        attrs["type"] = attrs["type"].upper()
        # print(">>NODE FILTERED")
        # print(f"Add {attrs['id']} -> layer: {attrs['type']}")
        """if single_upsert is True:
            await self.g.upsert_row(
                table=f"{edge_attrs['src_layer'].upper()}_{edge_attrs['rel']}_{edge_attrs['trgt_layer'].upper()}",
                batch_chunk=[edge_attrs])"""

        if self.nx_only is False:
            self.local_batch_loader(attrs)
        self.G.add_node(attrs["id"], **{k: v for k, v in attrs.items() if k != "id"})

        # todo just add each entry here results in doubles -> filter at upload process then
        if timestep:
            self.add_history_entry(
                nid=attrs.get("id"),
                ntype=attrs["type"],
                attrs=attrs,
                timestep=timestep
            )
        return True

    def add_edge(self, src=None, trt=None, attrs: dict or None = None, flatten=False, timestep=None):
        #pprint.pp(attrs)
        #print(f"Add edge {src}->{attrs.get('rel')}->{trt}")
        try:
            src_layer = self.replace_special_chars(attrs.get("src_layer")).upper()
            trgt_layer = self.replace_special_chars(attrs.get("trgt_layer")).upper()

            # print("src_layer", src_layer)
            # print("trgt_layer", trgt_layer)
            if src is None:
                src = attrs.get("src")
            if trt is None:
                trt = attrs.get("trt")

            if src and trt and src_layer and trgt_layer:
                if isinstance(src, int):
                    src = str(src)
                if isinstance(trt, int):
                    trt = str(trt)
                # print("int conv...")

                attrs = self.clean_attr_keys(attrs, flatten)
                # print("attrs_new", attrs )
                rel = attrs.get("rel", "").lower().replace(" ", "_")

                attrs = {
                    **attrs,
                    "src": src,
                    "trgt": trt,
                    "id": f"{src}_{rel}_{trt}"
                }

                # print(">>FILTERED EDGE")
                # pprint.pp(attrs)

                src_layer = attrs.get("src_layer").upper()
                trgt_layer = attrs.get("trgt_layer").upper()

                # print(f"ids {src} -> {trt}; Layer {src_layer} -> {trgt_layer}")

                edge_table_name = f"{src_layer}_{rel}_{trgt_layer}"
                attrs["type"] = edge_table_name

                src_node_attr = {"id": src, "type": src_layer}

                trgt_node_attr = {"id": trt, "type": trgt_layer}
                # print(f"Add {src} -> trgt: {trt}")

                if self.nx_only is False:
                    # todo run in executor
                    self.local_batch_loader(src_node_attr)
                    self.local_batch_loader(trgt_node_attr)
                    self.local_batch_loader(attrs)

                self.G.add_edge(src, trt, **{k: v for k, v in attrs.items() if k not in ["src", "trgt"]})
                self.G.add_node(src, **src_node_attr)
                self.G.add_node(trt, **trgt_node_attr)

                if timestep:
                    self.add_history_entry(
                        nid=attrs.get("id"),
                        ntype=attrs["type"],
                        attrs=attrs,
                        timestep=timestep
                    )

        except Exception as e:
            print(f"Skipping link src: {src} -> trgt: {trt} cause:", e)


    def add_history_entry(self, nid, ntype, attrs, timestep):
        """
        Adds all changes to a local history
        todo: directly upload here to spanner
        """
        print("Extend history")
        # Load local history
        if ntype not in self.history:
            self.history[ntype] = {}

        if not self.history[ntype].get(nid):
            self.history[ntype][nid] = {}

        # Include timestep key (for multiple updates / iteration
        if not self.history[ntype][nid].get(timestep):
            self.history[ntype][nid][timestep] = []

        self.history[ntype][nid][timestep].append(dict(id=nid, **{k: v for k, v in attrs.items() if k != "id"}))

        if len(self.history[ntype][nid][timestep]) > 10000:
            print("history limit exceeded -> push batch")
            # push updates todo: save history alltimes in BQ (after limit increase)
            self.q_handler.add_task(
                db_path=f"HIS_{ntype}/{nid}/{timestep}/",
                attrs=attrs
            )
        print("Finished history")

    def update_node(self, nid, attrs, timestep):
        print("Update node", nid)
        ntype = attrs.get("type")

        self.add_history_entry(nid, ntype, attrs, timestep)

        self.G.nodes[nid].update(attrs)
        if self.upload_to in ["sp", "bq"]:
            for item in self.schemas[ntype]["rows"]:
                if item["id"] == nid:
                    item.update(attrs)
        else:
            # Update directly to FB
            # Load to queue to update FB
            """
            self.q_handler.add_task(
                db_path=f"HIS_{ntype}/{nid}/",
                attrs=attrs
            )
            """
            pass
        return


    def update_edge(self, src, trgt, attrs, timestep):
        rel = attrs.get("rel", "").lower().replace(" ", "_")
        src_layer = attrs.get("src_layer").upper()
        trgt_layer = attrs.get("trgt_layer").upper()
        table_name = f"{src_layer}_{rel}_{trgt_layer}"
        edge_id = f"{src}_{rel}_{trgt}"

        # Add to history
        self.add_history_entry(edge_id, "edges", attrs, timestep)

        # Update nx
        self.G.edges[src][trgt].update(attrs)

        # Update dest specific
        if self.upload_to in ["sp", "bq"]:
            for item in self.schemas[table_name]["rows"]:
                if item["id"] == edge_id:
                    item.update(attrs)

        else:
            # Load to queue to update FB
            """self.q_handler.add_task(
                db_path=f"{table_name}/{edge_id}/",
                attrs=attrs
            )"""
            pass

        return


    ####################################
    # FIREBASE HANDLING
    ####################################
    """ 
    def upsert_firebase(
            self,
            fb_dest=None
    ):

        updates = {}
        for nid, attrs in self.G.nodes(data=True):
            ntype = attrs.get("type")
            if not ntype in updates:
                updates[ntype] = []
            if not ntype in ["USERS"]:
                updates[ntype].append(
                    {k: v for k, v in attrs.items()}
                )

        updates["edges"] = []
        for src, trgt in self.G.edges():
            edge_attrs = self.G.get_edge_data(src, trgt)
            updates["edges"].append(
                edge_attrs
            )
        # print("updates", updates)
        self.firebase.upsert_batch(updates, fb_dest)"""

    def upsert_firebase(
            self,
            fb_dest=None
    ):
        updates = {
            # Schlüssel: der Ziel-Pfad für den Knoten
            f"{attrs.get('type')}/{nid}":
            # Wert: das Attribut-Dictionary des Knotens, ohne den Schlüssel 'id'
                {k: v for k, v in attrs.items() if k not in ["id", "symbol"]}

            # Die Schleife, die die Elemente (nid, attrs) liefert
            for nid, attrs in self.G.nodes(data=True)
        }

        for src, trgt in self.G.edges():
            edge_attrs = self.G[src][trgt]
            #print("edge_attrs", edge_attrs)


            for key,value in edge_attrs.items():
                #print("Edge value", value)

                path = f"edges/{src}_{value.get('rel')}_{trgt}"
                updates.update(
                    {
                        path: {k: v for k, v in value.items() if k not in ["id", "symbol"]}
                    }
                )
        # print("updates", updates)
        self.firebase.upsert_batch(updates, fb_dest)












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
            self.G = nx.MultiGraph()
        print("Local Graph loaded")

    def save_graph(self, dest_name):
        data = nx.node_link_data(self.G)
        with open(f"{dest_name}", "w") as f:
            json.dump(data, f)
        print("Graph saved:", dest_name)
        return data



    def load_graph(self, local_g_path=None):
        if local_g_path is None:
            local_g_path = self.g_from_path
        """Loads the networkx graph from a JSON file."""
        cpr(f"📂 Loading graph from {local_g_path}...")
        with open(local_g_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)  # Use json.load() for files, not json.loads()
        self.G = nx.node_link_graph(graph_data)
        cpr(f"✅ Graph loaded! {len(self.G.nodes)} nodes, {len(self.G.edges)} edges.")


    def print_status_G(self):
        print(">>>STATUS")
        print(f" Nodes {len(self.G.nodes)}")
        print(f" Edges {len(self.G.edges)}")

    def print_status(self):
        print(">>>STATUS")
        for k, v in self.schemas.items():
            print(f"Table {k}: \n{len(v['rows'])} rows \n")

    def get_edge_attrs(self, parent, child):
        edge_attrs = self.G[parent["id"]][child["id"]]
        # Todo fetch directly form sp or bq
        print("Attrs fetched", edge_attrs)

    def replace_special_chars(self, s):
        """
        Replaces all special characters in a string with "_".
        Keeps only alphanumeric characters and underscores.

        :param s: Input string
        :return: Cleaned string with special characters replaced
        """
        return re.sub(r'[^a-zA-Z0-9_]', '', s)



    def clean_attr_keys(self, attrs, flatten=True, stringify=False):
        """
        Cleans attribute dictionary by:
        - Flattening nested attributes.
        - Removing duplicate keys after replacing special characters.
        - Ensuring consistency in column names.
        """

        cleaned_attrs = {}
        if flatten:
            attrs = flatten_attributes(attrs)

        for k, v in attrs.items():
            clean_key = self.replace_special_chars(k)
            if clean_key in cleaned_attrs:
                continue
            else:
                if stringify is True:
                    v = self.stringify_dict(v)
                cleaned_attrs[clean_key] = v

            """if isinstance(v, dict):
                # stringify dict
                cleaned_attrs[k] = json.dumps(v)"""

        for k, v in cleaned_attrs.items():
            if isinstance(v, str):
                cleaned_attrs[k] = v.replace("'", "")

        cleaned_attrs = self.manipulator.manipulator_dictribnutor(cleaned_attrs)
        return cleaned_attrs

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
                print(f"Added {table_name} to schema")

            if row_id not in [item for item in self.schemas[table_name]["id_map"]]:
                #print(f"Insert {row_id} into {table_name}")
                self.schemas[table_name]["rows"].append(args)
                self.schemas[table_name]["id_map"].add(row_id)
            # else:
            # print(f"{row_id} already in schema")
        # print("Added args")


    def stringify_dict(self, v):
        if isinstance(v, dict):
            v = json.dumps(v)
        elif isinstance(v, list):
            new_v = []
            for value in v:
                if isinstance(value, dict):
                    new_v.append(json.dumps(value))
                else:
                    new_v.append(value)
            v = new_v
        return v


    def get_single_neighbor_nx(self, node, target_type):
        # print("Node", node)
        if isinstance(node, tuple):
            node = node[0]
        for neighbor in self.G.neighbors(node):
            if self.G.nodes[neighbor].get('type') == target_type:
                return neighbor, self.G.nodes[neighbor]
        return None, None  # No neighbor of that type found

    def get_neighbor_list(self, node, target_type: str or list) -> List[tuple] or None:
        neighbors = []
        if isinstance(target_type, str):
            target_type = [target_type]
        for neighbor in self.G.neighbors(node):
            if self.G.nodes[neighbor].get('type') in target_type:
                neighbors.append((neighbor, self.G.nodes[neighbor]))
        return neighbors


    def remove_node(self, node_id, ntype):
        for row in self.schemas[ntype]["rows"]:
            if row["id"] == node_id:
                self.schemas[ntype]["rows"].remove(row)
                break
        self.G.remove_node(node_id)


