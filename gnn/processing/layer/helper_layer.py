"""
Funktionen:
-


"""

import aiofiles

from agents import ControlAgent
from agents.extractor import FetchAgent
from ggoogle import model


def extract_eco(evidence_string):
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
        print("match", eco_id)
        numeric = eco_id[4:].isdigit()
        if numeric:
            return str(match.group(0))








async def process_layer(data, G):
    """
    Represents wide varity to different ml helper models
    enable dynamic target (e.g., classification label or similarity) for specific case, classified by ml model
    Bsp: Database fetch (url) -> process -> integration in graph

    Each node represents a 100% dynamic adjustable & extendable graph network
    - init access / create venv
    - look given data / kb (in specific folder/file
    - prompt categorize  : extend graph
    - lib & kb fetcher & processor :
    - additional data fetcher and processor
    - code checker
    - dataset preprocessor code writer (get ields of interest)
    - 2 operators (each main step goes to one of them, the other one compares, can give tios for improvement,... continue just if both give ok,
    - helper -> if anything is missing , formulate question
    prompt -> comprehensive list of functionality -> node incl. re agent , embeds, add kb, ...

    agent build everything rom ground up
    """
    operator_init_prompt ="""You are an ai agent system operator. 
    Write a mathing role and base prompt for the given types of ai agents
    """
    task=None # todo mit function calling promts dynamisch anpassen
    task_type=None
    context=None
    history=None
    total_tools=[
        "search_web",
        "crawl_url(s)",
        "run_command",
    ]


    unfinished = True
    input_prmpt="Fetch the following datasets and process it and create a scheme from its content inside the /data scr"






    # get tasks ->

    detailed_info_op1 =f"""You are a 
    You receive a list of tasks:
    {""} # dataset download, processing, graph creation
    For each task, you will define explicit requirements 
    """

    for eco in data:
        eco_id = eco['id']
        print("Add node", eco_id)
        G.add_node(
            eco_id,
            **eco,
            layer='eco'
        )
        for edge, value in eco.items():
            if "ECO:" in value and not edge == "id" and not "[ECO:" in value and not "ECO:R" in value and not "OECO:" in value and not "ECO:M" in value:
                print(f"eco edge: {edge}:{value}")
                stuff = extract_eco(value)
                if stuff:
                    G.add_edge(eco_id, stuff, relationship=edge)

import re

async def save_python_code(code_string, output_file):
    """
    Transforms a given Python code string into a runnable Python file.

    :param code_string: String containing Python code (may include markdown markers like ```python).
    :param output_file: Path to save the transformed Python code as a file.
    """
    # Remove markdown code block markers
    clean_code = re.sub(r"text: ```python\n", "", code_string)  # Remove opening marker
    clean_code = re.sub(r"```", "", clean_code)  # Remove closing marker
    exec(clean_code.strip())
    # Write the cleaned code to a Python file
    try:
        async with aiofiles.open(class_out_path, mode="w") as f:
            await f.write(str(clean_code))
        print(f"Code saved successfully to {output_file}")
    except Exception as e:
        print(f"An error occurred while saving the code: {e}")


