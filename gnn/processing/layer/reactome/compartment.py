from extract_data.functions.print_short import p
from extract_data.functions.reactome import detail_enhanced
from extract_data.functions.reactome.get_details import get_details


def handle_compartment(detail_item):
    p("handle compartments...")
    compartments = detail_item.get("compartment", None)
    if compartments and isinstance(compartments, list) and len(compartments) > 0:
        print("Compartment")
        for index, compartment_item in enumerate(compartments):
            ref_id = compartment_item.get('dbId', None)
            if ref_id:
                p(f"Working Compartment: {index} ID: {ref_id}")
                """
                {
                  "dbId": 7660,
                  "displayName": "nucleoplasm",
                  "accession": "0005654",
                  "databaseName": "GO",
                  "definition": "That part of the nuclear content other than the chromosomes or the nucleolus.",
                  "name": "nucleoplasm",
                  "url": "https://www.ebi.ac.uk/QuickGO/term/GO:0005654",
                  "className": "Compartment",
                  "schemaClass": "Compartment"
                }
                """
                # todo later drop items and more refine
                comp_url = compartment_item.get("url")
                compartment_item["go_term_id"]: str = ""
                compartment_item["go_term_id"] = comp_url.rsplit('/', 1)[-1].replace("_", ":")
                compartment_details = get_details(url=detail_enhanced(compartment_item))
                compartment_item["compartment_details"] = compartment_details if compartment_details and isinstance(compartment_details, dict) and not compartment_details.get("code") else {}

            else:
                p(f"No ref_ id or invalid: {ref_id}")
