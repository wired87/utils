"""
Found 22 new rows, 18 existing rows of 40 in GO.
Error while inserting batch: 400 Invalid value for column name in table GO: Expected STRING.
failed insert row {'id': 'GO:0004842', 'type': 'GO', 'parent': ['ontology'], 'child': None, 'info': None, 'name': 'ubiquitin-protein transferase activity', 'def': None, 'comment': None, 'synonym': ['E2 BROAD', 'E3 BROAD', 'ubiquitin conjugating enzyme activity NARROW', 'ubiquitin ligase activity NARROW', 'ubiquitin protein ligase activity NARROW', 'ubiquitin protein-ligase activity NARROW', 'ubiquitin-conjugating enzyme activity NARROW'], 'property_value': None, 'created_by': None, 'xref': None, 'creation_date': None} <class 'dict'> in table cause error: 400 Invalid value for column name in table GO: Expected STRING.
failed insert row {'id': 'GO:0005634', 'type': 'GO', 'parent': ['ontology'], 'child': None, 'info': 'GO:0005634', 'name': 'nucleus', 'def': 'A membrane-bounded organelle of eukaryotic cells in which chromosomes are housed and replicated. In most cells the nucleus contains all of the cells chromosomes except the organellar chromosomes and is the site of RNA synthesis and processing. In some species or in specialized cell types RNA metabolism or DNA replication may be absent. GOC:go_curators', 'comment': None, 'synonym': None, 'property_value': None, 'created_by': None, 'xref': ['NIF_Subcellular:sao1702920020', 'Wikipedia:Cell_nucleus'], 'creation_date': None} <class 'dict'> in table cause error: 400 Invalid value for column name in table GO: Expected STRING.
failed insert row {'id': 'GO:0016301', 'type': 'GO', 'parent': ['ontology'], 'child': None, 'info': None, 'name': 'kinase activity', 'def': None, 'comment': 'Note that this term encompasses all activities that transfer a single phosphate group although ATP is by far the most common phosphate donor reactions using other phosphate donors are included in this term.', 'synonym': ['p', 'h', 'o', 's', 'p', 'h', 'o', 'k', 'i', 'n', 'a', 's', 'e', ' ', 'a', 'c', 't', 'i', 'v', 'i', 't', 'y', ' ', 'E', 'X', 'A', 'C', 'T'], 'property_value': None, 'created_by': None, 'xref': ['Reactome:R-HSA-6788855 FN3KRP phosphorylates PsiAm RibAm', 'Reactome:R-HSA-6788867 FN3K phosphorylates ketosamines'], 'creation_date': None} <class 'dict'> in table cause error: 400 Invalid value for column name in table GO: Expected STRING.
failed insert row {'id': 'GO:0019107', 'type': 'GO', 'parent': ['ontology'], 'child': None, 'info': None, 'name': 'myristoyltransferase activity', 'def': 'Catalysis of the transfer of a myristoyl CH3-CH212-CO- group to an acceptor molecule. GOC:ai', 'comment': None, 'synonym': None, 'property_value': None, 'created_by': None, 'xref': ['Reactome:R-HSA-141367 Myristoylation of tBID by NMT1', 'Reactome:R-HSA-162914 Myristoylation of Nef'], 'creation_date': None} <class 'dict'> in table cause error: 400 Invalid value for column name in table GO: Expected STRING.


"""

from data.extractors.db_id_extractor import DBIdExtractor
from ggoogle.spanner.sanetize import sanitize_for_spanner
from gnn.graph_helper.validate_node_layer import id_clasiication
from utils.utils import GraphUtils


