import asyncio
import gzip
import os
import re
import shutil
from typing import List

import requests

from bm.settings import BASE_DIR
from utils.utils import GraphUtils


class EncodeProcessor:
    """
    Huge amount of data
    """
    def __init__(self, ):
        super().__init__()
        self.g_utils = GraphUtils(table_name="encode")
        self.enc_base= r"https://www.encodeproject.org/"
        self.json_format = "?format=json"
        self.brain_experiment_graph = "https://www.encodeproject.org/report/?type=Experiment&status=released&control_type%21=%2A&replicates.library.biosample.donor.organism.scientific_name=Homo+sapiens&biosample_ontology.organ_slims=brain&limit=all"
        # todo repair mount path and set here
        self.enc_base_dir = os.path.join(BASE_DIR, "data", "encode")


    def get_out_paths(self, file_id):
        output_gz = os.path.join(self.enc_base_dir, f"{file_id}.fasta.gz")
        output_fasta = os.path.join(self.enc_base_dir, f"{file_id}.fasta")
        return output_gz, output_fasta


    def get_file_url(self, experiment_id):
        return f"{self.enc_base}{experiment_id}{self.json_format}"

    def get_download_url(self, href):
        return f"{self.enc_base}{href}"

    def download_unpack_gz(self, file_id, download_url):
        """Downloads and extracts a FASTA file from ENCODE project."""
        output_gz, output_fasta= self.get_out_paths(file_id)

        # Download the file
        response = requests.get(download_url, stream=True)
        if response.status_code == 200:
            with open(output_gz, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            print(f"Downloaded: {output_gz}")
        else:
            print(f"Failed to download {download_url}")
            return

        # Extract the gzip file
        with gzip.open(output_gz, 'rb') as f_in, open(output_fasta, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        print(f"Extracted: {output_fasta}")

        # Read and parse the extracted FASTA content
        return output_fasta

    def extract_fasta_schema(self, output_fasta):
        fasta_schema = {}
        all_values = []
        with open(output_fasta, 'r') as f:
            for i, line in enumerate(f):
                if line.startswith('>'):
                    match = re.match(r">(\S+)\s?(.*)", line.strip())
                    for ind, m in enumerate(match.groups()):
                        if m not in fasta_schema:
                            line = next(f, None)
                            values = re.match(r">(\S+)\s?(.*)", line.strip())
                            #append schema:values
                            all_values.append({k:v for k,v in zip(list(match.group()), values)})
                            #set schema
                            value = values[ind]
                            fasta_schema[m if ind != 0 else "id"] = type(value)
        print("Extracted FASTA Schema:")
        for entry in fasta_schema:
            print(entry)
        return fasta_schema, all_values

    async def handle_single_experiment(self, experiment_id):
        """
        Go

        :param experiment_id:
        :return:
        """
        data_structure = await self.g_utils.utils.download_json_content(self.get_file_url(experiment_id))
        href = data_structure.get("href")
        # save mem
        data_structure = None
        href= self.get_download_url(href)
        data_url = await self.g_utils.download_and_extract_fasta(file_id=experiment_id, download_url=href)

        fasta_schema, all_values = self.extract_fasta_schema(data_url)
        spanner_schema = {k: self.g_utils.get_spanner_type(v) for k,v in fasta_schema.items()}

        self.g_utils.add_columns_bulk(table_name=str(experiment_id), attrs=spanner_schema)




        self.g_utils.batch_process_rows(
            table_name=str(experiment_id),
            id_column_name="id",
            rows=all_values,
        )






    async def handle_files(self, entry):
        tasks = []
        for f in entry["files"]:
            await self.handle_single_experiment(f["@id"])
            tasks.append(self.g_utils.utils.download_json_content(self.get_file_url(f["@id"])))
        results = await asyncio.gather(*tasks)
        # example results element https://www.encodeproject.org/files/ENCFF688JFN/?format=json
        results = await asyncio.gather()

    async def working_brain_graph(self, data=None):
        """
        From url: "https://www.encodeproject.org/report/?type=Experiment&status=released&control_type%21=%2A&replicates.library.biosample.donor.organism.scientific_name=Homo+sapiens&biosample_ontology.organ_slims=brain&limit=all"
        -> includes all Brain experiments (1207)
        """
        if not data:
            data = await self.g_utils.utils.download_json_content(self.brain_experiment_graph)

        print("START WORKING ENCODE EXPERIMENT")
        for i in data.get("@graph"):
            # print("i", i)
            gid = i.get("accession")

            experiment_files:List=i.get("files")
            #await self.handle_files()

            #print("Adding Exp node")
            await self.g_utils.add_node(
                attrs=dict(
                    id=gid,
                    type="experiment",  # Handle missing @type
                    sub_type="encode_brain_experiment_dataset",
                    parent=[],
                    child=[],
                    **i
                ))

            xrefs = i.get("dbxrefs")
            # print("WORKING XREF", xrefs)
            if xrefs:
                eattrs = {"rel": "xref", "type": "xref"}
                for xref in xrefs:
                    await self.g_utils.add_edge(src=gid, trt=xref, attrs=eattrs)






    async def main(self, data):
        await self.working_brain_graph(data)