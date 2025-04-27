from extract_data import FAIL_LIST, GENE_RELATIONSHIPS
from extract_data.functions.base_request import base_request, abase_request
from extract_data.functions.print_short import p


def get_filter_genes(id: str, gene_list):
    """
    GO:0051569 involved_in

    docs for request: https://api.geneontology.org/#/models/get_models_by_orcid_api_users__orcid__models_get
    Filter gene for GO_ID -> fetch up id so model recognize relationship

    - get all genes for specific go-trm (human)
    - add relationship to given go-term
    - add to item
    """

    for relationship_item in GENE_RELATIONSHIPS:
        try:
            # example id:  -> taxon=NCBITaxon%3A9606 for just human genes
            # https://api.geneontology.org/api/bioentity/function/GO:0044598/genes?taxon=NCBITaxon%3A9606&relationship_type=involved_in&start=0&rows=100000
            url = rf"https://api.geneontology.org/api/bioentity/function/{id}/genes?taxon=NCBITaxon%3A9606&relationship_type={relationship_item}&start=0&rows=100000"
            gene_content = base_request(url)
            """
            {
              "associations": [
                {
                  "id": "556e6950726f744b420950313435353009414b523141310909474f3a3030343435393709504d49443a31383237363833380949444109095009416c646f2d6b65746f207265647563746173652066616d696c792031206d656d62657220413109414c4452317c414c520970726f7465696e097461786f6e3a3936303609323031383132323009556e6950726f740909556e6950726f744b423a50313435353009",
                  "subject": {
                    "id": "UniProtKB:P14550",
                    "iri": "http://identifiers.org/uniprot/P14550",
                    "label": "AKR1A1",
                    "category": [
                      null
                    ],
                    "taxon": {
                      "id": "NCBITaxon:9606",
                      "iri": "http://purl.obolibrary.org/obo/NCBITaxon_9606",
                      "label": "Homo sapiens"
                    }
                  },
                  "object": {
                    "id": "GO:0044597",
                    "iri": "http://purl.obolibrary.org/obo/GO_0044597",
                    "label": "daunorubicin metabolic process",
                    "category": [
                      null
                    ],
                    "taxon": {
                      "id": "NCBITaxon:9606",
                      "iri": "http://purl.obolibrary.org/obo/NCBITaxon_9606",
                      "label": "Homo sapiens"
                    }
                  },
                  "negated": false,
                  "relation": null,
                  "publications": [
                    {
                      "id": "UniProtKB"
                    }
                  ],
                  "evidence_types": [
                    {
                      "id": "ECO:0000314",
                      "label": "direct assay evidence used in manual assertion"
                    }
                  ],
                  "object_closure": null,
                  "provided_by": [
                    "UniProt"
                  ],
                  "evidence": "ECO:0000314"
                },
            """

            if gene_content:
                del gene_content["id"]
                associations = gene_content.get("associations", None)
                # we receive GENE_REQUEST_EXAMPLE_RESPONSE
                if associations and isinstance(associations, list) and len(associations) > 0:
                    print("Content valid...")
                    for gene_item in associations:
                        # todo one request (per relationship_item) got some gene entries -> just evidence is diferent
                        gene_item["relationship_to_go_term"] = relationship_item

                        # todo save proteins extra
                        gene_item["provided_by"].append("LOCAL")

                    gene_list.append(i for i in gene_content["associations"])

                else:
                    print("No Genes given...")
                    # ToDo request other src

            else:
                print("Content response FAILED...")

        except Exception as e:
            print("Content request Error:", e)

    FAIL_LIST.append(id)

# 69487

def process_gene_content(content):
    for index, item in enumerate(content["associations"]):
        print("Working item:", item)
        item.pop('id')
        item["subject"]["gene_detailed_info"]: dict = {}
        gene_id = item["subject"]["id"].split(":", 1)[1]  # UniProtKB:XXXXXXX

        print("Working Gene ID:", gene_id)



# async #



