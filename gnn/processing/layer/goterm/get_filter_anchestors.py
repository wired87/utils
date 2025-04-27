
from extract_data import ANCESTOR_ELEMENTS, FAIL_LIST
from extract_data.functions.base_request import base_request


def get_filter_ancestors(item):
    for element in ANCESTOR_ELEMENTS:  # -> e.g. is_a,...
        # example item["id"] : GO:0042389
        url = f"https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms/{item['id']}/ancestors?relations={element}"
        try:
            content = base_request(url)
            """
            {
              "numberOfHits": 1,
              "results": [
                {
                  "id": "GO:0042389",
                  "isObsolete": false,
                  "name": "omega-3 fatty acid desaturase activity",
                  "definition": {
                    "text": "Catalysis of the introduction of an omega-3 double bond into the fatty acid hydrocarbon chain.",
                    "xrefs": [
                      {
                        "dbCode": "PMID",
                        "dbId": "9037020"
                      }
                    ]
                  },
                  "ancestors": [ -> Just extrfact ancestors
                    "GO:0003824",
                    "GO:0016705",
                    "GO:0016491",
                    "GO:0042389",
                    "GO:0003674"
                  ],
                  "aspect": "molecular_function",
                  "usage": "Unrestricted"
                }
              ],
              "pageInfo": null
            }
            
            """
            if content:
                all_ancestors = content["results"][0]["ancestors"]
                for i in all_ancestors:
                    # example i: GO:0003674
                    ancestor_url = f"https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms/{i}/constraints"
                    ancestor_details = base_request(ancestor_url)

                    ancestor_info = {}
                    ancestor_info["ancestors_gene_ontology_id"] = i
                    ancestor_info["ancestor_name"] = ancestor_details["results"][0]["name"]
                    ancestor_info["ancestor_description"] = ancestor_details["results"][0]["definition"]["text"]

                    print("Append Ancestor info:", ancestor_info)
                    # create a new dict and give it a list
                    item["ancestors"].setdefault(element, []).append(ancestor_info)
            else:
                FAIL_LIST.append(
                    {
                        "item": item["id"],
                        "ancestor": element
                    }
                )

        except Exception as e:
            print("Error get ANCESTOR:", e)
            FAIL_LIST.append(
                {
                    "item": item["id"],
                    "ancestor": element
                }
            )







