import asyncio

from utils.utils import GraphUtils

"""
self.pop_items = [
            "species",
            "orthologousEvent",
            "literatureReference",
            "compartment",
            "output",
            "input",
            "goBiologicalProcess",
            "precedingEvent",
        ]
"""
#################################

class ReactomeLayer:
    """
    Reactome API -> BQ
    Dataflow
    top level hsa ->
    """

    def __init__(self):
        self.layer = "RHSA"
        self.g_utils = GraphUtils(table_name=self.layer)

        self.parent = ["GENE", "PATHWAY"]
        """
        todo link edges all times to new and old reactome ids
        """

        self.top_lvl_url = "https://reactome.org/ContentService/data/pathways/top/9606"

    def anchestors_url(self, st_id):
        return f"https://reactome.org/ContentService/data/event/{st_id}/ancestors"

    def participant_url(self, st_id):
        return f"https://reactome.org/ContentService/data/participants/{st_id.split('-')[-1]}"

    def details_url(self, st_id):
        return f"https://reactome.org/ContentService/data/query/enhanced/{st_id}"

    def pathway_map_url(self, stId):
        return rf"https://reactome.org/ContentService/data/pathway/{stId}/containedEvents"


    async def main2(self, parent_id=None):
        i = 0
        top_lvl_pathways = await self.g_utils.utils.aget(self.top_lvl_url if parent_id is None else self.pathway_map_url(parent_id))
        print("top_lvl_pathways", top_lvl_pathways)
        unpacked_pathways = top_lvl_pathways[0]
        if isinstance(unpacked_pathways, list):
            for idx, top_path in enumerate(unpacked_pathways):
                print("unpacked_pathways", unpacked_pathways)

                item_id = top_path.get("stId")
                details = await self.g_utils.utils.aget(self.details_url(item_id))

                await self.g_utils.aadd_node(
                    attrs=dict(
                        **self.extract_default_node_attrs(details, item_id=item_id),
                        figure_urls=[item.get("figure", {}).get("url") for item in details.get("figure", [])],
                        figure_db_ids=[item.get("figure", {}).get("dbId") for item in details.get("figure", [])],
                        summation_texts=[item.get("texts", "") for item in details.get("summation")]
                    )
                )

                if parent_id:
                    await self.g_utils.aadd_edge(
                        src=parent_id,
                        trt=item_id,
                        attrs=dict(
                            src_layer=self.layer,
                            trgt_layer=self.layer,
                            rel="sub_pathway",
                        )
                    )

                await self.g_utils.aadd_edge(
                    src=top_path.get("stId"),
                    trt=9606,
                    attrs=dict(
                        src_layer="RHSA",
                        trgt_layer="SPECIES",
                        rel="organism_specific"
                    )
                )
                await asyncio.gather(*[
                    self.handle_ancestors(item_id),  #
                    self.hanle_orthologs(details, item_id=item_id),
                    self.handle_events(details, parent_item_id=item_id),
                    self.literature_handler(details, item_id=item_id),
                    self.inp_handler(details, item_id),
                    self.out_handler(details, item_id),
                ])
                # go edge
                await self.g_utils.add_edge(
                    src=top_path.get("stId"),
                    trt=f"{details.get('goBiologicalProcess', {}).get('databaseName', '')}:{details.get('goBiologicalProcess', {}).get('accession', '')}",
                    attrs=dict(
                        src_layer="RHSA",
                        trgt_layer="SPECIES",
                        rel=details.get('goBiologicalProcess', {}).get('GO_BiologicalProcess', '').lower()
                    )
                )
                ######### map the pathways
                await self.main2(top_path.get("stId"))



    async def inp_handler(self, details, item_id):
        inputs = details.get("input", [])

        async def input_processor(inp):
            if isinstance(inp, dict):
                inp_id = inp.get("stId")
                if inp_id:
                    await self.g_utils.add_node(
                        attrs=self.extract_default_node_attrs(inp, inp_id)
                    )

                    await self.g_utils.add_edge(
                        item_id,
                        inp_id,
                        attrs=dict(
                            rel="gets_input",
                            type="input",
                            src_layer=self.layer,
                            trgt_layer=self.layer
                        )
                    )
        await asyncio.gather(*[input_processor(item) for item in inputs if len(inputs)])


    async def out_handler(self, item, item_id):
        output = item.get("output", [])

        async def out_processor(out):
            if isinstance(out, dict):
                out_id = out.get("stId")

                await self.g_utils.add_node(
                    attrs=self.extract_default_node_attrs(
                        item=out,
                        item_id=out_id
                    )
                )
                await self.g_utils.add_edge(
                    item_id,
                    out_id,
                    attrs=dict(
                        rel=f"outputs",
                        type="output",
                        src_layer=self.layer,
                        trgt_layer=self.layer
                    )
                )

        await asyncio.gather(*[out_processor(out) for out in output if len(output)])



    async def handle_ancestors(self, item_id):
        ancestors = await self.g_utils.utils.aget(self.anchestors_url(item_id))

        async def ancestor_processor(ancestor):
            anc_id = ancestor.get("stId")
            if anc_id == item_id:
                return
            await self.g_utils.add_edge(
                item_id,
                anc_id,
                attrs=dict(
                    rel="ancestor",
                    src_layer=self.layer,
                    trgt_layer=self.layer if anc_id.startswith("R-HSA") else f"{anc_id.split('-')[0]}{anc_id.split('-')[1]}"
                )
            )
        await asyncio.gather(*[ancestor_processor(ancestor) for ancestor in ancestors if ancestors])


    async def literature_handler(self, item, item_id=None):
        lit_ref = item.get("literatureReference", [])
        if lit_ref and len(lit_ref):
            async def literature_processor(item):
                for l_ref in lit_ref:
                    l_id = l_ref.get("dbId", )
                    await self.g_utils.add_node(
                        attrs=dict(
                            id=item.get("dbId"),
                            display_name=l_ref.get("displayName"),
                            pubmed_id=l_ref.get("pubMedIdentifier", None),
                            journal=l_ref.get("journal"),
                            url=l_ref.get("url"),
                    ))
                    await self.g_utils.add_edge(
                        item_id,
                        l_id,
                        attrs=dict(
                            rel=l_ref.get("className"),
                            src_layer=self.layer,
                            trgt_layer=l_ref.get("className")
                        )
                    )
            await asyncio.gather(*[literature_processor(event) for event in lit_ref])


    async def handle_events(self, item, parent_item_id):
        events = item.get("hasEvent", [])

        async def event_processor(item):
            if item and isinstance(item, dict):
                await self.g_utils.add_node(
                    attrs=self.extract_default_node_attrs(item, item_id=None)
                )
                await self.g_utils.add_edge(
                    parent_item_id,
                    item.get("stId"),
                    attrs=dict(
                        rel="has_event"
                    )
                )
        await asyncio.gather(*[event_processor(event) for event in events])




    async def hanle_orthologs(self, details, item_id):
        orth_event = details.get("orthologousEvent", [])

        async def ortho_item(item):
            if item and not isinstance(item, int or str):
                await self.g_utils.add_node(
                    attrs=self.extract_default_node_attrs(item, item_id=None)
                )
                await self.g_utils.add_edge(
                    item_id,
                    item.get("stId"),
                    attrs=dict(
                        rel="occurrence_in"
                    )
                )
        await asyncio.gather(*[ortho_item(event) for event in orth_event])




    async def handle_preceding_event(self, details, item_id):
        orth_event = details.get("orthologousEvent", [])

        async def ortho_item(item):
            preceding_event = details.get("precedingEvent", [])
            for p_event in preceding_event:
                p_id = p_event.get("stId")
                class_n = p_event.get("className", )
                if class_n:
                    p_event.pop("className")
                await self.g_utils.add_edge(
                    p_id,
                    item_id,
                    attrs=dict(rel='preceding_event',
                               type=class_n,
                               src_layer="RHSA",
                               trgt_layer=self.layer
                               ),
                )
        await asyncio.gather(*[ortho_item(event) for event in orth_event])





    def extract_default_node_attrs(self, item, item_id=None):
        node_attrs = dict(
            id=item_id if item_id is not None else item.get("stId"),
            name=item.get("name"),
            isInDisease=item.get("isInDisease"),
            isInferred=item.get("isInferred"),
            className=item.get("className"),
            species_name=item.get("speciesName"),
        )
        display_name = item.get("displayName")
        node_attrs["name"].append(display_name)
        return node_attrs



if __name__ == "__main__":
    # Paths to data files+
    r = ReactomeLayer()
    asyncio.run(r.main2())
    graph_dump_path = r"C:\Users\wired\OneDrive\Desktop\Projects\pythonProject\data\raw\reactome\reactome.graphdb.dump"

