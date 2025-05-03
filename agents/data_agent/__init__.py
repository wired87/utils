"""
Get urls for datasets (dj class based view
fetch ds
gather first 10mb of the file
extract elements to get an understanding of the structure and possible variations
use an ai agent to recognize possible nodes and relationships between them and xternal sources (generally marked with identiieres) -> returns all nodes and edges objects in json format
a second agent compares the result and give tipps for improvement till hes confirmesd with the result
a pre written py script receives the output from the agent, creates nodes, edges and embeddings of both and creates new layers from it
tech satack:
- not neo4j!
- _google services
- rest is your choice


building docker:
write a script that can be executed in py that creates a docker file from a spcific direction in the project and give some params inside for the script that gets exectuted then

build docker to kubernetes / workbench -> run
"""