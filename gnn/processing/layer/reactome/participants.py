from extract_data.functions.base_request import base_request
from extract_data.functions.print_short import p, pp
from extract_data.functions.reactome.get_details import get_details


def request_participants_and_details(detail_item):
    """
    Participant  = molecules that are active within a reaction
    """

    detail_item["participants"] = {}
    url = rf"https://reactome.org/ContentService/data/participants/{detail_item['stId']}"
    p(f"Request participants: {url}")

    """
    [
      {
        "peDbId": 1299271,
        "displayName": "TALK 1and 2 [plasma membrane]",
        "schemaClass": "DefinedSet",
        "refEntities": [
          {
            "dbId": 145500,
            "identifier": "Q96T55",
            "schemaClass": "ReferenceGeneProduct",
            "displayName": "UniProt:Q96T55 KCNK16",
            "icon": "EntityWithAccessionedSequence",
            "url": "http://purl.uniprot.org/uniprot/Q96T55"
          },
          {
            "dbId": 52162,
            "identifier": "Q96T54",
            "schemaClass": "ReferenceGeneProduct",
            "displayName": "UniProt:Q96T54 KCNK17",
            "icon": "EntityWithAccessionedSequence",
            "url": "http://purl.uniprot.org/uniprot/Q96T54"
          }
        ]
      },
    ...
    """

    content = base_request(url)
    if content and isinstance(content, list) and len(content) > 0 and not "NOT_FOUND" in content:
        p("Participants content fetched...")
        # participant detail with peDbId
        if isinstance(content, list):
            p(f"... & valid. Len:{len(content)}")
            for item in content:  # -> single participant
                item_id = item.get('peDbId', None)
                if item_id:
                    p(f"Working participant {item_id}")
                    item["participant_details"] = []
                    participant_subunits = get_details(
                        url=rf"https://reactome.org/ContentService/data/complex/{item_id}/subunits?excludeStructures=false"
                    )
                    """item_id
                    [
                      {
                        "dbId": 1299275,
                        "displayName": "TALK1 homomer [plasma membrane]",
                        "stId": "R-HSA-1299275",
                        "stIdVersion": "R-HSA-1299275.1",
                        "name": [
                          "TALK1 homomer"
                        ],
                        "speciesName": "Homo sapiens",
                        "isChimeric": false,
                        "inDisease": false,
                        "schemaClass": "Complex",
                        "className": "Complex"
                      },
                    """
                    if participant_subunits and isinstance(participant_subunits, list):
                        print("Participant subunit request successful...")
                        item["participant_subunits"] = participant_subunits
                    else:
                        item["participant_subunits"] = []
                        print("FAILED Participant subunit request...\n item", pp(participant_subunits))

                    details_url = rf"https://reactome.org/ContentService/data/query/enhanced/{item_id}"
                    participant_enhanced_details = base_request(details_url)
                    if participant_enhanced_details and isinstance(participant_enhanced_details, dict):
                        p(f"Participants fetched for {participant_enhanced_details.get('displayName')}")
                        item["participant_details"] = participant_enhanced_details
                    else:
                        item["participant_details"] = {}
                        p(f"No detailes could be fetched")

                    ref_entities = item.get("refEntities", None)
                    if ref_entities and isinstance(ref_entities, list) and len(ref_entities) > 0:
                        for index, ref in enumerate(ref_entities):
                            ref_id = ref.get('dbId', None)
                            """
                            {
                                "dbId": 145500,
                                "identifier": "Q96T55",
                                "schemaClass": "ReferenceGeneProduct",
                                "displayName": "UniProt:Q96T55 KCNK16",
                                "icon": "EntityWithAccessionedSequence",
                                "url": "http://purl.uniprot.org/uniprot/Q96T55"
                            }
                            """
                            p(f"Fetch details for Item: {index} ID: {ref_id}")
                            if ref_id:
                                details = get_details(url=rf"https://reactome.org/ContentService/data/query/enhanced/{ref_id}")
                                if details and isinstance(details, dict):
                                    p(f"Extraction successful...")
                                    ref["ref_entity_details"] = details
                                else:
                                    p(f"ID {ref_id} could not be fetched. \n -> Item:{pp(ref)}")
                    else:
                        print("FAILED etch ref entities:", pp(ref_entities))

                    reference_entities(item)

                else:
                    p(f"Received id {item_id} INVALID...")

    # todo Also request participants references when no entry was found
    else:
        p("Fetched participants invalid... ")
        reference_entities(detail_item)
        detail_item["participants"] = []


def reference_entities(item):
    re_id = item.get('dbId', item.get("peDbId", None))
    p(f"Working item {re_id}")
    if re_id:
        p("Extracted re_id valid...")
        re_entities_url = rf"https://reactome.org/ContentService/data/participants/{re_id}/referenceEntities"
        content = base_request(re_entities_url)
        """
        [
          {
            "dbId": 64982,
            "displayName": "UniProt:Q9Y5K1 SPO11",
            "databaseName": "UniProt",
            "identifier": "Q9Y5K1",
            "name": [
              "SPO11"
            ],
            "otherIdentifier": [
            xxxxx,
            xxxxx,...
            ]

        """
        if content:
            p(f"Extracted reference_entities content...")
            item["reference_entities"] = content
    else:
        print("INVALID re_id -> reference_entities")
