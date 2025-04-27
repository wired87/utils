from datetime import date

from extract_data.functions.reactome.details import request_item_details
from extract_data.functions.save_data_checkpoint import save_data_checkpoint


def extract_data(data):
    """
    Recursively extract all values associated with a specific key from a deeply nested structure.

    :param nested_structure: The nested structure (list or dictionary):

    [
      {
        "stId": "R-HSA-9612973",
        "name": "Autophagy",
        "species": "Homo sapiens",
        "type": "TopLevelPathway",
        "diagram": true,
        "children": [
          {
            "stId": "R-HSA-1632852",
            "name": "Macroautophagy",
            "species": "Homo sapiens",
            "type": "Pathway",
            "diagram": true,
            "children": [
              {
                "stId": "R-HSA-5672817",
                "name": "Active MTORC1 binds the ULK1 complex",
                "species": "Homo sapiens",
                "type": "Reaction",
                "diagram": false
              },

    :param key_to_find: The key whose values you want to extract.
    :return: A list of values matching the key.
    Einfach double entries geht am schnellsten -> dumm aber schnell
    #
    Einfach datenbanken downloaden u identifier bereitstellen - das modell nur mit identifiern u kurzer beschriebung trainieren

    check dynamic for nested events

    """

    for k, i in enumerate(data):
        print("Working item:", k)
        print("data", type(i))
        request_item_details(top_lvl_item=i)  # i = str
        children = i.get("children", [])
        if children:
            extract_data(data=i["children"])

    save_data_checkpoint(
        path=rf"C:\Users\wired\OneDrive\Desktop\Projects\aws_to_bucket\extract_data\filtered_data\checkpoints\extract_reactome_data_{date.today()}.json",
        content=data
    )



class ReactomeAPI:
    """A comprehensive class to interact with Reactome REST API."""

    BASE_URL = "https://reactome.org/ContentService"

    def __init__(self, identifier):
        self.identifier = identifier

    def fetch_data(self, endpoint, params=None):
        """Helper method to make GET requests to the Reactome API."""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {url}: {e}")
            return None

    def get_database_info(self):
        """Fetch database name and version."""
        name = self.fetch_data("data/database/name")
        version = self.fetch_data("data/database/version")
        return {"database_name": name, "database_version": version}

    def get_event_details(self):
        """Fetch enhanced details about the identifier."""
        return self.fetch_data(f"data/query/enhanced/{self.identifier}")

    def get_pathways(self):
        """Fetch pathways associated with the identifier."""
        return self.fetch_data(f"data/mapping/{self.identifier}/pathways")

    def get_reactions(self):
        """Fetch reactions associated with the identifier."""
        return self.fetch_data(f"data/mapping/{self.identifier}/reactions")

    def get_orthology(self, species_id):
        """Fetch orthology information for a given species."""
        return self.fetch_data(f"data/orthology/{self.identifier}/species/{species_id}")

    def get_interactions(self):
        """Fetch interaction details for the identifier."""
        return self.fetch_data(f"interactors/static/molecule/{self.identifier}/details")

    def get_references(self):
        """Fetch reference entities for the identifier."""
        return self.fetch_data(f"references/mapping/{self.identifier[-4:]}") # last 4 character form id

    def get_all_information(self):
        """Aggregate all relevant information about the identifier."""
        return {
            "database_info": self.get_database_info(),
            "event_details": self.get_event_details(),
            "pathways": self.get_pathways(),
            "reactions": self.get_reactions(),
            "interactions": self.get_interactions(),
            "participants": self.get_participants(),
            "references": self.get_references(),
        }