async def aget_filter_genes(go_id: str, gene_list, session):
    """
    Filter genes for GO_ID -> fetch associated genes, recognize relationships,
    and append to the provided gene_list.
    """
    for relationship_item in GENE_RELATIONSHIPS:
        p(f"Processing Genes rel: {relationship_item} for GO_ID: {go_id}")
        try:
            url = rf"https://api.geneontology.org/api/bioentity/function/{go_id}/genes?taxon=NCBITaxon%3A9606&relationship_type={relationship_item}&start=0&rows=100000"
            # Returns genes annotated to the provided GO Term. e.g. GO:0044598
            gene_content = await abase_request(url, session)
#https://api.geneontology.org/api/bioentity/function/GO:0002622/genes?taxon=NCBITaxon%3A9606&relationship_type=involved_in&start=0&rows=100000
            if gene_content:
                associations = gene_content.get("associations", [])
                print()
                if associations:
                    print(f"Valid content for {relationship_item}, Total associations: {len(associations)}")
                    for gene_item in associations:
                        # Add relationship to GO term and mark source
                        gene_item["relationship_go_term"] = relationship_item
                        gene_item.setdefault("provided_by", []).append("LOCAL")
                    gene_list.extend(associations)
                else:
                    print(f"No genes found for relationship: {relationship_item}")
            else:
                print(f"Failed to fetch genes for GO ID: {go_id}")

        except Exception as e:
            print(f"Error processing relationship {relationship_item} for GO ID {go_id}: {e}")
            FAIL_LIST.append(go_id)

async def process_gene_content_async(content):
    """
    Process gene content to extract and clean up detailed gene information.
    """
    for index, item in enumerate(content.get("associations", [])):
        print(f"Processing item {index}")
        item.pop('id', None)  # Remove unnecessary ID
        item["subject"]["gene_detailed_info"] = {}
        gene_id = item["subject"]["id"].split(":", 1)[1]  # Extract UniProtKB:XXXXXXX
        print(f"Extracted Gene ID: {gene_id}")



""" LOGS
Error processing relationship involved_in for GO ID GO:0005176: Response payload is not completed: <TransferEncodingError: 400, message='Not enough data for satisfy transfer length header.'>
Processing Genes rel: acts_upstream_of_or_within for GO_ID: GO:0005176
Error processing relationship involved_in_regulation_of for GO ID GO:0019615: Response payload is not completed: <ContentLengthError: 400, message='Not enough data for satisfy content length header.'>
Error processing relationship involved_in_regulation_of for GO ID GO:0004393: Response payload is not completed: <ContentLengthError: 400, message='Not enough data for satisfy content length header.'>
Error in topology_graph_async for GO ID GO:0043979: Response payload is not completed: <TransferEncodingError: 400, message='Not enough data for satisfy transfer length header.'>
Processing Genes rel: involved_in for GO_ID: GO:0043979
Error processing relationship involved_in_regulation_of for GO ID GO:0033552: Response payload is not completed: <ContentLengthError: 400, message='Not enough data for satisfy content length header.'>
Error processing relationship acts_upstream_of_or_within for GO ID GO:1902325: Response payload is not completed: <ContentLengthError: 400, message='Not enough data for satisfy content length header.'>
Processing Genes rel: involved_in_regulation_of for GO_ID: GO:1902325
Error processing relationship involved_in_regulation_of for GO ID GO:0034018: Response payload is not completed: <ContentLengthError: 400, message='Not enough data for satisfy content length header.'>
Error processing relationship involved_in for GO ID GO:0160129: Response payload is not completed: <TransferEncodingError: 400, message='Not enough data for satisfy transfer length header.'>
Processing Genes rel: acts_upstream_of_or_within for GO_ID: GO:0160129
Error processing relationship involved_in_regulation_of for GO ID GO:0047880: Response payload is not completed: <ContentLengthError: 400, message='Not enough data for satisfy content length header.'>
Error processing relationship acts_upstream_of_or_within for GO ID GO:0034012: Response payload

"""