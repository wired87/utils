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
import json
import time

from _google.api_core.exceptions import ResourceExhausted

from typing import List

from utils.file.flatten_dict import flatten_attributes
from utils.utils import GraphUtils


class GeneLayer:
    """
    Some ense are classified as enst -> move after finish
    todo: 49702 got id and name -> let it run get_all_ids(where_not_null_id_col_name=name) again to check if complete

    gene_xref_protein_id -> merge protein_id -> protein
    """

    def __init__(self):
        self.g_utils = GraphUtils(table_name="GENE", upload_to="sp")
        self.layer = "GENE"
        self.parent = ["species"]
        self.testing = False
        self.max_concurrent_tasks = 100
        self.local_id_map_path="gnn/processing/layer/gene_id_map.json"
        self.all_ids = json.load(open(self.local_id_map_path, "r"))["ids_fetched"] #self.g_utils.get_all_ids(self.layer, where_not_null_id_col_name="start")
        print("len local ckpit ids", len(self.all_ids))
        self.bucket_path = "train_data/gene/ensembl_9606.json"
        self.local_path = "data/main_ckpt/gene.json"
        self.testing_item_path = r"C:\Users\wired\OneDrive\Desktop\Projects\bm\data\single\gene.json"



    def handle_xrefs(self, xrefs: List, path: str, pid, src_layer="GENE"):
        for item in xrefs:
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
                self.g_utils.add_edge(
                    pid,
                    trt=item.get("display_id", item.get("primary_id")),
                    attrs=attrs
                )

    def list_str_edges(self, gene: dict, self_id: str, path: str, src_layer="GENE"):
        try:
            for key, value in gene.items():
                new_path = f'{path}.{key}'

                if isinstance(value, list) and all(isinstance(v, (str, int)) for v in value):
                    for entry in value:
                        if entry:
                            attrs = dict(
                                path=new_path,
                                rel=handle_relationship(key),
                                type=key,
                                src_layer=src_layer,
                                trgt_layer=key
                            )
                            self.g_utils.add_edge(
                                src=self_id,
                                trt=entry,
                                attrs=attrs
                            )
        except Exception as e:
            print(f"Error processing list_str_edges: {e}")

    def handle_protein_features(self, protein_features, tid):
        # print("handle protein features")
        for pf in protein_features:
            try:

                pf_name = pf.get("translation_id", pf.get("name"))
                if pf_name:
                    attrs = dict(
                        id=pf_name,
                        type='protein',
                        **{k: v for k, v in flatten_attributes(pf).items() if k != "id"}
                    )
                    # print("NODE handle_protein_features")
                    # pprint.pp(attrs)
                    self.g_utils.add_node(
                        attrs=attrs
                    )
                    attrs = dict(
                        rel='transcribes',
                        src_layer="TRANSLATION",
                        trgt_layer='TRANSLATION',
                        type="transcript"
                    )
                    # print("EDGE handle_protein_features")
                    # pprint.pp(attrs)
                    self.g_utils.add_edge(
                        tid,
                        pf_name,
                        attrs=attrs
                    )
            except Exception as e:
                print(f"Error processing handle_protein_features: {e}")

    def get_ens_layer(self, key):
        return "gene" if "ENSG" in key else "protein"

    def handle_exons(self, exons: List, pid: str, path: str, parent: str = "GENE"):
        if exons:
            try:
                for exon in exons:
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
                        self.g_utils.add_node(
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
                        self.g_utils.add_edge(
                            pid,
                            exon_id,
                            attrs=attrs,
                        )
                    else:
                        print("Exon id missing")
            except Exception as e:
                print(f"Error processing handle_exons: {e}")

    def transcript_processor(self, trans_item, trans_layer, gene_id, item, path):
        try:
            transcript_id = trans_item.get("id")

            attrs = dict(
                **flatten_attributes(trans_item),
                type=trans_layer,
                parent=["gene"],
            )
            # print("NODE handle_transcript")
            # pprint.pp(attrs)
            self.g_utils.add_node(
                attrs=attrs
            )
            #
            attrs = dict(
                rel="transcribes",
                src_layer="GENE",
                trgt_layer=trans_layer,
                type="transcript"
            )
            # print("EDGE handle_transcript")
            # pprint.pp(attrs)
            self.g_utils.add_edge(
                gene_id,
                transcript_id,
                attrs=attrs
            )
            #
            exons = item.get("exons", None)

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

            translations = trans_item.get("translations", [])
            if translations:
                layer = "TRANSLATION"
                for item in translations:
                    self.translation_processing(item, transcript_id, path, layer, trans_item)
        except Exception as e:
            print(f"Error processing transcript_processor: {e}")

    def handle_transcript(self, item, gene_id, path):
        transcripts = item.get("transcripts", None)
        if transcripts:
            trans_layer = 'transcript'
            for trans_item in transcripts:
                self.transcript_processor(trans_item, trans_layer, gene_id, item, path)

    def translation_processing(self, item, transcript_id, path, layer, trans_item):
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
        self.g_utils.add_node(
            attrs=attrs
        )

        # print("EDGE translations")
        # pprint.pp(attrs)
        self.g_utils.add_edge(
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

    def go_list_processor(self, go, src_layer, item_id):
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
                self.g_utils.add_edge(
                    item_id,
                    term,
                    attrs=attrs
                )

            parent: List[str] = go.get("parents", None)  # [Go:xxx,...
            if parent:
                for p in parent:
                    self.g_utils.add_edge(
                        p,
                        term,
                        attrs=dict(
                            rel="parent",
                            src_layer="go",
                            trgt_layer="go",
                            type="go"
                        ))
        except Exception as e:
            print(f"Error processing go: {e}")

    def handle_goterm(self, item, src_layer="GENE"):
        """
        Todo currently just created edges (goterm nodes extra) -> check if complete
        """
        # print("Goterm")
        item_id = item.get("id")
        go_list = item.get("GO", [])
        if go_list and len(go_list) > 0:
            for go in go_list:
                self.go_list_processor(go, src_layer, item_id)

    def handle_gene_edges(self, gene, gene_id, base_path="GENE"):

        self.list_str_edges(gene, gene_id, path=rf"{base_path}"),
        self.handle_xrefs(
            xrefs=gene.get('xrefs', []),
            path=rf"{base_path}.xrefs",
            pid=gene_id
        ),
        self.handle_transcript(gene, gene_id, base_path),
        self.handle_goterm(gene)

    def process_single_gene(self, gene):
        try:

            gene_id = gene['id']
            # print(gene_id)

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
            # print("GENE set:")
            # pprint.pp(item)
            self.g_utils.add_node(attrs=item)
            self.handle_gene_edges(gene, gene_id)
            print("Finished", gene_id)
            gene = None
        except ResourceExhausted as e:
            print("Resource exhaused. Sleep 60sec. e:", e)
            time.sleep(60)
            self.process_single_gene(gene)
            # await sync_to_async(send_email)(e, "ratelimit error")
        except Exception as e:
            print("Unexpected error occurred", e)
            time.sleep(60)
            self.process_single_gene(gene)
            # await sync_to_async(send_email)(e, "unexpected error")

    def main(self, data=None):
        print("Process Gene")
        if not data:
            data = asyncio.run(self.g_utils.load_content(  ############# args here
                local_path=self.local_path,
                bucket_path=self.bucket_path,
                layer=self.layer,
                test_chunk=None,
                testing=None
            ))
        if self.testing:
            self.process_single_gene(data)
            return

        data = self.g_utils.data_preprocessor(data, self.all_ids)

        print("Creating tasks")
        i = 0
        """batch_chunks = []
        for i in range(0, len(data), self.max_concurrent_tasks):
            chunk = data[i:i + self.max_concurrent_tasks]
            batch_chunks.append(chunk)
            for item in data[i:i + self.max_concurrent_tasks]:
                item = None"""

        for i in range(0, len(data), self.max_concurrent_tasks):
            i += 1
            print("Start batch", i)
            batch_chunk = data[i:i + self.max_concurrent_tasks]
            for gene in batch_chunk:
                self.process_single_gene(gene)
                self.all_ids.append(gene.get("id"))

            asyncio.run(self.g_utils.abatch_commit())
            self.update_id_map()
        print("Finished")

    def update_id_map(self):
        with open(self.local_id_map_path, "w") as f:
            json.dump({"ids_fetched": self.all_ids}, f)

def handle_relationship(key):
    return "xref"


if __name__ == "__main__":
    gene_layer = GeneLayer()
    gene_layer.main()
