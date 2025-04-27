import asyncio
import os

from utils.utils import GraphUtils

class CellTranscriptomeLayer:

    def __init__(self, file_name=None, upload_to="sp"):
        self.layer = "TRANSCRIPTOME"
        self.upload_to = upload_to
        self.g_utils = GraphUtils(table_name=self.layer, upload_to=upload_to)
        self.parent = ["cell"]

        self.all_ids = self.g_utils.get_ids()
        self.file_name = file_name or "thalamic_6k_9606.json"
        self.local_path = rf"C:\Users\wired\OneDrive\Desktop\Projects\bm\data\main_ckpt\{self.layer}.json" if os.name == "nt" else f"data/main_ckpt/{self.layer}.json"
        self.bucket_path = f"train_data/cell/transcriptomes/{self.file_name}"
        self.batch_size=10
        self.xref_fields = {
            "EFO": "assay_ontology_term_id",
            "PATO": ["sex_ontology_term_id", "disease_ontology_term_id"],
            "HSAPDV": "development_stage_ontology_term_id",
            "CL": "cell_type_ontology_term_id",
            "UBERON": "tissue_ontology_term_id",
            "DONOR": "donor_id",
            "CELL_TYPE": "cell_type",
            "HANCESTRO": "self_reported_ethnicity_ontology_term_id",
            "NCBITAXON": "organism_ontology_term_id",
        }
        self.multiprocess_batch_size = 3

    def gene_edges(self, item, cell_id):
        try:
            for key, value in item.get("gene_expression", {}).items():
                # key=ens id
                self.g_utils.add_node(
                    attrs=dict(
                        id=key,
                        type="gene",
                        parent=["species"]
                    )
                )

                attrs = dict(
                    rel="building_block",
                    type="cell_development",
                    expression=value,
                    src_layer="gene",
                    trgt_layer=self.layer
                )
                self.g_utils.add_edge(
                    key,
                    cell_id,
                    attrs=attrs,
                )
        except Exception as e:
            print(f"Error gene_edges: error: {e}")

    def handle_cell_edges(self, item, cell_identifier):
        self.gene_edges(item, cell_id=cell_identifier)
        try:
            for db, xref in self.xref_fields.items():
                if isinstance(xref, str):
                    xref = [xref]
                for i in xref:
                    xref_id = item.get(i)
                    if xref_id:
                        self.g_utils.add_node(
                            attrs=dict(
                                id=xref_id,
                                type=db,
                                parent=[""]
                            )
                        )
                        self.g_utils.add_edge(
                            cell_identifier,
                            xref_id,
                            attrs=dict(
                                rel='xref' if db != "CELL_TYPE" else "family",
                                src_layer=self.layer,
                                type=f"{self.layer}_{db}",
                                trgt_layer=db,
                            )
                        )
        except Exception as e:
            print(f"Error handle_cell_edges: error: {e}")
    def process_batch(self, chunk):
        for index, entry in enumerate(chunk):
            self._process(entry, index)
        asyncio.run(self.g_utils.abatch_commit())

    def main(self, data=None):
        print("Start workibg on cell")

        asyncio.run(self.g_utils.acheck_add_table(self.layer, ttype="node"))

        if not data:
            data = asyncio.run(self.g_utils.load_content(
                local_path=self.local_path,
                bucket_path=self.bucket_path,
                layer=self.layer,
                test_chunk=None,
                testing=None
            ))

        data = self.g_utils.data_preprocessor(data, self.all_ids, key="name_of_cell")

        """data = [data[i:i + self.batch_size] for i in range(0, len(data), self.batch_size)]

        for i in range(0, len(data), self.multiprocess_batch_size):
            chunks = data[i:i + self.multiprocess_batch_size]
            with multiprocessing.Pool(processes=self.multiprocess_batch_size) as pool:
                pool.map(self.process_batch, chunks)"""

        for i in range(0, len(data), self.batch_size):
            batch_chunk = data[i:i + self.batch_size]
            for index, entry in enumerate(batch_chunk):
                self._process(entry, index)
            asyncio.run(self.g_utils.abatch_commit())
        print("Process finished")

    def xref_processor(self, k, item):
        try:
            v = self.xref_fields[k]
            if isinstance(v, str):
                item.get("metadata", {}).pop(v, None)
            elif isinstance(v, list):
                for subkey in v:
                    item.get("metadata", {}).pop(subkey, None)
        except Exception as e:
            print(f"Error xref_processor: error: {e}")

    def _process(self, item, i):
        """
        name cell -> gene
        """
        try:
            identifier = item.get("name_of_cell")
            if identifier in self.all_ids:
                print(f"Cell id {identifier}:{i} alreay exists")
                return
            xref_fields = {
                "gene_expression": item.get("gene_expression", {})
            }
            xref_fields.update({k: item.get("metadata", {}).get(k) for k in self.xref_fields.keys()})

            for k in self.xref_fields:
                self.xref_processor(k, item)

            if identifier:
                # print("Working cell", identifier)
                self.g_utils.add_node(
                    attrs=dict(
                        id=identifier,
                        **item.get("metadata", {}),
                        type=self.layer,
                        parent=self.parent,
                    ))
                self.handle_cell_edges(xref_fields, identifier)
                item = None
                print("Finished", identifier)
        except Exception as e:
            print("Error processing:", e)


if __name__ == "__main__":
    cl = CellTranscriptomeLayer()
    cl.main()