#text: "```python\nimport networkx as nx\n\nclass UniProtKBGraphBuilder:\n    def __init__(self, data):\n        self.data = data\n        self.graph = nx.Graph()\n\n    def build_graph(self):\n        for key, entry in self.data.items():\n            self._add_protein_node(entry)\n            self._add_organism_node(entry)\n            self._add_gene_nodes(entry)\n            self._add_comment_nodes(entry)\n            self._add_feature_nodes(entry)\n            self._add_keyword_nodes(entry)\n            self._add_reference_nodes(entry)\n            self._add_cross_reference_nodes(entry)\n            self._add_edges(entry)\n        return self.graph\n\n    def _add_protein_node(self, entry):\n        protein_id = entry.get(\'primaryAccession\')\n        if protein_id:\n            self.graph.add_node(protein_id, label=\'Protein\', data=entry)\n\n    def _add_organism_node(self, entry):\n        organism = entry.get(\'organism\')\n        if organism:\n            taxon_id = organism.get(\'taxonId\')\n            if taxon_id:\n                self.graph.add_node(taxon_id, label=\'Organism\', data=organism)\n\n    def _add_gene_nodes(self, entry):\n        genes = entry.get(\'genes\')\n        if genes:\n            for gene in genes:\n                gene_name = gene.get(\'geneName\', {}).get(\'value\')\n                if gene_name:\n                    self.graph.add_node(gene_name, label=\'Gene\', data=gene)\n\n    def _add_comment_nodes(self, entry):\n        comments = entry.get(\'comments\')\n        if comments:\n            for comment in comments:\n                comment_type = comment.get(\'commentType\')\n                if comment_type:\n                    # Create a more robust comment_id by hashing the comment text\n                    comment_text = comment.get(\'texts\', [{}])[0].get(\'value\', \'\')\n                    comment_id = f\"{comment_type}_{hash(comment_text)}\"\n                    self.graph.add_node(comment_id, label=\'Comment\', data=comment)\n\n    def _add_feature_nodes(self, entry):\n        features = entry.get(\'features\')\n        if features:\n            for feature in features:\n                feature_type = feature.get(\'type\')\n                if feature_type:\n                    # Create a more robust feature_id by hashing the feature description\n                    feature_description = feature.get(\'description\', \'\')\n                    feature_id = f\"{feature_type}_{hash(feature_description)}\"\n                    self.graph.add_node(feature_id, label=\'Feature\', data=feature)\n\n    def _add_keyword_nodes(self, entry):\n        keywords = entry.get(\'keywords\')\n        if keywords:\n            for keyword in keywords:\n                keyword_id = keyword.get(\'id\')\n                if keyword_id:\n                    self.graph.add_node(keyword_id, label=\'Keyword\', data=keyword)\n\n    def _add_reference_nodes(self, entry):\n        references = entry.get(\'references\')\n        if references:\n            for reference in references:\n                reference_id = reference.get(\'citation\', {}).get(\'id\')\n                if reference_id:\n                    self.graph.add_node(reference_id, label=\'Reference\', data=reference)\n\n    def _add_cross_reference_nodes(self, entry):\n        cross_references = entry.get(\'uniProtKBCrossReferences\')\n        if cross_references:\n            for cross_reference in cross_references:\n                database = cross_reference.get(\'database\')\n                if database:\n                    cross_reference_id = f\"{database}_{cross_reference.get(\'id\')}\"\n                    self.graph.add_node(cross_reference_id, label=\'CrossReference\', data=cross_reference)\n\n    def _add_edges(self, entry):\n        protein_id = entry.get(\'primaryAccession\')\n        if protein_id:\n            self._add_protein_organism_edge(protein_id, entry)\n            self._add_protein_gene_edges(protein_id, entry)\n            self._add_protein_comment_edges(protein_id, entry)\n            self._add_protein_feature_edges(protein_id, entry)\n            self._add_protein_keyword_edges(protein_id, entry)\n            self._add_protein_reference_edges(protein_id, entry)\n            self._add_protein_cross_reference_edges(protein_id, entry)\n\n    def _add_protein_organism_edge(self, protein_id, entry):\n        organism = entry.get(\'organism\')\n        if organism:\n            taxon_id = organism.get(\'taxonId\')\n            if taxon_id:\n                self.graph.add_edge(protein_id, taxon_id, label=\'IN_ORGANISM\')\n\n    def _add_protein_gene_edges(self, protein_id, entry):\n        genes = entry.get(\'genes\')\n        if genes:\n            for gene in genes:\n                gene_name = gene.get(\'geneName\', {}).get(\'value\')\n                if gene_name:\n                    self.graph.add_edge(protein_id, gene_name, label=\'ENCODED_BY\')\n\n    def _add_protein_comment_edges(self, protein_id, entry):\n        comments = entry.get(\'comments\')\n        if comments:\n            for comment in comments:\n                comment_type = comment.get(\'commentType\')\n                if comment_type:\n                    # Use the robust comment_id created in _add_comment_nodes\n                    comment_text = comment.get(\'texts\', [{}])[0].get(\'value\', \'\')\n                    comment_id = f\"{comment_type}_{hash(comment_text)}\"\n                    self.graph.add_edge(protein_id, comment_id, label=\'HAS_COMMENT\')\n\n    def _add_protein_feature_edges(self, protein_id, entry):\n        features = entry.get(\'features\')\n        if features:\n            for feature in features:\n                feature_type = feature.get(\'type\')\n                if feature_type:\n                    # Use the robust feature_id created in _add_feature_nodes\n                    feature_description = feature.get(\'description\', \'\')\n                    feature_id = f\"{feature_type}_{hash(feature_description)}\"\n                    self.graph.add_edge(protein_id, feature_id, label=\'HAS_FEATURE\')\n\n    def _add_protein_keyword_edges(self, protein_id, entry):\n        keywords = entry.get(\'keywords\')\n        if keywords:\n            for keyword in keywords:\n                keyword_id = keyword.get(\'id\')\n                if keyword_id:\n                    self.graph.add_edge(protein_id, keyword_id, label=\'HAS_KEYWORD\')\n\n    def _add_protein_reference_edges(self, protein_id, entry):\n        references = entry.get(\'references\')\n        if references:\n            for reference in references:\n                reference_id = reference.get(\'citation\', {}).get(\'id\')\n                if reference_id:\n                    self.graph.add_edge(protein_id, reference_id, label=\'CITED_IN\')\n\n    def _add_protein_cross_reference_edges(self, protein_id, entry):\n        cross_references = entry.get(\'uniProtKBCrossReferences\')\n        if cross_references:\n            for cross_reference in cross_references:\n                database = cross_reference.get(\'database\')\n                if database:\n                    cross_reference_id = f\"{database}_{cross_reference.get(\'id\')}\"\n                    self.graph.add_edge(protein_id, cross_reference_id, label=\'CROSS_REFERENCE\')\n```\n"

async def main(class_out_path, ds_siongle_path, pre_processed):
    chat = model.start_chat()
    visitor = ControlAgent(chat=chat)
    ds_agent = FetchAgent(chat=chat, ds_path=ds_siongle_path)

    content = await ds_agent.process_ds()
    print("content recieved", type(content))
    scheme = await ds_agent.ds_scheme(content, json_file=True, pre_processed=pre_processed)
    print("scheme ", type(scheme))

    python_content = await ds_agent.ask(scheme)
    print("python_content ", type(python_content))

    #check = await visitor.check(original_prompt=ds_agent, content=python_content)
    await save_python_code(str(python_content), output_file=class_out_path)

def get_o_p(init_task, task=None, task_type=None, context=None, history=None):
    # operator prompt
    p = f"""You are a part of a two-ai-agent-system. 
    Your abolute goal is to finish the given task: {init_task}
    You have a venv available.
    Based on the provided type: {task_type}, bring the workflowa step forward to 
    complete the absolute task. If something isnt unclear, define just a improved
    Current task:
    {task}
    Decide your next step based on the given metadata:
    {context} # env info (content),...
    and history:
    {history}

    Define now:
    type: of the response to your partner, # e.g. execute, or write code
    task: definition of the follow up on task.
    """
    return p



    
    


