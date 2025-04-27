


"""
edges



todo
uniparc
- transcript
GO:
- link as edges
- batches
GENCODE, RefSeq,
UNBEDINGS AUF MOLECULARER EBENE VERLINKEN -> NICHT AUF DATENBANK EBENE -> dem modell ist es egal wo oder wie daten entstanden sind










ENSG → Gene

ENST → Transcript

ENSP → Protein

ENSR → Regulatory Feature

ENSMUSG, ENSMUST, etc. → Mouse-specific equivalents

"""

import asyncio


from google.api_core.exceptions import ResourceExhausted

from typing import List

from utils.file.flatten_dict import flatten_attributes
from utils.utils import GraphUtils
from tqdm.asyncio import tqdm_asyncio  # Async-friendly progress bar

class GeneLayer:
    """
    Some ense are classified as enst -> move after finish
    """

    def __init__(self):
        self.g_utils = GraphUtils(table_name="GENE", upload_to="sp")
        self.layer = "GENE"
        self.parent=["species"]
        self.max_concurrent_tasks = 10
        self.testing = False
        self.all_ids = self.g_utils.get_all_ids(self.layer, where_not_null_id_col_name="start")
        self.bucket_path= "train_data/gene/ensembl_9606.json"
        self.local_path= "data/main_ckpt/gene.json"
        self.testing_item_path = r"/data/single/gene.json"
        #print("len self.all_ids", len(self.all_ids))

    async def handle_xrefs(self, xrefs: List, path: str, pid, src_layer="GENE"):
        async def xref_processor(item):
            dname = item.get("db_display_name")
            if dname:
                attrs = dict(
                    path=path,
                    **item,
                    rel='xref',
                    src_layer=src_layer,
                    trgt_layer=dname,
                )
                attrs["type"] = "xref"
                await self.g_utils.add_edge(
                    pid,
                    trt=item.get("display_id", item.get("primary_id")),
                    attrs=attrs
                )
        await asyncio.gather(*[xref_processor(item) for item in xrefs])
            



    async def list_str_edges(self, gene: dict, self_id: str, path: str, src_layer="GENE"):
        try:
            async def list_processor(key, value):

                async def list_entry_processor(entry):
                    if entry:
                        attrs = dict(
                            path=new_path,
                            rel=handle_relationship(key),
                            type=key,
                            src_layer=src_layer,
                            trgt_layer=key
                        )
                        # print("EDGE list_str_edges")
                        # pprint.pp(attrs)
                        await self.g_utils.add_edge(
                            self_id,
                            entry,
                            attrs=attrs,
                        )

                new_path = f'{path}.{key}'
                # print("key", key)
                if isinstance(value, List) and all(isinstance(v, (str, int)) for v in value):  #
                    await asyncio.gather(*[list_entry_processor(entry) for entry in value])
            await asyncio.gather(*[list_processor(key, value) for key, value in gene.items()])
        except Exception as e:
            print(f"Error processing list_str_edges: {e}")
            

    async def handle_protein_features(self, protein_features, tid):
        # print("handle protein features")
        try:
            async def protein_feature_processor(pf):
                pf_name = pf.get("translation_id", pf.get("name"))
                if pf_name:
                    attrs = dict(
                        id=pf_name,
                        type='protein',
                        **{k: v for k, v in flatten_attributes(pf).items() if k != "id"}
                    )
                    # print("NODE handle_protein_features")
                    # pprint.pp(attrs)
                    await self.g_utils.add_node(
                        attrs=attrs
                    )
                    #
                    attrs = dict(
                        rel='transcribes',
                        src_layer="TRANSLATION",
                        trgt_layer='TRANSLATION',
                        type="transcript"
                    )
                    # print("EDGE handle_protein_features")
                    # pprint.pp(attrs)
                    await self.g_utils.add_edge(
                        tid,
                        pf_name,
                        attrs=attrs
                    )

            await asyncio.gather(*[protein_feature_processor(pf) for pf in protein_features])
        except Exception as e:
            print(f"Error processing handle_protein_features: {e}")

    def get_ens_layer(self, key):
        return "gene" if "ENSG" in key else "protein"

    async def handle_exons(self, exons: List, pid: str, path: str, parent: str = "GENE"):
        if exons:
            try:
                async def exon_processor(exon):
                    exon_id = exon.get("id")
                    if exon_id:
                        attrs = dict(
                            id=exon_id,
                            type="exon",
                            parent=[parent],
                            child=[],
                            **{k: v for k, v in flatten_attributes(exon).items() if k != "id"}
                        )
                        # print("NODE handle_exons")
                        # pprint.pp(attrs)
                        await self.g_utils.add_node(
                            attrs=attrs
                        )
                        #
                        attrs = dict(
                            rel='transcript',
                            path=path,
                            src_layer=parent,
                            trgt_layer="exon",
                            type="transcript"
                        )
                        attrs["type"] = "xref"
                        # print("EDGE handle_exons")
                        # pprint.pp(attrs)
                        await self.g_utils.add_edge(
                            pid,
                            exon_id,
                            attrs=attrs,
                        )
                    else:
                        print("Exon id missing")
                await asyncio.gather(*[exon_processor(exon) for exon in exons])
            except Exception as e:
                print(f"Error processing handle_exons: {e}")
        
            
    async def transcript_processor(self, trans_item, trans_layer, gene_id, item, path):
        try:
            transcript_id = trans_item.get("id")

            attrs = dict(
                **flatten_attributes(trans_item),
                type=trans_layer,
                parent=["gene"],
            )
            # print("NODE handle_transcript")
            # pprint.pp(attrs)
            await self.g_utils.add_node(
                attrs=attrs
            )
            #
            attrs = dict(
                rel="transcribes",
                src_layer="",
                trgt_layer=trans_layer,
                type="transcript"
            )
            # print("EDGE handle_transcript")
            # pprint.pp(attrs)
            await self.g_utils.add_edge(
                gene_id,
                transcript_id,
                attrs=attrs
            )
            #
            exons = item.get("exons", None)

            await asyncio.gather(
                *[
                    self.handle_exons(
                        exons=exons,
                        pid=transcript_id,
                        path=f'{path}.transcript.exon',
                        parent=trans_layer
                    ),
                    self.handle_goterm(trans_item, src_layer=trans_layer),
                    self.list_str_edges(
                        item,
                        self_id=transcript_id,
                        path=f'{path}.transcript',
                        src_layer="transcript"
                    ),
                    self.handle_xrefs(
                        xrefs=item.get('xrefs', []),
                        path=f"{path}.transcript.xref",
                        pid=transcript_id,
                        src_layer=trans_layer
                    )

                ])
            translations = trans_item.get("translations", [])
            if translations:
                layer = "TRANSLATION"
                await asyncio.gather(
                    *[self.translation_processing(item, transcript_id, path, layer, trans_item) for item in translations])
        except Exception as e:
            print(f"Error processing transcript_processor: {e}")


    async def handle_transcript(self, item, gene_id, path):
        transcripts = item.get("transcripts", None)
        if transcripts:
            trans_layer = 'transcript'
            await asyncio.gather(
                *[self.transcript_processor(trans_item, trans_layer, gene_id, item, path) for trans_item in transcripts]
            )


    async def translation_processing(self, item, transcript_id, path, layer, trans_item):
        translation_id = item.get('id')
        exons = item.get("exons", None)
        attrs = dict(
            path=f'{path}.transcript.translation',
            **item,
            parent=["gene", "transcript"],
            type=layer,
        )
        # print("NODE translations")
        # pprint.pp(attrs)
        await self.g_utils.add_node(
            attrs=attrs
        )

        # print("EDGE translations")
        # pprint.pp(attrs)
        await self.g_utils.add_edge(
            transcript_id,
            translation_id,
            attrs=dict(
                rel="translates",
                src_layer="transcript",
                trgt_layer=layer,
                type="translation_relation"
            )
        )

        protein_features = item.get("protein_features", [])
        await asyncio.gather(
            *[
                self.handle_goterm(trans_item, src_layer=layer),
                self.handle_protein_features(protein_features, translation_id),
                self.list_str_edges(
                    gene=item,
                    self_id=transcript_id,
                    path=f"{path}.transcript.translation",
                ),
                self.handle_xrefs(
                    xrefs=item.get('xrefs', []),
                    path=f"{path}.transcript.translation.xref",
                    pid=translation_id,
                    src_layer=layer
                ),
                self.handle_exons(
                    exons=exons,
                    pid=transcript_id,
                    path=f'{path}.transcript.translation.exon',
                    parent=layer
                )

            ])

    async def go_list_processor(self, go, src_layer, item_id):
        try:
            term = go.get("term", None)
            evidence = go.get("evidence", None)
            if term:
                attrs = dict(
                    rel="involved_in",
                    type="go",
                    src_layer=src_layer,
                    trgt_layer="go",
                    info=evidence[0] if evidence and len(evidence) > 0 else "go"
                )
                # print("EDGE handle_goterm")
                # pprint.pp(attrs)
                await self.g_utils.add_edge(
                    item_id,
                    term,
                    attrs=attrs
                )

            parent: List[str] = go.get("parents", None)  # [Go:xxx,...
            if parent:
                await asyncio.gather(*[self.g_utils.add_edge(
                    p,
                    term,
                    attrs=dict(
                        rel="parent",
                        src_layer="go",
                        trgt_layer="go",
                        type="go"
                    )) for p in parent])
        except Exception as e:
            print(f"Error processing go: {e}")


    async def handle_goterm(self, item, src_layer="GENE"):
        """
        Todo currently just created edges (goterm nodes extra) -> check if complete
        """
        # print("Goterm")
        item_id = item.get("id")
        go_list = item.get("GO", [])
        if go_list and len(go_list) > 0:
            await asyncio.gather(*[self.go_list_processor(go, src_layer, item_id) for go in go_list])




    async def handle_gene_edges(self, gene, gene_id, base_path="GENE"):
        await asyncio.gather(
            *[
                self.list_str_edges(gene, gene_id, path=rf"{base_path}"),
                self.handle_xrefs(
                    xrefs=gene.get('xrefs', []),
                    path=rf"{base_path}.xrefs",
                    pid=gene_id
                ),
                self.handle_transcript(gene, gene_id, base_path),
                self.handle_goterm(gene)
            ])


    async def process_single_gene(self, gene):
        try:

            gene_id = gene['id']
            #print(gene_id)

            # print("Working id", gene_id)
            item = dict(
                name=gene.get("name", None),
                description=gene.get("description"),
                biotype=gene.get("biotype"),
                start=gene.get("start"),
                end=gene.get("end"),
                strand=gene.get("strand"),
                coord_system=gene.get("coord_system"),
                type=self.layer,
                id=gene_id,
                parent=self.parent
            )
            #print("GENE set:")
            #pprint.pp(item)
            await self.g_utils.add_node(attrs=item)
            await self.handle_gene_edges(gene, gene_id)
            print("Finished", gene_id)
            gene = None
        except ResourceExhausted as e:
            print("Resource exhaused. Sleep 60sec. e:", e)
            await asyncio.sleep(60)
            await self.process_single_gene(gene)
            # await sync_to_async(send_email)(e, "ratelimit error")
        except Exception as e:
            print("Unexpected error occurred", e)
            await asyncio.sleep(60)
            await self.process_single_gene(gene)
            # await sync_to_async(send_email)(e, "unexpected error")



    async def main(self, data=None):
        await self.g_utils.acreate_session()
        print("Process Gene")
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        if not data:
            data = await self.g_utils.load_content(############# args here
                local_path=self.local_path,
                bucket_path=self.bucket_path,
                layer=self.layer,
                test_chunk=None,
                testing=None
            )
        if self.testing:
            await self.process_single_gene(data)
            return

        async def sem_task(task):
            async with semaphore:
                return await task

        data = self.g_utils.data_preprocessor(data, self.all_ids)

        print("Creating tasks")
        for i in range(0, len(data), self.max_concurrent_tasks):
            batch_chunk = data[i:i + self.max_concurrent_tasks]
            tasks = [sem_task(self.process_single_gene(gene)) for index, gene in enumerate(batch_chunk)]
            await tqdm_asyncio.gather(*tasks, desc=f"Processing {self.layer}", unit=self.layer)
            await self.g_utils.batch_commit()
        print("Finished")


def handle_relationship(key):
    return "xref"


if __name__ == "__main__":
    gene_layer = GeneLayer()
    asyncio.run(gene_layer.main())


