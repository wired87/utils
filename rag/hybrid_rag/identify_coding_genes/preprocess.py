def preprocess_prompt(query):
    return f"""
        Expand the following query with related terms and synonyms from the Gene Ontology (GO) database.
        Query: "{query}"

        - Include precise scientific terms related to biological processes, molecular functions, and cellular components.
        - For 'dendrite,' include 'neurite,' 'synapse,' 'axon,' 'neural branching.'
        - Extract relevant GO-Terms that closely match the query context.

        Return a structured list of expanded search terms.
        """