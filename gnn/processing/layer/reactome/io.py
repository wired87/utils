from typing import List

from extract_data.functions.base_request import base_request
from extract_data.functions.print_short import p
from extract_data.functions.reactome.compartment import handle_compartment


def add_io(detail_item):
    io_list = ["input", "output"]
    for io in io_list:
        io_object_list: List or None = detail_item.get(io)  # ITEM[INPUT]
        if io_object_list and isinstance(io_object_list, list) and len(io_object_list):
            for single_item in io_object_list:

                """
                {
                  "dbId": 29428,
                  "displayName": "DNA [nucleoplasm]",
                  "stId": "R-ALL-29428",
                  "stIdVersion": "R-ALL-29428.1",
                  "name": [
                    "DNA",
                    "Deoxyribonucleic Acid"
                  ],
                  "consumedByEvent": [
                    912363
                  ],
                  "inDisease": false,
                  "schemaClass": "OtherEntity",
                  "className": "OtherEntity"
                },
                """

                if not isinstance(single_item, dict):
                    # some entries are jut ids for db entry -> same id in item under dbId -> or just search fro stId
                    print(f"Unusual entry found: '{io}'-> remove...")
                    io_object_list.remove(single_item)
                    continue

                single_item["details"] = {}
                url = f"https://reactome.org/ContentService/data/query/enhanced/{single_item['stId']}"
                details = base_request(url)

                if details:
                    single_item["details"] = details
                    handle_compartment(details)
                else:
                    p("No details in add_io")

                subunit_url = rf"https://reactome.org/ContentService/data/complex/{single_item.get('dbId')}/subunits?excludeStructures=false"
                content = base_request(subunit_url)
                if content:
                    print("Subunits fetched...")
                    single_item["subunits"] = content

