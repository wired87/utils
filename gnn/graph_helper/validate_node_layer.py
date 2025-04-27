def id_clasiication(rel):
    if "IS" in rel:
        print("Layer before", rel)
    if rel.startswith("R-") or rel.startswith("Reactome:"):
        rel.replace("Reactome:", "")
        # reactome id -> R-HSA-1169397
        parts = rel.split("-")
        if len(parts) >= 2:
            extr_id = "-".join(parts[:2])  # -> R-HSA join the first two parts
            extr_id = extr_id.replace("-", "")
            # print("Extr Reactome id", extr_id)
            return extr_id

    rel = rel.split(":")[0].split("_")[0]
    if "IS" in rel:
        print("Layer after", rel)
    return rel


class NodeLayerValidator:
    def __init__(self):
        self.db_map = {
            # Standard biological databases
            "ens": "Ensembl",
            "refseq": "RefSeq",
            "refseq_peptide": "RefSeq (Peptide)",
            "refseq_mrna": "RefSeq (mRNA)",
            "uniprot": "UniProt",
            "uniprot_gn": "UniProt Gene",
            "ncbi": "NCBI",
            "genecards": "GeneCards",
            "chebi": "ChEBI",
            "gtex": "GTEx",
            "geo": "GEO",
            "sra": "SRA",
            "ebi": "EBI",
            "dbsnp": "dbSNP",
            "pubchem": "PubChem",
            "arrayexpress": "ArrayExpress",
            "hgnc": "HGNC",
            "go": "GO",
            "omim": "OMIM",
            "mim_gene": "OMIM Gene",
            "mim_morbid": "OMIM Morbid",
            "pdb": "PDB",
            "kegg": "KEGG",
            "pfam": "Pfam",
            "panther": "PANTHER",
            "interpro": "InterPro",
            "prosite_patterns": "Prosite (Patterns)",
            "prosite_profiles": "Prosite (Profiles)",  # ✅ Added
            "embl": "EMBL",
            "ccds": "CCDS",
            "ucsc": "UCSC",
            "wikigene": "WikiGene",
            "biogrid": "BioGRID",  # ✅ Normalized to lowercase key
            "cdd": "CDD",  # ✅ Added
            "uniparc": "UniParc",  # ✅ Added
            "superfamily": "SuperFamily",  # ✅ Added
            "smart": "Smart",  # ✅ Added
            "ncbifam": "NCBIfam",  # ✅ Added
            "gene3d": "Gene3D",  # ✅ Added
            "pirsf": "PIRSF",  # ✅ Added
            "mobidblite": "MobiDBLite",  # ✅ Added
            "ncoils": "ncoils",  # ✅ Added
            "Reactome": "Reactome",  # ✅ Added

            # Relationship-based mappings
            "alphafold": "has_predicted_structure",
            "protein_id": "has_protein_id",
            "hpa": "linked_to_protein_expression",
            "seg": "has_segment_annotation",
            "entrezgene": "mapped_to_entrez_id",
            "coord_system": "aligned_to_coordinate_system",
            "strand": "located_on_strand",
            "transcripts": "contains_transcripts",
            "exons": "contains_exons"
        }

    def layer_from_key(self, key):
        try:
            #print("key", key)
            if key is not None:
                if key.lower() == "reactome" or "reactome" in key.lower():
                    #print("Reactome key converted")
                    return "RHSA"
                elif "uniprot" in key.lower():
                    return "protein"
                elif key.lower().startswith("ensg"):
                    return "GENE"
                elif key.lower().startswith("ense"):
                    return "TRANSCRIPT"
                elif key.lower().startswith("enst"):
                    return "TRANSCRIPT"
                elif key.lower().startswith("ensr"):
                    return "REGULATORY_FEATURE"
                elif key.lower().startswith("ensp"):
                    return "PROTEIN"
                elif key.lower().startswith("ens"):
                    return "GENE"
                elif "entrezgene" in key.lower() and "trans" in key.lower() and "name" in key.lower():
                    return "ENTREZGENE"
                for k, v in self.db_map.items():
                    if k.lower() in key.lower():
                        return k.upper()
        except Exception as e:
            print("Error in layer_from_key:", e)

        return key.upper().replace(" ", "_")
