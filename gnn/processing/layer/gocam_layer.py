"""
Way mre detailed info for goterms
"""
import asyncio

from gnn.graph_helper.validate_node_layer import id_clasiication
from gnn.processing.model.main import asave_data_checkpoint

import re

from utils.file.flatten_dict import flatten_attributes
from utils.utils import GraphUtils


def extract_last_number(s):
    """ Extracts the last number (hex or integer) from a given string. """
    #  gomodel:6246724f00002072/6246724f00002086 ->  6246724f00002086
    return re.findall(r'[\da-fA-F]+', s)[-1] if re.findall(r'[\da-fA-F]+', s) else None


class GoCam:
    def __init__(self, parent, layer):
        self.g_utils = GraphUtils(table_name=layer)
        self.layer = layer
        self.parent = parent

    async def main(self, data):
        tasks = [self.process_gocam_item(item) for index, item in enumerate(data)]
        await asyncio.gather(*tasks)

    async def process_gocam_item(self, item):
        cam_id = item['id'].split(":")[-1].split("/")[-1]
        item["id"] = cam_id,
        item["type"] = self.layer
        item["parent"] = self.parent
        if cam_id:
            print("Cam id", cam_id)
            await self.g_utils.add_node(
                attrs=item
            )
            await self.process_gocam_edges(item)
        else:
            print("Skipping node", item)

    async def process_gocam_edges(self, data):
        # input: single gocam model element
        for item in data.get('individuals', []):
            item_id = item.get("id", None)

            if item_id:
                item_id = extract_last_number(item_id)
                # print("process item", item_id)
                attrs = item
                attrs["id"] = item_id,
                attrs["type"] = self.layer
                attrs["parent"] = self.parent
                await self.g_utils.add_node(
                    attrs=attrs
                )
                await self.g_utils.add_edge(data.get("id"), item["id"], attrs=dict(rel="individual", parent="gocam"))
                types = ["type", "root-type"]
                for gc_type in types:
                    for i in item[gc_type]:
                        try:
                            filler = i.get("filler", None)
                            if filler is not None:
                                await self.g_utils.add_edge(
                                    item_id,
                                    filler["id"],
                                    attrs=dict(
                                        rel=filler.get("label", "unknown"),
                                        type=f"{i.get('type', 'unknown')}.{filler.get('type', 'unknown')}")
                                )
                                await self.g_utils.add_node(
                                    dict(id=filler["id"],
                                         **flatten_attributes(filler),
                                         type=self.layer
                                         ))
                            else:
                                await self.g_utils.add_edge(
                                    item_id,
                                    i["id"],
                                    attrs=dict(
                                        rel=i.get("label", "unknown").replace(".", "_").replace(":", "_").replace(" ", "_"),
                                        type=i.get("type", "unknown"))
                                )
                        except KeyError as e:
                            print(f"Missing 'type' or 'root-type' in go cam model element: {item}")
                            await asave_data_checkpoint(
                                r"C:\Users\wired\OneDrive\Desktop\Projects\pythonProject\data\fail_item.json",
                                {"object": i, "error": str(e), "main": data})

        for fact in data.get('facts', []):
            subject = fact.get("subject")
            object_ = fact.get("object")
            property_label = fact.get("property-label", fact.get("property"))

            # Ensure subject and object exist in the graph
            await self.g_utils.add_node(
                attrs=dict(
                    id=subject,
                    type=self.layer,
                    parent=self.parent,
                    description="Fact subject node"))
            print(f"Added missing subject node: {subject}")

            await self.g_utils.add_node(
                attrs=dict(
                    id=object_,
                    type='gocam',
                    description="Fact object node"
                ))
            print(f"Added missing object node: {object_}")
            await self.g_utils.add_node(
                dict(id=property_label,
                     type=id_clasiication(property_label))
            )

            await self.g_utils.add_edge(
                subject, object_, attrs=dict(rel=property_label))
            # indirect

            # print(f"Added fact edge: {subject} -> {object_} [{property_label}]")

            # Add annotations as metadata on the edge
            for annotation in fact.get("annotations", []):
                key = annotation.get("key")
                value = annotation.get("value")
                if key and value and not key in ["date", "providedBy", "contributor"]:
                    # Update edge metadata
                    if self.g_utils.G.has_edge(subject, object_):
                        if "annotations" not in self.g_utils.G[subject][object_]:
                            self.g_utils.G[subject][object_]["annotations"] = {}
                        self.g_utils.G[subject][object_]["annotations"][key] = value
