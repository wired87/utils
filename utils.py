from _google.bq.loader.aloader import ABQHandler
from utils.gnn.embedder import embed
from utils.file.aread_json import aread_content


# todo batch process: collect, then send up in batches

def replace_special_chars(s):
    """
    Replaces all special characters in a string with "_".
    Keeps only alphanumeric characters and underscores.

    :param s: Input string
    :return: Cleaned string with special characters replaced
    """
    return re.sub(r'[^a-zA-Z0-9_]', '', s)



import pprint
import re

import asyncio
import csv
import json
import os
from typing import Dict, List, Any, Union, Tuple, Optional

import aiofiles
import httpx
import networkx as nx
import yaml
from tqdm import tqdm

from _google.spanner.acore import SpannerAsyncHelper

from bm.logging_custom import cpr
from utils.file.flatten_dict import flatten_attributes
from _google.storage.storage import GBucket
from _google.spanner.graph_loader import SpannerGraphLoader
from utils.gnn.processing.graph_manipulator import Manipulator


# todo batch process: collect, then send up in batches

class GraphUtils(
    SpannerGraphLoader,
    SpannerAsyncHelper,
    #BigQueryGraphHandler,
    ABQHandler
):
    def __init__(
            self,
            table_name="CELL",
            upload_to: str = "bq",
            not_null_check_col="id",
            sp_dbid=None,
            cache_only=False,
            G=None,
            dataset=None
    ):
        #super().__init__()
        #ABQHandler.__init__(self)
        self.dataset=dataset
        SpannerAsyncHelper.__init__(self, sp_dbid)
        SpannerGraphLoader.__init__(self, sp_dbid)
        ABQHandler.__init__(self, dataset=dataset)
        #BigQueryGraphHandler.__init__(self)

        self.G = G or nx.Graph()

        self.table_name = table_name
        self.upload_to = upload_to
        self.bucket = GBucket()
        self.utils = Utils()
        self.manipulator = Manipulator()
        self.batch_chunk_size = 10000
        self.loop_count = 0
        self.not_null_check_col = not_null_check_col
        self.schemas = {

        }
        """self.table_name: {
                        "schema": {},
                        "rows": [],
                        "id_map": set(),
                    },"""

        # For localized G loading for changes while loop
        self.cache = []
        self.cache_trash = []
        self.ecache_trash = []

        self.tables_created = []
        self.edge_batch = {}
        self.runs = 0
        self.all_tables = self.list_spanner_tables() if upload_to == "sp" else self.get_tables()
        self.cache_only = cache_only





    ####################################
    # CORE
    ####################################


    async def abatch_commit(self, embed_only=True):
        """Need to be called after each layer process finished with rest_commit
        if any(len(v["rows"]) > self.batch_chunk_size for v in self.schemas.values()) or rest_commit and not self.commit:
        self.commit=True
        """
        print(">>>Start batch commit")
        try:
            self.print_status()
            await self.acreate_session()
            await self.acreate_tables_batch()
            await self.aschema_batch_process()
            await self.aupsert_batch(embed_only)
            self.cleanup_self_schema()
        except Exception as e:
            print(f"Error during abatch_commit: {e}")
        print(">>>Finished")

    async def batch_commit(self):
        """Need to be called after each layer process finished with rest_commit
        if any(len(v["rows"]) > self.batch_chunk_size for v in self.schemas.values()) or rest_commit and not self.commit:
        self.commit=True
        """
        print(">>>Start batch commit")
        self.print_status()
        self.create_tables_batch()
        self.schema_batch_process()
        self.upsert_batch()
        self.cleanup_self_schema()
        print(">>>Finished")







    def add_node(self, attrs: dict, flatten=False):
        attrs = self.clean_attr_keys(attrs, flatten)
        attrs["type"] = attrs["type"].upper()
        # print(">>NODE FILTERED")
        #print(f"Add {attrs['id']} -> layer: {attrs['type']}")
        self.local_batch_loader(attrs)
        if self.cache_only is False:
            self.G.add_node(attrs["id"], **{k: v for k, v in attrs.items() if k != "id"})

        return True

    def add_edge(self, src=None, trt=None, attrs: dict or None = None, flatten=False):
        #pprint.pp(attrs)

        try:

            src_layer = replace_special_chars(attrs.get("src_layer")).upper()
            trgt_layer = replace_special_chars(attrs.get("trgt_layer")).upper()

            #print("src_layer", src_layer)
            #print("trgt_layer", trgt_layer)
            if src is None:
                src = attrs.get("src")
            if trt is None:
                trt = attrs.get("trt")

            if src and trt and src_layer and trgt_layer:
                if isinstance(src, int):
                    src = str(src)
                if isinstance(trt, int):
                    trt = str(trt)
                #print("int conv...")

                attrs = self.clean_attr_keys(attrs, flatten)
                #print("attrs_new", attrs )
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

                #print(f"ids {src} -> {trt}; Layer {src_layer} -> {trgt_layer}")

                edge_table_name = f"{src_layer}_{rel}_{trgt_layer}"
                attrs["type"] = edge_table_name

                src_node_attr = {"id": src, "type": src_layer}

                trgt_node_attr = {"id": trt, "type": trgt_layer}
                # print(f"Add {src} -> trgt: {trt}")

                # todo run in executor
                self.local_batch_loader(src_node_attr)
                self.local_batch_loader(trgt_node_attr)
                self.local_batch_loader(attrs)

                if self.cache_only is False:
                    self.G.add_edge(src, trt, **{k:v for k,v in attrs.items() if k not in ["src", "trgt"]})
                else:
                    self.cache.append(dict(
                        src=src,
                        trgt=trt,
                        **{k: v for k, v in attrs.items() if k not in ["src", "trgt"]}
                    )
                )

                #self.G.add_node(src, type=src_layer)
                #self.G.add_node(trt, type=trgt_layer)

        except Exception as e:
            print(f"Skipping link src: {src} -> trgt: {trt} cause:", e, )



    ####################################
    # HELPER
    ####################################


    def get_ids(self, table=None):
        if table is None:
            table = self.table_name
        if self.upload_to == "sp":
            ids = self.get_all_ids(table)
        else:
            ids = self.get_column_values(table, "id", )
        print(f"Fetched {len(ids)} ids from {table}")
        return ids


    def save_ckpt(self, path, content, mode="j"):
        with open(path, "w") as f:
            json.dump(content, f)

    def data_preprocessor(self, data: list[dict] = [], keys_to_remove: list[str] = [], key="id") -> list[dict]:
        print(f"Removing {len(keys_to_remove)}/{len(data)} ({len(data) - len(keys_to_remove)} processed ids ")
        filtered_data = [item for item in data if item.get(key) not in keys_to_remove]
        print("Entries left:", len(filtered_data))
        return filtered_data

    async def load_content(
            self,
            local_path,
            bucket_path,
            layer,
            test_chunk,
            testing
    ):
        print("Load content")
        if testing is not None:
            content = await aread_content(test_chunk)
        else:

            if not os.path.exists(local_path):
                print(f"Local path {local_path} does not exists. Fetch from {bucket_path}")
                content = json.loads(self.bucket.download_blob(bucket_path))
                content = self.utils.structure_content_save(
                    content,
                    layer=layer,
                    save_to=local_path,
                    single=False
                )
            else:
                print("Fetch content from", local_path)
                with open(local_path, 'r') as f:
                    content = json.load(f)
        # print("Content load")
        return content

    async def alocal_batch_loader(self, args):
        table_name = args.get("type")
        row_id = args["id"]
        if table_name:
            if table_name not in self.schemas:
                self.schemas[table_name] = {
                    "schema": {},
                    "rows": [],
                    "id_map": set(),
                }
                # print(f"Added {table_name} to schema")

            if row_id not in [item for item in self.schemas[table_name]["id_map"]]:
                self.schemas[table_name]["rows"].append(args)
                self.schemas[table_name]["id_map"].add(row_id)

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
                print(f"Insert {row_id} into {table_name}")
                self.schemas[table_name]["rows"].append(args)
                self.schemas[table_name]["id_map"].add(row_id)
            else:
                print(f"{row_id} already in schema")
        #print("Added args")


    async def acreate_tables_batch(self):
        # print("Creating tables batch")
        if self.upload_to == "sp":
            await asyncio.gather(*[
                self.acheck_add_table(
                    table_name=k,
                    ttype="edge" if any(c.islower() for c in k) else "node",
                    schema_fetch=False
                ) for k, v in self.schemas.items() if k not in self.all_tables])

            print("Table process finished")

        else:
            for k, v in self.schemas.items():
                # todo get all (filtered) bq tables
                await self.acheck_add_bq_table(
                    table_name=k,
                    ttype="edge" if any(c.islower() for c in k) else "node",
                    schema_fetch=False
                )

    def create_tables_batch(self):
        # print("Creating tables batch")
        if self.upload_to == "sp":
            for k, v in self.schemas.items():
                print("k",k)
                if k not in self.all_tables:
                    self.check_add_table(
                        table_name=k,
                        # Check if min one chear is lower
                        ttype="edge" if any(c.islower() for c in k) else "node",
                        schema_fetch=False
                    )
        else:
            for k, v in self.schemas.items():
                # todo get all (filtered) bq tables
                self.get_create_bq_table(
                    table_name=k,
                    ttype="edge" if any(c.islower() for c in k) else "node",
                )

    async def aschema_batch_process(self):
        # print("Schema process")
        for k, v in self.schemas.items():
            all_keys = set().union(*(row.keys() for row in v["rows"]))
            for row_key in all_keys:
                sample_value = next((row[row_key] for row in v["rows"] if row_key in row), None)
                if sample_value is not None:
                    if self.upload_to == "sp":
                        col_type = self.get_spanner_type(sample_value)
                    else:
                        col_type = self.get_bq_type(sample_value)
                    print("Adding row key", row_key, col_type)
                    v["schema"][row_key] = col_type

        if self.upload_to == "sp":
            await asyncio.gather(
                *[
                    self.aadd_col(
                        keys=v["schema"],
                        table=k,
                        type_from_val=False,
                    ) for k, v in self.schemas.items()
                ]
            )
        else:
            for k, v in self.schemas.items():
                await self.aupdate_bq_schema(
                    keys=v["schema"],
                    table=k
                )

    def schema_batch_process(self):
        # print("Schema process")
        for k, v in self.schemas.items():
            all_keys = set().union(*(row.keys() for row in v["rows"]))
            for row_key in all_keys:
                sample_value = next((row[row_key] for row in v["rows"] if row_key in row), None)
                if sample_value is not None:
                    if self.upload_to == "sp":
                        col_type = self.get_spanner_type(sample_value)
                    else:
                        col_type = self.get_bq_type(sample_value)
                    # print("Adding row key", row_key, spanner_type)
                    v["schema"][row_key] = col_type

        if self.upload_to == "sp":
            for k, v in self.schemas.items():
                self.check_add_cols_batch(
                    keys=v["schema"],
                    t=k
                )
        else:
            for k, v in self.schemas.items():
                self.update_bq_schema(
                    keys=v["schema"],
                    table=k
                )

    def clear_cache(self):
        for nid in self.cache_trash:
            self.G.remove_node(nid)

        """RM a Node"""
        for (src, trgt) in self.ecache_trash:
            self.G.remove_edge(src, trgt)

    def rmn(self, nid, ion_parent_id=None):
        """RM a Node"""
        print(f"Rm {nid} from {ion_parent_id}")
        self.cache_trash.append(nid)

    def rme(self, src, trgt):
        self.ecache_trash.append((src, trgt))

    async def aupsert_batch(self, embed_only):
        print("Begin upsert process")
        if self.upload_to == "sp":
            tasks = []
            print("self.schemas", self.schemas)
            for k, v in self.schemas.items():
                rows=[embed(row) for row in v["rows"]] if embed_only else v["rows"]
                print("Len rows", len(rows))
                tasks.append(
                    self.aupdate_insert(
                        table=k,
                        rows=rows
                    )
                )
            await asyncio.gather(*tasks)

            print("Batch upserted")
        else:
            for k, v in self.schemas.items():
                self.bq_insert(k, v["rows"])

    def upsert_batch(self):
        if self.upload_to == "sp":
            for k, v in self.schemas.items():
                self.update_insert(
                    table=k,
                    rows=v["rows"]
                )
        else:
            for k, v in self.schemas.items():
                self.bq_insert(k, v["rows"])

    def cleanup_self_schema(self):
        # print("Cleanup schema")
        for k, v in self.schemas.items():
            v["rows"] = []

    def print_status(self):
        print(">>>STATUS")
        for k, v in self.schemas.items():
            print(f"Table {k}: \n{len(v['rows'])} rows \n")
    def print_status_G(self):
        print(">>>STATUS")
        nodes = {}
        for k, v in self.G.nodes(data=True):
            node_type = v.get("type")
            if node_type not in nodes:
                nodes[node_type] = 0
            nodes[node_type] += 1
        pprint.pp(nodes)




    def get_single_neighbor_nx(self, node, target_type):
        #print("Node", node)
        if isinstance(node, tuple):
            node=node[0]
        for neighbor in self.G.neighbors(node):
            if self.G.nodes[neighbor].get('type') == target_type:
                return neighbor, self.G.nodes[neighbor]
        return None, None  # No neighbor of that type found

    def get_neighbor_list(self, node, target_type:str or list) -> List[tuple] or None:
        neighbors = []
        if isinstance(target_type, str):
            target_type = [target_type]
        for neighbor in self.G.neighbors(node):
            if self.G.nodes[neighbor].get('type') in target_type:
                neighbors.append((neighbor, self.G.nodes[neighbor]))
        return neighbors

    def get_len_neighbors_type_nx(self, node, target_type):
        len_neighbors = 0
        for neighbor in self.G.neighbors(node):
            if self.G.nodes[neighbor].get('type') == target_type:
                return neighbor, self.G.nodes[neighbor]
        return None  # No neighbor of that type found

    def get_gene_id_name(self, chrom=False):
        if chrom:
            query = f"""
                SELECT id, coord_system_seq_name, start, 'end' 
                FROM GENE 
                WHERE id IS NOT NULL 
                  AND coord_system_seq_name IS NOT NULL 
                  AND start IS NOT NULL 
                  AND 'end' IS NOT NULL
              """
        else:
            query = f"""
                    SELECT id, name FROM GENE WHERE id IS NOT NULL AND name IS NOT NULL
                    """
        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(query)

        if results:
            if chrom:
                stuff = [{"id":stuff[0], "chrom":stuff[1], "start":stuff[2], "end":stuff[3]} for stuff in results]
                print("Gene entry 0", stuff[0])
            else:
                stuff = {f"{stuff[0]}": stuff[1] for stuff in results}
                print("Gene entries", len(stuff.items()))
            return stuff



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
            clean_key = replace_special_chars(k)
            if clean_key in cleaned_attrs:
                continue
            else:
                if stringify is True:
                    v = self.stringify_dict(v)
                cleaned_attrs[clean_key] = v

            """if isinstance(v, int):
                cleaned_attrs[k] = str(v)"""

        for k, v in cleaned_attrs.items():
            if isinstance(v, str):
                cleaned_attrs[k] = v.replace("'", "")

        cleaned_attrs = self.manipulator.manipulator_dictribnutor(cleaned_attrs)
        return cleaned_attrs

    def table_schema_process(self, table_name, attrs, ttype="node"):
        if not self.schemas.get(table_name):
            # create table, return its default schema (if new created), update local
            schema = self.check_add_table(table_name=table_name, ttype=ttype)
            # print("schema", schema)
            self.schemas[table_name] = schema

        for k, v in attrs.items():
            if k not in self.schemas.get(table_name):
                spanner_type = self.get_spanner_type(v)
                self.check_add_cols(
                    col_type=spanner_type,
                    key=k,
                    t=table_name,
                    existing_cols=self.schemas[table_name].keys()
                )
                self.schemas[table_name][k] = spanner_type

        for k, v in attrs.items():
            # print("kv", k, v)
            if k not in self.schemas.get(table_name):
                self.schemas[table_name].update({k: self.get_spanner_type(v)})


    ############ SPANNER
    async def atable_schema_process(self, table_name: str, attrs: Dict, ttype: str = "node"):
        if not self.schemas.get(table_name):
            # create table, return its default schema (if new created), update local
            schema = await self.acheck_add_table(table_name=table_name, ttype=ttype)
            # print("schema", schema)
            self.schemas[table_name] = schema
        try:
            if self.upload_to == "sp":
                schema = await self.aadd_col(keys=attrs, table=table_name, existing_schema=self.schemas[table_name])
                # print("table schema", schema)
            else:
                schema = await self.update_bq_schema(keys=attrs, table=table_name)
            if isinstance(schema, dict) and len(schema.keys()):
                self.schemas[table_name].update(schema)
        except Exception as e:
            print("Error in atable_schema_process", e)

    ##############BQ

    async def bqaadd_edge(self, table_name):
        if not self.schemas.get(table_name):
            self.schemas[table_name]: List[Dict] = []
        if self.schemas.get(table_name) and len(self.schemas[table_name]) >= 5000:
            # upload bq batch
            schema = {}
            for item in self.schemas[table_name]:
                for k, v in item.items():
                    if k not in schema:
                        schema[k] = self.get_spanner_type(v)

    ################################################################################################

    async def find_node_by_attribute(self, attr_name, attr_value):
        """Finds a node by attributCheck if Spanner tablee value (Optimized)."""
        g_list = list(self.G.nodes(data=True))
        return next((node for node, attrs in g_list if attrs.get(attr_name) == attr_value), None)

    async def nx_node(self, attrs):
        """✅ Fix: Rename `type` to `node_type` to prevent NetworkX conflicts."""
        src = attrs.pop("id", None)  # ✅ Remove `id` from attrs safely
        if not src or "#" in src:
            return  # ✅ Prevent invalid nodes

        attrs["type"] = attrs["type"].upper()

        if src not in self.G:
            new_stuff = {k: v for k, v in attrs.items() if k != "id"}

            print("Adding node", src)
            self.G.add_node(src, **new_stuff)
        else:
            # ✅ Update existing node safely
            node_data = self.G.nodes[src]
            for k, v in attrs.items():
                if k not in node_data:
                    self.G.nodes[src][k] = v

    def load_graph(self, graph_file):
        """Loads the networkx graph from a JSON file."""
        if graph_file:
            cpr(f"📂 Loading graph from {graph_file}...")
            with open(graph_file, "r", encoding="utf-8") as f:
                graph_data = json.load(f)  # Use json.load() for files, not json.loads()
            self.graph = nx.node_link_graph(graph_data)
            cpr(f"✅ Graph loaded! {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges.")


    async def add_edge_nx(self, src, trt, attrs):
        attrs = attrs or {}
        if not self.G.has_edge(src, trt):
            self.G.add_edge(src, trt, **attrs)



