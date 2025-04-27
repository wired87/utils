"""
Run 1 issues:
- rm source: @evidence
- removed path attr edges
- added submissionNames for proteinDescription
- fixed feature
->  strange connection formed by self.find_node_by_attribute
"""
import asyncio
from asyncio import Semaphore

from tqdm.asyncio import tqdm_asyncio

from utils.file.flatten_dict import flatten_attributes
from ggoogle.storage.storage import GBucket
from utils.utils import GraphUtils, Utils

class ProteinLayer:

    def __init__(self, parent=None, layer=None, path=None):
        self.g_utils = GraphUtils(table_name=layer, upload_to="bq")
        self.layer = layer or "protein"
        self.parent = parent or ["GENE", "MOLECULE", "RNA"]
        self.max_concurrent_tasks = 100
        self.semaphore = Semaphore(self.max_concurrent_tasks)
        self.bucket = GBucket("bestbrain")
        self.utils = Utils()
        self.path=path or "train_data/protein/uniprot_9606.json"
        self.local_path ="data/main_ckpt/protein.json"

    async def get_data(self):
        data = await self.g_utils.load_content(
            local_path=self.local_path,
            bucket_path=self.path,
            layer=self.layer,
            test_chunk=None,
            testing=None
        )
        if not data:
            data = await self.utils.get_process(self.path)
        data = await data["results"]
        if isinstance(data, list):
            print(f"Extracted {len(data)} items")
        else:
            print("unusual format", type(data))
        return data

    async def build_graph(self):
        async def sem_task(task):
            async with self.semaphore:
                return await task

        data = await self.get_data()

        # Directly gather the async tasks
        for i in range(0, len(data), self.max_concurrent_tasks):
            batch_chunk = data[i:i + self.max_concurrent_tasks]
            tasks = [sem_task(self._process_entry(entry, index)) for index, entry in enumerate(batch_chunk)]
            await tqdm_asyncio.gather(*tasks, desc=f"Processing {self.layer}", unit=self.layer)
            await self.g_utils.batch_commit()


    async def _process_entry(self, entry, index):
        protein_id = entry.get('primaryAccession') or entry.get("uniProtkbId", "").split("_")[0]
        # print("working protein", index, ":", protein_id)
        await self._add_edges(entry, protein_id)
        attrs = dict(
            id=protein_id,
            type=self.layer,
            parent=self.parent,
            **flatten_attributes(entry)
        )
        await self.g_utils.add_node(
            attrs=attrs
        )

    async def _add_edges(self, item, protein_id):
        if not protein_id:
            return
        await asyncio.gather(
            self.proteinDescription(item),
            self._add_protein_organism_edge(protein_id, item),
            # self._add_protein_gene_edges(protein_id, item),
            self._add_protein_comment_edges(protein_id, item),
            self._add_protein_feature_edges(protein_id, item),
            self._add_protein_keyword_edges(protein_id, item),
            self._add_protein_reference_edges(protein_id, item),
            self._add_protein_cross_reference_edges(protein_id, item)
        )

    async def _add_protein_organism_edge(self, protein_id, entry):
        organism = entry.get("organism")
        if organism:
            taxon_id = organism.get("taxonId")
            if taxon_id:
                await self.g_utils.add_edge(
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
                gene_id = await self.g_utils.find_node_by_attribute(attr_name="name", attr_value=syn.get("value"))
                if gene_id:
                    return gene_id
        return None

    async def _add_protein_gene_edges(self, protein_id, entry):
        genes = entry.get("genes")
        if genes:
            for gene in genes:
                gene_name = gene.get("geneName", {})
                gene_value = gene_name.get("value")
                # todo gather somehow ensg id
                """gene_id = await self.g_utils.find_node_by_attribute(attr_name="name", attr_value=gene_value)
                if not gene_id:
                    gene_id = await self.gather_gene_id_from_synonym(gene)
                if gene_id:
                    await self.g_utils.add_edge(protein_id, gene_id, rel="encoded_by")
                    await self.handle_eco(gene_name, gene_id)"""

                """orfn = gene.get("orfNames", [])
                for orf in orfn:
                    await self.handle_eco(orf, gene_id if gene_id else gene_value)"""

    async def handle_eco(self, item, item_id=None, parent=None):
        evidences = item.get("evidences", [])
        for k, evidence in enumerate(evidences):
            evidence_id = evidence.get("evidenceCode", None)
            db_source = evidence.get("source", None)
            db_id = evidence.get("id", None)
            if db_id and db_source and evidence_id:
                await self.g_utils.add_node(
                    attrs=dict(id=evidence_id, **evidence, type="eco", parent=[]
                               ))
                await self.g_utils.add_edge(
                    src=db_id,
                    trt=evidence_id,
                    attrs=dict(
                        rel="has_evidence",
                        src_layer=db_source,
                        trgt_layer="eco",
                    )
                )

            if item_id and evidence_id and parent:
                await self.g_utils.add_edge(
                    src=item_id,
                    trt=evidence_id,
                    attrs=dict(
                        rel="has_evidence",
                        src_layer = "protein",
                        trgt_layer = "eco",

                    )
                )

    async def handle_texts(self, item, pid):
        texts = item.get("texts", [])
        for j, text in enumerate(texts):
            await self.handle_eco(text, pid)

    async def proteinDescription(self, item):
        p_des = item.get("proteinDescription", {})
        rn = p_des.get("recommendedName", None)
        if rn:
            fn = rn.get("fullName", {})
            await self.handle_eco(fn, fn.get("value", "unknown"))
        sn = p_des.get("submissionNames", None)

        if sn:
            if isinstance(sn, list):
                for s in sn:
                    fn = s.get("fullName", {})
                    await self.handle_eco(fn, fn.get("value", "unknown"))
            elif isinstance(sn, dict):
                fn = sn.get("fullName", {})
                await self.handle_eco(fn, fn.get("value", "unknown"))

    async def handle_subcl_fields(self, protein_id, item, key):
        # print("Working", key)
        location = item.get(key, {})
        if location:
            location_id = location.get("id", None)
            if location_id:
                await self.g_utils.add_node(
                    attrs=dict(
                        id=location_id,
                        type=key,
                        **location
                    ))

                await self.g_utils.add_edge(
                    protein_id,
                    location_id,
                    attrs=dict(rel="subcellular_location")
                )

                await self.handle_eco(
                    location
                )

    async def subcellular_locations(self, item, protein_id):
        subcellular_locations = item.get("subcellularLocations", [])
        for subcellular_location in subcellular_locations:
            for key, value in subcellular_location.items():
                # print("handle subcl filed", key)
                await self.handle_subcl_fields(protein_id, item=subcellular_location, key=key)

    async def handle_interactions(self, item, item_id):
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
                                await self.g_utils.add_edge(
                                    item_id,
                                    inter_accession,
                                    attrs=dict(rel="interactant"))

    async def _add_protein_comment_edges(self, protein_id, entry):
        comments = entry.get("comments")
        if not comments:
            return
        for i, comment in enumerate(comments):
            comment_type = comment.get("commentType")
            if not comment_type:
                continue

            await self.handle_texts(comment, protein_id)
            await self.subcellular_locations(comment, protein_id)
            await self.handle_interactions(comment, protein_id)

            for key, value in comment.items():
                if isinstance(value, dict):
                    await self.handle_subcl_fields(protein_id, item=comment, key=key)

    r"""async def handle_sequence_embeddings(self, entry_id):
        mach das später konzentrier dich auf die erste version
        #ToDo: Use per-residue file (21GB) -> https://ftp.ebi.ac.uk/pub/contrib/UniProt/embeddings/current_release/UP000005640_9606/per-residue.h5
        h5_file = r"C:\Users\wired\OneDrive\Desktop\Projects\pythonProject\train_data\protein\perprotein_sequence_embeddings_up.h5"
        with h5py.File("path/to/embeddings.h5", "r") as file:
            print(f"number of entries: {len(file.items())}")
            for sequence_id, embedding in file.items():
                print(
                    f"  id: {sequence_id}, "
                    f"  embeddings shape: {embedding.shape}, "
                    f"  embeddings mean: {np.array(embedding).mean()}"
                )
        if entry_id:
            with h5py.File(h5_file, "r") as f:
                f = await handle_h5(PER_PROTEIN)
                for key, embedding in f.items():
                    if key == entry_id:
                        return np.array(embedding)
        return None"""

    async def _add_protein_feature_edges(self, protein_id, entry):
        features = entry.get("features")
        if features:
            for i, feature in enumerate(features):
                feature_id = feature.get("featureId", None)
                if not feature_id:
                    feature_id = f"{protein_id}_feature_{i}"
                feature_type = feature.get("type")
                await self.g_utils.add_node(
                    attrs=dict(**feature,
                               id=feature_id,
                               type="protein_feature",
                               info=feature_type,
                               parent=[f"protein"]
                               ))
                await self.g_utils.add_edge(
                    src=protein_id,
                    trt=feature_id,
                    attrs=dict(
                        rel=f"has_feature",
                        src_layer="protein",
                        trgt_layer="protein_feature",
                    )
                )
                await self.handle_eco(feature)

    async def _add_protein_keyword_edges(self, protein_id, entry):
        keywords = entry.get("keywords")
        if keywords:
            for keyword in keywords:
                keyword_id = keyword.get("id")
                await self.g_utils.add_node(
                    attrs=dict(id=keyword_id,
                               type="cellular_component",
                               **keyword
                               ))
                await self.g_utils.add_edge(
                    protein_id,
                    keyword_id,
                    attrs=dict(
                        rel="present_in",
                        src_layer = "protein",
                        trgt_layer = "cellular_component",
                    )
                )
                await self.handle_eco(
                    item=keyword,
                )

    async def _add_protein_reference_edges(self, protein_id, entry):
        references = entry.get("references")
        if references:
            for reference in references:
                citation_id = reference.get("citation", {}).get("id")
                if citation_id:
                    await self.g_utils.add_node(
                        dict(
                            id=citation_id,
                            type="reference",
                            **flatten_attributes(reference)
                        ))
                    await self.handle_eco(reference)
                    await self.g_utils.add_edge(
                        protein_id,
                        citation_id,
                        attrs=dict(
                            rel="cited",
                            src_layer = "protein",
                            trgt_layer = "reference",

                        ))

    async def _add_protein_cross_reference_edges(self, protein_id, entry):
        cross_references = entry.get("uniProtKBCrossReferences")
        if cross_references:
            for cross_reference in cross_references:
                database = cross_reference.get("database")
                ref_id = cross_reference.get("id")
                if database and ref_id:
                    cross_reference_id = f"{database}:{ref_id}"
                    await self.g_utils.add_edge(
                        protein_id,
                        cross_reference_id,
                        attrs=dict(
                            rel="xref",
                            src_layer = "protein",
                            trgt_layer = "xref",
                        ))
async def main():
    protein_handler=ProteinLayer()
    await protein_handler.build_graph()


if __name__ == "__main__":
    asyncio.run(main())