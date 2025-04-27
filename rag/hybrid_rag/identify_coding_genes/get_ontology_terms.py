def get_on_terms(query):
    return f"""
        Search in the provided graph for all ontology term ids that are involved in the following process: {query}
        """