class Utils:

    def __init__(self, info=None):
        self.bucket = GBucket("bestbrain")
        self.info = info
        #self.local_dest_base = LOCAL_DEST_BASE
        #self.bucket_dest_base = BUCKET_DEST_BASE

    async def get_file_metadata_async(self, url: str, just_size=True) -> dict or None:
        """Retrieves file metadata asynchronously using a HEAD request."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.head(url, follow_redirects=True)
                response.raise_for_status()
                h_info = response.headers
                if response and h_info and just_size:
                    if 'content-length' in h_info:
                        size = h_info['content-length']
                        print(f"File Size: {size} bytes")
                        return size
                return dict(response.headers)
            except httpx.RequestError as e:
                print(f"Error: {e}")
                return None

    async def load_content(self, path, layer, local, single=False, save_to=None):
        """
        Set save url
        check exists
        fetch
        prep
        save
        return
        """
        if local:
            path = local

        print("Fetch content from", path)
        if not os.path.exists(path):
            content = json.loads(self.bucket.download_blob(path))
            content = self.structure_content_save(content, layer=layer, save_to=save_to, single=single)
        else:
            # Path exists, -> handle file types
            print("Load file local")
            if path.endswith("tsv"):
                content = []
                with open(path, 'r', newline='', encoding='utf-8') as tsvfile:
                    reader = csv.DictReader(tsvfile, delimiter='\t')  # Important to define the delimeter.
                    for row in reader:
                        content.append(row)
            elif path.endswith("json"):
                content = await aread_content(save_to)

            with open(path, "rb") as f:
                content = f.read()
        print("Content load successful")
        return content

    def structure_content_save(self, content, layer, single, save_to):
        if isinstance(content, dict):
            if layer.lower() == "gene":
                content = content["genes"]
            elif layer.lower() == "protein":
                content = content["results"]
        else:
            print("first_item", content[0])

        if single:
            content = content[0]
        print("content set")

        dir_path = os.path.dirname(save_to)
        if not os.path.exists(dir_path) or os.path.isfile(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        print("save_to", save_to)
        with open(save_to, "w") as f:
            json.dump(content, f)
        print("content saved")
        return content

    async def save_layer_ckpt(self, bucket_path, loal_path, data=None, graph_type=None):
        """
        Save the graph as a JSON file and upload it to the bucket.
        """
        print("upload graph to bucket")

        if graph_type in ["protein", "gene"]:
            print("Graph needs to be split since it's too heavy")


        # Convert graph to node-link format
        data = nx.node_link_data(data)
        data["is_multigraph"] = False

        # 🔹 Ensure `loal_path` is a string before passing it
        loal_path_str = str(loal_path)

        # Upload JSON data
        await self.bucket.upload_json_to_folder(
            json_content=data,
            bucket_path=bucket_path,
            local_path=loal_path_str  # 🔹 Fix: Convert Path to String
        )

    async def aget(self, url, j: str or bool = True):
        #print("get content from ", url)

        size = None
        if j:
            headers = {
                "Content-Type": "application/json"
            }
        i = 0
        async with httpx.AsyncClient() as client:
            while i !=3:
                try:
                    if j:
                        r = await client.get(url, headers=headers, timeout=999.0)
                    else:
                        r = await client.get(url, timeout=999.0)

                    if r.is_success:
                        content = r.text
                        if j is True:
                            content = r.json()

                        elif j == "b":
                            content = r.content

                        elif j=="y":
                            content = yaml.safe_load(r.content)

                        else:
                            r = r.content
                            size = len(r)
                        print("Content gathered ")
                        return content, size

                except Exception as e:
                    print(f"Request failed: {e}, retrying...")
                    await asyncio.sleep(1)
                    i += 1
                    continue  # try again


    async def apost(self, url: str, data=dict()) -> dict or None:
        headers = {'Content-Type': 'application/json'}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers, timeout=999.0)
                if response.is_success:
                    return response.json()
        except Exception as e:
            print(f'Request failed: {e}, retrying...')
        return None


    async def download_json_content(
            self,
            url,
            j=True,
            save: str or None = None,  # file_name
            save_layer: str or None = None
    ):
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url) as response:
                # Check if the response is successful
                if response.status_code != 200:
                    print(f"Failed to download JSON: {response.status_code}")
                    return None
                total_size = int(response.headers.get("content-length", 0))
                print(f"File size: {total_size}")
                progress = tqdm(total=total_size, unit="B", unit_scale=True, desc="Downloading JSON")
                print("Downloading JSON", progress)
                # Gather content
                content = bytearray()
                async for chunk in response.aiter_bytes(chunk_size=1024):
                    content.extend(chunk)
                    progress.update(len(chunk))

                progress.close()

                # Decode JSON content
                try:
                    if j:
                        content = json.loads(content.decode('utf-8'))  # Parse JSON
                        # print("JSON content", json_content)
                        if save:
                            await self.save_process(file_name=save, content=content, layer=save_layer)
                    else:
                        content = content.decode('utf-8')
                    return content
                except json.JSONDecodeError as e:
                    print(f"Failed to decode JSON: {e}")
                    return None

    async def save_process(self, file_name, content, layer=None):

        if layer is None:
            dest_local = os.path.join(self.local_dest_base, file_name)
            dest_bucket = self.bucket_dest_base + file_name
        else:
            dest_local = os.path.join(self.local_dest_base, layer, file_name)
            dest_bucket = f"{self.bucket_dest_base}{layer}/{file_name}"

        await self.asave_ckpt_local(dest_local, content)
        self.bucket.upload_from_str(dest_path=dest_bucket, content=content)

    async def get_process(self, request_path):
        json_file: bool = request_path.endswith('.json')
        file_name = request_path.split("/")[-1]
        save_local = os.path.join(self.local_dest_base, file_name)
        try:

            if os.path.exists(request_path):
                print("Fetch content local")
                content = await self.aread_content(request_path, j=json_file)
            elif list(self.bucket.bucket.list_blobs(prefix=request_path, max_results=1)):
                print("Fetch file from bucket")
                content = json.loads(self.bucket.download_blob(request_path))
                await self.asave_ckpt_local(path=save_local, content=content)

            else:
                print("Fetch from web")
                content = await self.download_json_content(url=request_path, j=json_file, save=file_name)
            return content
        except Exception as e:
            print("not file found:", e)
        return None

    async def aread_content(self, path, mode="r", j=True):
        print("READ LOCAL CONTENT FROM", path)
        if not path:
            return None
        async with aiofiles.open(path, mode) as file:
            content = await file.read()
        if j:
            return json.loads(content)
        return content

    async def asave_ckpt_local(self, path, content, mode="w"):

        # Ensure the directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Write JSON content asynchronously
        async with aiofiles.open(path, mode=mode) as json_file:
            await json_file.write(json.dumps(content, indent=2))

        print(f"Checkpoint saved successfully at {path}")
"""



    async def aadd_col(self, keys: Dict, table, type_from_val=True):
        table_schema = await self.afetch_table_schema(table_name=table)
        print("Working schema for table")
        cols_to_insert = {}
        for k, v in keys.items():
            if k not in table_schema:
                if type_from_val is True:
                    v = self.get_spanner_type(v)
                cols_to_insert[k] = v

        all_queries = self.add_col_batch_query(
                        table=table,
                        col_data=cols_to_insert
        )
        if all_queries is None:
            return None
        await self.update_db(all_queries)
        #print("All cols added")
"""