class ROHandler:

    def __init__(self, parent, layer):
        self.g_utils = GraphUtils(table_name=layer)
        self.parent = parent
        self.layer = layer
        print("RO self.parent", self.parent)
        print("RO self.layer", self.layer)
        self.dbid_extractor = DBIdExtractor()


    async def main(self, data):

        split_data = self.data_to_list(data)

        # save mem
        data = None
        keys_to_remove_list = set(['replaced_by', "relationship", 'subset', 'xref', 'inverse_of', 'id_info', 'is_a', 'disjoint_from',
        'holds_over_chain', 'domain', 'expand_expression_to', 'property_value', 'transitive_over', 'range'])
        for i, term in enumerate(split_data):
            raw_id = term.get("id")
            #print("raw_id", raw_id)
            item_id = self.dbid_extractor.extract_identifiers(raw_id)
            if item_id != raw_id:
                term["id_info"] = term.get("id")
            if isinstance(item_id, list):
                #print("List id found", item_id)
                item_id = item_id[0]
            #print("Extracted id", item_id)
            term["id"] = str(item_id).replace(" ", "")

            term["parent"] = self.parent
            term["type"] = id_clasiication(term["id"])

            """if i == len(split_data) -1:
                print("Item:", term)"""
            """for p in self.parent:
                await self.g_utils.add_edge(src=item_id, trt=p, attrs=dict(rel=p))
            """

            if "property_value" in term:
                pv =term["property_value"]
                if isinstance(pv, str):
                    term["property_value"] = [str(pv)]
            if "subset" in term:
                pv =term["subset"]
                if isinstance(pv, str):
                    term["subset"] = [str(pv)]
            if "synonym" in term:
                pv =term["synonym"]
                if isinstance(pv, str):
                    term["synonym"] = [str(pv)]
            if "name" in term:
                pv = term["name"]
                term["name"] = sanitize_for_spanner(str(pv))

            for k, v in term.items():
                if k != "id":
                    if isinstance(v, list):
                        for index, value in enumerate(v):
                            await self.handle_edges(item_id, value, k)
                    else:
                        await self.handle_edges(item_id, v, k)

            # rm fields already added as edge
            for item in keys_to_remove_list:
                if item in term:
                    term.pop(item)

            await self.g_utils.add_node(term)

    async def handle_edges(self, item_id, v, k):
        key_value_ids = self.dbid_extractor.extract_identifiers(input_string=v)
        rel = v.split("!")[-1]
        if len(key_value_ids) and isinstance(key_value_ids, list):
            for key in key_value_ids:
                if key != item_id:
                    await self.g_utils.add_node(
                        attrs={
                            "id": key,
                            "type": id_clasiication(key),
                            "parent": self.parent,
                            "info": rel if rel else None
                        }
                    )
                    await self.g_utils.add_edge(
                        item_id,
                        key,
                        attrs=dict(
                            rel=k,
                            #info=rel if rel else None
                        )
                    )


    def data_to_list(self, data):
        """
        Parses OBO-like data, handling duplicate keys by creating lists of values.

        Args:
            data (str): The OBO-like data string.

        Returns:
            list: A list of dictionaries, where each dictionary represents a Term entry.
                  Duplicate keys have their values stored in lists.
        """
        terms = []
        current_term = None
        if not data:
            raise Exception("Warning: Input data is empty.")

        print("Converting RO data_to_list")
        for line in data.splitlines():
            line = line.strip()
            #print("current_term and line", current_term, line)

            if line.startswith("[") and line.endswith("]"):  # Typedef || Term
                #print("Start line:", line)
                if current_term:
                    terms.append(current_term)
                current_term = {}
            elif isinstance(current_term, dict) and line:
                #print("current_term and line2")
                if ":" in line:
                    #print(":in line")
                    key, value = line.split(":", 1)
                    #print("Extracted", key, value)
                    key = key.strip()
                    value = value.strip()
                    value = sanitize_for_spanner(value)

                    # Handle comments
                    if "!" in value:
                        value, comment = value.split("!", 1)
                        value = value.strip()

                    # Handle options (e.g., {all_only="true"})
                    if "{" in value:
                        value = value.strip()  # ensure no leading/trailing whitespace.

                    # Handle duplicate keys by creating lists
                    if key in current_term:
                        if isinstance(current_term[key], list):
                            current_term[key].append(value)
                        else:
                            current_term[key] = [current_term[key], value]
                    else:
                        current_term[key] = value

        #print("Append", current_term)
        if current_term:
            terms.append(current_term)
        print("Example term extracted", terms[0])
        print("Example term extracted 222", terms[19])
        return terms






