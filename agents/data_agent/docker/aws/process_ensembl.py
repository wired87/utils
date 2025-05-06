import json

import aiofiles
import aiohttp
import boto3

from aiolimiter import AsyncLimiter

from utils.gnn.processing.model.main import asave_data_checkpoint

"""Mared issues: 
chromosome HSCHR6_MHC_MCF_CTG1

"""

BASE_END = ";expand=1"
ENSMBL_FAILURE = []
# Load environment variables from the .env file
ACCESS_ID="e3MtOEpYNMaqx+fmHGJCAKk8MrtwDTgFl5GWF53X"
SECRET_KEY="AKIAZQBRZAHPYY7FVF5W"
REGION="eu-central-1"
BUCKET="genexfabric"

# Access environment variables
aws_access_key_id = ACCESS_ID
aws_secret_access_key = SECRET_KEY
region_name = REGION
bucket_name = BUCKET
import asyncio

async def puffer(runs):
    print(f"Runs value before increment: {runs}")
    if runs is not None and runs % 15 == 0:  # Ensure `runs` is not None before using it
        await asyncio.sleep(1)
    runs = (runs or 0) + 1  # Default to 0 if `runs` is None
    return runs

async def aread_json_content(path, mode="r"):
    async with aiofiles.open(path, mode=mode) as file:
        content = await file.read()
    return json.loads(content)

rate_limiter = AsyncLimiter(max_rate=10, time_period=1)


async def fetch_data(url, session, check=None, post=None):
    if post:
        async with rate_limiter:  # Automatically enforces rate limit
            async with session.post(url, data=post["data"], headers=post["headers"]) as response:
                check = await puffer(check)
                return await response.json() if response.headers.get('Content-Type', '').startswith('application/json') else await response.text()
    else:
        async with rate_limiter:
            async with session.get(url) as response:
                check = await puffer(check)
                return await response.json() if response.headers.get('Content-Type', '').startswith('application/json') else await response.text()


async def abase_request(url: str, session: aiohttp.ClientSession, request_type: str = "json", post: dict or None = None, check=None):
    try:
        response = await fetch_data(url, session, check=check, post=post)
        if isinstance(response, aiohttp.ClientResponse):
            if response.status == 200:
                if request_type == "json":
                    content = await response.json()
                elif "Too Many Requests" in response:
                    await asyncio.sleep(1)
                    return await abase_request(url, session, request_type, post)
                else:
                    content = await response.text()
                print("Response ok, return content...")
                return content
            elif response.status in (429, 443):
                retry_after = int(response.headers.get("Retry-After", 5))
                print("Rate limit exceeded, sleep 1m, then try again...")
                await asyncio.sleep(retry_after)
                return await abase_request(url, session, request_type, post)
            else:
                print(f"Failed to fetch URL {url}: {response.status}")
                return None
        else:
            return response
    except Exception as e:
        print("Error doing abase_request request:", e)
        await asyncio.sleep(3)
        return await abase_request(url, session, post=post)



async def handle_sequence(session, item, url, runs):
    tasks = []

    sequence_types = [
        "genomic",
        "cds",
        "cdna",
        "protein"
    ]

    for sequence_type in sequence_types:
        tasks.append(abase_request(f"{url}type={sequence_type}", session, check=runs))
    results = await asyncio.gather(*tasks)

    sequence_dict = dict(
        genomic=results[0]
        if ("No" not in results[0] and isinstance(results[0], dict) and results[0].get("error") is None)
        else "unknown",
        cds=results[1]
        if ("No" not in results[1] and isinstance(results[1], dict) and results[1].get("error") is None)
        else "unknown",
        cdna=results[2]
        if ("No" not in results[2] and isinstance(results[2], dict) and results[2].get("error") is None)
        else "unknown",
        protein=results[3]
        if ("No" not in results[3] and isinstance(results[3], dict) and results[3].get("error") is None)
        else "unknown"
    )

    print("sequence_dict extracted...")
    item["sequences"] = sequence_dict





















async def phenotypes(url, item, session, runs):
    content = await abase_request(url, session, check=runs)
    print("Phenotype content:", content)
    if content:
        item["phenotypes"] = content
    else:
        item["phenotypes"] = []



