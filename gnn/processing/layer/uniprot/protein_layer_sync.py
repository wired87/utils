"""
Run 1 issues:
- rm source: @evidence
- removed path attr edges
- added submissionNames for proteinDescription
- fixed feature
->  strange connection formed by self.find_node_by_attribute
"""
import asyncio
import json
from asyncio import Semaphore

from utils.file.flatten_dict import flatten_attributes
from ggoogle.storage.storage import GBucket
from utils.utils import GraphUtils, Utils

class ProteinLayer:

    def __init__(self, parent=None, layer=None, path=None):
        self.g_utils = GraphUtils(table_name=layer, upload_to="sp")
        self.layer = layer or "PROTEIN"
        self.parent = parent or ["GENE", "MOLECULE", "RNA"]
        self.max_concurrent_tasks = 100
        self.local_id_map_path = "gnn/processing/layer/uniprot/protein_id_map.json"

        self.all_ids = json.load(open(self.local_id_map_path, "r"))["ids_fetched"]
        print(f"Local {self.layer} ids", len(self.all_ids))

        self.semaphore = Semaphore(self.max_concurrent_tasks)
        self.ens_id_name = None
        self.bucket = GBucket("bestbrain")
        self.utils = Utils()
        self.bucket_path="train_data/protein/uniprot_9606.json"
        self.local_path = "data/main_ckpt/protein.json"


    """async def get_data(self):
        print("Get Data")
        data = await self.g_utils.load_content(
            local_path=self.local_path,
            bucket_path=self.bucket_path,
            layer=self.layer,
            test_chunk=None,
            testing=None
        )
        print("Fetched data", type(data))
        if not data:
            data = await self.utils.get_process(self.bucket_path)
            print("Fetche data second try:", type(data))

        data = self.g_utils.data_preprocessor(data, self.all_ids)

        if isinstance(data, list):
            print(f"Extracted {len(data)} items")
        else:
            print("unusual format", type(data))
        return data"""


    def build_graph(self):
        self.ens_id_name = self.g_utils.get_gene_id_name()
        if self.ens_id_name is not None and len(self.ens_id_name):

            data = asyncio.run(self.g_utils.load_content(  ############# args here
                local_path=self.local_path,
                bucket_path=self.bucket_path,
                layer=self.layer,
                test_chunk=None,
                testing=None
            ))
            i=0
            # Directly gather the async tasks
            for i in range(0, len(data), self.max_concurrent_tasks):
                print("Batch", i)
                i += 1
                batch_chunk = data[i:i + self.max_concurrent_tasks]
                for index, entry in enumerate(batch_chunk):
                    self._process_entry(entry, index)
                asyncio.run(self.g_utils.batch_commit())
                self.update_id_map()


    def _process_entry(self, entry, index):
        protein_id = entry.get('primaryAccession') or entry.get("uniProtkbId", "").split("_")[0]
        self._add_edges(entry, protein_id)
        attrs = dict(
            id=protein_id,
            type=self.layer,
            parent=self.parent,
            **flatten_attributes(entry)
        )
        self.g_utils.add_node(
            attrs=attrs
        )

    def _add_edges(self, item, protein_id):
        if not protein_id:
            return
        self.proteinDescription(item),
        self._add_protein_organism_edge(protein_id, item)
        self._add_protein_gene_edges(protein_id, item)
        self._add_protein_comment_edges(protein_id, item)
        self._add_protein_feature_edges(protein_id, item)
        self._add_protein_keyword_edges(protein_id, item)
        self._add_protein_reference_edges(protein_id, item)
        self._add_protein_cross_reference_edges(protein_id, item)


    def _add_protein_organism_edge(self, protein_id, entry):
        organism = entry.get("organism")
        if organism:
            taxon_id = organism.get("taxonId")
            if taxon_id:
                self.g_utils.add_edge(
                    protein_id,
                    taxon_id,
                    attrs=dict(
                        rel="active_in",
                        type="species",
                        src_layer = "protein",
                        trgt_layer = "species",))

    async def gather_gene_id_from_synonym(self, item):
        synonyms = item.get("synonyms", None)
        if synonyms:
            for syn in synonyms:
                gene_id = self.g_utils.find_node_by_attribute(attr_name="name", attr_value=syn.get("value"))
                if gene_id:
                    return gene_id
        return None

    def _add_protein_gene_edges(self, protein_id, entry):
        def gene_id_from_name(value):
            return next((k for k, v in self.ens_id_name.items() if v == value), None)

        genes = entry.get("genes")
        if genes:
            for gene in genes:
                gene_name = gene.get("geneName", {})
                gene_value = gene_name.get("value")
                print("Gene value", gene_value)
                gene_id = gene_id_from_name(gene_value)
                if gene_id:
                    self.g_utils.add_edge(
                        src=protein_id,
                        trt=gene_id,
                        attrs=dict(
                            rel="coded_by",
                            type="gene",
                            src_layer="protein",
                            trgt_layer="gene",
                    ))



    def handle_eco(self, item, item_id=None, parent=None):
        evidences = item.get("evidences", [])
        for k, evidence in enumerate(evidences):
            evidence_id = evidence.get("evidenceCode", None)
            db_source = evidence.get("source", None)
            db_id = evidence.get("id", None)
            if db_id and db_source and evidence_id:
                self.g_utils.add_node(
                    attrs=dict(
                        id=evidence_id,
                        **{k: v for k, v in evidence.items() if k != "id"},
                        type="eco",
                        parent=[]
                   ))
                self.g_utils.add_edge(
                    src=db_id,
                    trt=evidence_id,
                    attrs=dict(
                        rel="has_evidence",
                        src_layer=db_source,
                        trgt_layer="eco",
                    )
                )

            if item_id and evidence_id and parent:
                self.g_utils.add_edge(
                    src=item_id,
                    trt=evidence_id,
                    attrs=dict(
                        rel="has_evidence",
                        src_layer = "protein",
                        trgt_layer = "eco",

                    )
                )

    def handle_texts(self, item, pid):
        texts = item.get("texts", [])
        for j, text in enumerate(texts):
            self.handle_eco(text, pid)

    def proteinDescription(self, item):
        p_des = item.get("proteinDescription", {})
        rn = p_des.get("recommendedName", None)
        if rn:
            fn = rn.get("fullName", {})
            self.handle_eco(fn, fn.get("value", "unknown"))
        sn = p_des.get("submissionNames", None)

        if sn:
            if isinstance(sn, list):
                for s in sn:
                    fn = s.get("fullName", {})
                    self.handle_eco(fn, fn.get("value", "unknown"))
            elif isinstance(sn, dict):
                fn = sn.get("fullName", {})
                self.handle_eco(fn, fn.get("value", "unknown"))

    def handle_subcl_fields(self, protein_id, item, key):
        # print("Working", key)
        location = item.get(key, {})
        if location:
            location_id = location.get("id", None)
            if location_id:
                self.g_utils.add_node(
                    attrs=dict(
                        id=location_id,
                        type=key,
                        **{k: v for k, v in location.items() if k != "id"},
                    ))

                self.g_utils.add_edge(
                    protein_id,
                    location_id,
                    attrs=dict(
                        src_layer="protein",
                        trgt_layer=key,
                        rel="subcellular_location"
                    )
                )

                self.handle_eco(
                    location
                )

    def subcellular_locations(self, item, protein_id):
        subcellular_locations = item.get("subcellularLocations", [])
        for subcellular_location in subcellular_locations:
            for key, value in subcellular_location.items():
                # print("handle subcl filed", key)
                self.handle_subcl_fields(protein_id, item=subcellular_location, key=key)

    def handle_interactions(self, item, item_id):
        """
        ToDo: request molecule details from accession and chek i its already exist in db -> add ggf.
        """
        interactions = item.get("interactions", None)
        if interactions:
            for inter in interactions:
                if isinstance(inter, dict):
                    for key, value in inter.items():
                        if isinstance(value, dict):
                            inter_accession = value.get("uniProtKBAccession")
                            if inter_accession:
                                self.g_utils.add_edge(
                                    item_id,
                                    inter_accession,
                                    attrs=dict(
                                        rel="interactant",
                                        src_layer="protein",
                                        trgt_layer="",

                                    ))

    async def _add_protein_comment_edges(self, protein_id, entry):
        comments = entry.get("comments")
        if not comments:
            return
        for i, comment in enumerate(comments):
            comment_type = comment.get("commentType")
            if not comment_type:
                continue

            self.handle_texts(comment, protein_id)
            self.subcellular_locations(comment, protein_id)
            self.handle_interactions(comment, protein_id)

            for key, value in comment.items():
                if isinstance(value, dict):
                    self.handle_subcl_fields(protein_id, item=comment, key=key)


    def _add_protein_feature_edges(self, protein_id, entry):
        features = entry.get("features")
        if features:
            for i, feature in enumerate(features):
                feature_id = feature.get("featureId", None)
                if not feature_id:
                    feature_id = f"{protein_id}_feature_{i}"
                feature_type = feature.get("type")
                self.g_utils.add_node(
                    attrs=dict(**{k: v for k, v in feature.items() if k != "id"},
                               id=feature_id,
                               type="protein_feature",
                               info=feature_type,
                               parent=[f"protein"]
                               ))
                self.g_utils.add_edge(
                    src=protein_id,
                    trt=feature_id,
                    attrs=dict(
                        rel=f"has_feature",
                        src_layer="protein",
                        trgt_layer="protein_feature",
                    )
                )
                self.handle_eco(feature)

    def _add_protein_keyword_edges(self, protein_id, entry):
        keywords = entry.get("keywords")
        if keywords:
            for keyword in keywords:
                keyword_id = keyword.get("id")
                self.g_utils.add_node(
                    attrs=dict(id=keyword_id,
                               type="cellular_component",
                               **{k: v for k, v in keyword.items() if k != "id"},
                               ))
                self.g_utils.add_edge(
                    protein_id,
                    keyword_id,
                    attrs=dict(
                        rel="present_in",
                        src_layer = "protein",
                        trgt_layer = "cellular_component",
                    )
                )
                self.handle_eco(
                    item=keyword,
                )

    def _add_protein_reference_edges(self, protein_id, entry):
        references = entry.get("references")
        if references:
            for reference in references:
                citation_id = reference.get("citation", {}).get("id")
                if citation_id:
                    self.g_utils.add_node(
                        dict(
                            id=citation_id,
                            type="reference",
                            **flatten_attributes({k: v for k, v in references.items() if k != "id"},)
                        ))
                    self.handle_eco(reference)
                    self.g_utils.add_edge(
                        protein_id,
                        citation_id,
                        attrs=dict(
                            rel="cited",
                            src_layer = "protein",
                            trgt_layer = "reference",

                        ))

    def _add_protein_cross_reference_edges(self, protein_id, entry):
        cross_references = entry.get("uniProtKBCrossReferences")
        if cross_references:
            for cross_reference in cross_references:
                database = cross_reference.get("database")
                ref_id = cross_reference.get("id")
                if database and ref_id:
                    cross_reference_id = f"{database}:{ref_id}"
                    self.g_utils.add_edge(
                        protein_id,
                        cross_reference_id,
                        attrs=dict(
                            rel="xref",
                            src_layer = "protein",
                            trgt_layer = "xref",
                        ))    

    def update_id_map(self):
        self.all_ids.extend(self.g_utils.schemas.get(self.layer, {}).get("id_map", []))
        with open(self.local_id_map_path, "w") as f:
            json.dump({"ids_fetched": self.all_ids}, f)

if __name__ == "__main__":
    protein_handler = ProteinLayer()
    protein_handler.build_graph()
