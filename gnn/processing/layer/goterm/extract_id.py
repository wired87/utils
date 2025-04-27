
FAIL_LIST = []
async def aget_id(go_id: str):
    try:  # "http://purl.obolibrary.org/obo/GO_0099593"
        filtered_go_id = go_id.rsplit('/', 1)[-1]  # GO_0035449
        adapted_go_id = filtered_go_id.replace("_", ":")  # GO:0035449
        return adapted_go_id

    except KeyError as e:
        print("Extraction of ID failed (KeyError):", e)
        FAIL_LIST.append({"id": go_id})
    except Exception as e:
        print("Extraction of ID failed:", e)
        FAIL_LIST.append({"id": go_id})