def get_item_endpoints(gene_id):
    base = "https://rest.ensembl.org"
    return {
        "gene_info": f"{base}/lookup/id/{gene_id}?content-type=application/json;",
        "sequence": f"{base}/sequence/id/{gene_id}?content-type=application/json;", #ok
        "homology": f"{base}/homology/id/human/{gene_id}?content-type=application/json;",
        "phenotype": f"{base}/phenotype/gene/human/{gene_id}?content-type=application/json;",
    }


async def filter_sequence(input_data):
    # Split the input by lines
    print("input_data", input_data)
    lines = input_data.strip().split("\n")
    # Filter out lines that start with ">"
    sequence_lines = [lines.remove(line) for line in lines if line.startswith(">")]
    print("Filtered sequences", sequence_lines)
    # Join the sequence lines into a single string
    sequence = "".join(sequence_lines)
    return sequence


async def ahandle_exon(url, pheno_url, session, exon, runs):
    tasks = []
    seq_region_name = exon.get("seq_region_name", None)
    if seq_region_name:
        exon["chromosome"] = seq_region_name
        exon.pop("seq_region_name")
    print("chromosome", exon["chromosome"])

    tasks.append(handle_sequence(session, exon, url, runs))
    #tasks.append(phenotypes(pheno_url, exon, session, runs))
    await asyncio.gather(*tasks)




async def ahandle_transcripts(trans, url, pheno_url, session, runs):
    exon_tasks = []
    seq_region_name = trans.get("seq_region_name", None)
    if seq_region_name:
        trans["chromosome"] = seq_region_name
        trans.pop("seq_region_name")

    #exon_tasks.append(phenotypes(pheno_url, trans, session, runs))

    exons = trans.get("exons", [])
    print("Got exons: ", len(exons))
    if exons and len(exons) > 0:
        for exon in exons:
            exon_tasks.append(ahandle_exon(url, pheno_url, session, exon, runs))
        await asyncio.gather(*exon_tasks)


async def handle_single_gene_transcripts(gene_item, session, url, pheno_url, runs):
    tasks = []
    transcripts = gene_item.get("transcripts", [])
    print("Got transcripts: ", len(transcripts))
    if transcripts and len(transcripts) > 0:
        for trans in transcripts:
            tasks.append(ahandle_transcripts(trans, url, pheno_url, session, runs))
        await asyncio.gather(*tasks)


async def handle_first_level_single_gene_item(gene_item, session, runs):
    tasks = []
    gene_id = gene_item["id"]
    print("Working Gene", gene_id)
    if gene_id:
        endpoints = get_item_endpoints(gene_id=gene_id)
        tasks.append(handle_sequence(session, gene_item, f"{endpoints['sequence']}", runs))
        tasks.append(handle_single_gene_transcripts(gene_item, session, f"{endpoints['sequence']}", f"{endpoints['phenotype']}", runs))
        tasks.append(phenotypes(f"{endpoints['phenotype']}", gene_item, session, runs))
        #tasks.append(ahandle_gene_ino(session, gene_item, endpoints["gene_info"]))
        await asyncio.gather(*tasks)
    else:
        ENSMBL_FAILURE.append(gene_item["id"])

async def fetch_additional_info(gene_item, session, runs):
    seq_region_name = gene_item.get("seq_region_name", None)
    if seq_region_name:
        gene_item["chromosome"] = seq_region_name
        gene_item.pop("seq_region_name")
    await handle_first_level_single_gene_item(gene_item, session, runs)


async def gather_gene_data():
    traget = r"ens_filtered.json"
    test_url = r"ensemble.json"
    genome = await aread_json_content(test_url)
    runs = 1
    async with aiohttp.ClientSession() as session:
        #for gene_item in genome["genes"][:1]:
        # C:\Users\wired\OneDrive\Desktop\Projects\aws_to_bucket\extract_data\data\filtered_data\ensembl_single.json
        await fetch_additional_info(genome, session, runs)
        await asave_data_checkpoint(
            path=traget,
            content=genome
    )


s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
    )
traget = r"ens_seq.json"

if __name__ == "__main__":
    content = asyncio.run(gather_gene_data())
    s3.upload_file(
        Filename=traget,  # Local file name
        Bucket=bucket_name,  # S3 bucket name
        Key="ens_seq.json",  # S3 key (path in the bucket)
    )




