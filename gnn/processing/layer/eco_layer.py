import re


from utils.utils import GraphUtils


class ECO:

    def __init__(self, parent, layer):
        self.g_utils = GraphUtils(table_name=layer)
        self.layer = layer
        self.parent = parent

    def extract_eco(self, evidence_string):
        """
        Extract the ECO:NUMBER and its description from a given string.

        Args:
            evidence_string (str): The input string containing ECO information.

        Returns:
            dict: A dictionary with 'eco_id' and 'description', or None if no match is found.
        """
        # Define the regex pattern to capture ECO:NUMBER and description
        pattern = r"ECO:\d{7}"

        match: re.Match = re.search(pattern, evidence_string)

        if match:
            eco_id = match.group(0)
            return eco_id

    async def main(self, data):
        for item in data:
            # print("Add item", item["id"])
            eco_id = item['id']
            if eco_id.startswith("ECO"):
                await self.g_utils.add_node(
                    attrs=dict(
                        **{k: v for k, v in item.items() if k not in ["id", "parent", "type"]},
                        id=eco_id,
                        type=self.layer,
                        parent=self.parent
                    ))
                for key, value in item.items():
                    if "ECO:" in value and not key == "id" and not "[ECO:" in value and not "ECO:R" in value and not "OECO:" in value and not "ECO:M" in value:
                        stuff = self.extract_eco(value)
                        # print(f"Connect {eco_id}->{key}->{stuff}")
                        if stuff:
                            await self.g_utils.add_node(
                                attrs=dict(id=stuff,
                                           type="eco",
                                           parent=self.parent,
                                           ))
                            await self.g_utils.add_edge(
                                src=eco_id,
                                trt=stuff,
                                attrs=dict(rel=key)
                            )
