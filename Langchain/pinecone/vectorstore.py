import asyncio
import time

from asgiref.sync import sync_to_async
from openai import  RateLimitError
from Langchain.pinecone import Index, PineconeException
from Langchain.pinecone import ServerlessSpec, IndexList


from cachetools import TTLCache  # let save retunr values from methods/fuctions (for EVRY USER) to prevent unnecessary computing

#from Langchain import client
from ggoogle.send_mail.process import gmail_send_message
from ggoogle.storage.storage import GBucket
from Langchain.pinecone import pc
from gnn.embedder import get_embedder

vs_cache = TTLCache(maxsize=100, ttl=3600)  # Cache up to 100 entries for 1 hour

EMBEDDING_MODEL = [
    "text-embedding-ada-002",
    "text-embedding-3-small"
]
import datetime
import json
from typing import List,  Dict

import tiktoken
from langchain_core.documents import Document

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
)
from langchain_community.document_loaders.apify_dataset import ApifyDatasetLoader



class PrepareData:
    # jsonl input -> each line = doc
    def __init__(self):
        self.embedding_model = "text-embedding-3-small"

    def transfrorm_G_doc_or_embed(self, G):
        docs=[]
        for node_id, attrs in G.nodes(data=True):
            docs.append(
                Document(
                    page_content=json.dumps({"id": node_id, **attrs}),
                    metadata={"type": "node"}
                )
            )
        for src, trt, attrs in G.edges(data=True):
            docs.append(
                Document(
                    page_content=json.dumps({
                        "source": f"{src}",
                        "target": trt,
                        "relationship": attrs.get("relationship"),
                        **{k: v for k, v in attrs.items() if k != "relationship"}  # Correct dictionary unpacking
                    }),
                    metadata={
                        "type": "edge"
                    }
                )
            )
        return docs

    def dataset_mapping_function(self, dataset_item):
        try:
            metadata = {
                "source": dataset_item["url"],
            }

            print("metad:", metadata)
            # print("TEXT:", dataset_item["text"])
            optimized_text = dataset_item["text"].replace("\n", " ").strip()

            text = ' '.join(optimized_text.split()) + f'SOURCE": {dataset_item["url"]}'
            doc = Document(
                page_content=text,  # combined_text
                metadata=metadata  # metadata
            )
            print("LENCHJARS  DOC CONTENT:", len(doc.page_content))
            print("LEN CHATRS DOC METADATA:", len(doc.metadata))
            return doc
        except Exception as e:
            print("ERROR IN DATASET MAPPING FUNCTION:", e)
            return None

    def get_data_from_apify(self, dataset_id: str) -> List[Document] or None:
        try:
            print("GET DATA FROM APIFY...")
            loader = ApifyDatasetLoader(
                dataset_id=dataset_id,
                dataset_mapping_function=lambda dataset_item: self. dataset_mapping_function(dataset_item),
            )
            print("DOCUMENTS LOADED...")
            return loader.load()

        except Exception as e:
            print("ERROR WHILE LOADING DATA FROM APIFY:", e)
            return None

    def split_recoursive(self, data) -> List[Document] or None:
        try:
            print("SPLIT DOCS...")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=350,  # the model gets n characters at ones to eat . . .
                chunk_overlap=50,  # from every new chunk we put n chars from the old for better context
                separators=["\n"]
            )
            print("TEXT SPLITTER CREATED...")
            split_docs = text_splitter.split_documents(data)
            for doc in split_docs:
                print("SPLIT DOCS METADATA00:", len(doc.metadata), doc.metadata)
            return split_docs
        except Exception as e:
            print("ERROR WHILE SPLITTING DATA:", e)
            return None

    def split_character(self, data: Document):
        try:
            print("SPLIT DOCS BY CHARACTER...")
            text_splitter = CharacterTextSplitter(
                chunk_size=350,  # the model gets n characters at ones to eat . . .
                chunk_overlap=50,  # from every new chunk we put n chars from the old for better context
            )
            print("CHARACTER TEXT SPLITTER CREATED...")
            split_docs = text_splitter.split_documents([data])
            print("DOC SPLITTED BY CHARACTER INFO:", [(len(doc.page_content)) for doc in split_docs])
            return split_docs
        except Exception as e:
            print("ERROR WHILE SPLITTING DATA by character:", e)
            return None

    def get_token_len(self, doc):
        encoding = tiktoken.encoding_for_model(self.embedding_model)
        num_tokens_content = len(encoding.encode(doc.page_content))
        print("FINISHED TOKEN COUNT.", num_tokens_content)
        return num_tokens_content

    def split_manual(self, text, chunk_size=350):
        print("SPLIT CONTENT MANUALLY...")
        chunks = []
        if len(text) <= chunk_size:
            chunks.append(text)  # Single chunk if text is short enough
        else:
            for i in range(0, len(text), chunk_size):
                chunks.append(text[i : i + chunk_size])
        print("LEN MANUAL SPLIT CHUNKS:", [len(c) for c in chunks])
        print("CHUNKS LIST LEN:", len(chunks))
        return chunks

    def check_content_token_len(self, doc: Document, max_tokens: int = 8150):
        print("CHECK TOKEN LENGTH CONTENT-----------------------------------------------------------------------")
        final_docs = []
        try:
            num_tokens_content = self.get_token_len(doc)
            if num_tokens_content:
                if num_tokens_content <= max_tokens:
                    print(f"check_content_token_len token len first check is ok ({num_tokens_content})...")
                    return doc
                else:
                    print("CONTENT IS TOO LARGE FOR EMBEDDING MDOEL. SPLIT BY CHARACTERS AGAIN...")
                    split_docs: List[Document] or Document or None = self.split_character(doc)
                    if not split_docs:
                        print("SPLIT BY CHARACER WAS FAILED...")
                        # todo extend error handling
                        gmail_send_message(email="DEV_EMAIL", content=f"CONTENT: {doc.page_content} METADATA:{doc.metadata}", subject="DOC CONTENT CHECK")
                        return None

                    print(f"SPLIT DOC SUCCESSFUL...")
                    if isinstance(split_docs, Document):
                        print("SINGLE DOC WAS AGAIN RETURNED.. CHECK LEN...")
                        text_content: List[str] = self.split_manual(doc.page_content)
                        if isinstance(text_content, List) and len(text_content) > 0:
                            for chunk in text_content:
                                print(f"[isinstance(split_docs, Document)] APPEND DOC LEN {len(chunk)} TO DOC")
                                final_docs.append(Document(page_content=chunk, metadata=doc.metadata))
                        elif isinstance(text_content, str):
                            final_docs.append(Document(page_content=text_content, metadata=doc.metadata))
                        else:
                            gmail_send_message(email="DEV_EMAIL", content=f"Error in check_content_token_len  if isinstance(split_docs, Document): else: time:{datetime.datetime.now()}", subject="DOC CONTENT CHECK")

                    elif isinstance(split_docs, list):
                        print("SPLIT DOCS BY CHARACTER TYPE == LIST...")
                        for doc in split_docs:
                            print("CHECK TOKEN LEN AGAIN...")
                            num_tokens_content = self.get_token_len(doc)
                            if num_tokens_content:
                                print("CHECK FINISHED SUCCESSFULLY...")
                                if num_tokens_content <= max_tokens:
                                    print("CONTENT SIZE IS NOW OK...")
                                    final_docs.append(doc)
                                    continue
                                else:
                                    print("FAILED AGAIN THE TOKEN CHECK...")
                                    text_content: List[str] = self.split_manual(doc.page_content)
                                    for chunk in text_content:
                                        print(f"[isinstance(split_docs, list)] APPEND DOC LEN {len(chunk)} TO DOC")
                                        final_docs.append(Document(page_content=chunk, metadata=doc.metadata))

                    print("FINISHED PROCESSING. RETURN FINAL DCS:", len(final_docs), [len(doc.page_content) for doc in final_docs])
                    print("FMETADATA:", [len(doc.metadata) for doc in final_docs])
                    print("FMETADATA:", [len(doc.metadata["source"]) for doc in final_docs])

                    return final_docs

        except Exception as e:
            print("COULD NOT GET NUM OF TOKENS CAUS ERROR :", e)

    def _handle_split_failure(self, doc: Document):
        """Handles split failures by notifying the _b."""
        print("Split by character failed.")
        gmail_send_message(
            email="@",
            content=f"CONTENT: {doc.page_content}\nMETADATA:{doc.metadata}",
            subject="DOC CONTENT CHECK",
        )

    async def get_prepare_split_docs(self, dataset_id: str) -> List[Document] or None:
        loop = asyncio.get_running_loop()
        final_doc_list = []
        try:

            data: List[Document] or None = await loop.run_in_executor(None, self.get_data_from_apify, dataset_id)
            if not data:
                return None

            print("LOADED DATA LEN:", len(data))

            split_data: List[Document] or None = await loop.run_in_executor(None, self.split_recoursive, data)
            print("SPLIT DATA LEN:", len(split_data))

            # todo compress / short split docs

            for doc in split_data:
                document: Document or List[Document] or None = await loop.run_in_executor(None, self.check_content_token_len, doc)
                if isinstance(document, Document):
                    print("APPEND DOC...")
                    final_doc_list.append(document)
                elif isinstance(document, list):
                    print("EXTEND ALL DOCS...")
                    final_doc_list.extend(document)

            print("FINAL DATA LEN:", len(final_doc_list))
            return final_doc_list
        except Exception as e:
            print(f"An error occurred: {e}")
            return None


    def get_size_in_bytes(self, data):
        """Returns the size of the given data in bytes when serialized as a JSON string."""
        return len(json.dumps(data).encode('utf-8'))#

    def handle_doct_oversize(self, d:List[Dict], max_size_bytes:int=1):
        final_dict_list = []
        chunk_dicts = [] # dicts that sie is not greate then 5mb
        current_size = 0

        for item in d[0]:
            item_str = json.dumps(item)
            item_size = len(item_str.encode('utf-8'))

            if current_size + item_size > max_size_bytes:
                final_dict_list.append(chunk_dicts)
                chunk_dicts = []
                current_size = 0

            chunk_dicts.append(item)
            current_size += item_size

        if chunk_dicts and len(chunk_dicts) > 0:
            final_dict_list.append(chunk_dicts)

        return final_dict_list




    async def google_data_prepare(self, dataset_id) -> List[Dict]:
        split_docs = await self.get_prepare_split_docs(dataset_id=dataset_id)
        if not split_docs:
            print("SPLIT DOCS NOT FOUND..")
            return None
        upserter = VectorUpserter()
        embeds: List[Dict] = await upserter.process_embeddings(split_docs)
        print(f"Number of embeds created: {len(embeds)}")
        return embeds


class PCVectorStore:

    def __init__(self):
        self.prepare_data = PrepareData()

    def filter_index(self, name: str, index_list: IndexList) -> Index or None:
        print("SEARCH INDEX...")
        for index in index_list:
            if index.name == name:
                print("INDEX FROM NAME FOUND:", index)
                return index

        print("NO INDEX COULD BE FOUND...")
        return None


    def get_host_manually(self, name):
        try:
            info = pc.describe_index(name)
            host = info.host
            return host
        except Exception as e:
            print("ERROR DET INDEX DESCRIPTION:", e)
            return None



    def get_index(self, name_or_bot: str or None, name: str = "similarity") -> Index or None:
        print("GETTING INDEX...")
        # todo check the pc nfo save method
        try:
            return self.get_index_info(name, name_or_bot)
        except Exception as e:
            print("COULD NOT GET INDEX CAUSE THE FOLLOWING ERROR:", e)
            try:
                pc.create_index(
                    name=name,
                    dimension=1536,  # for case of use OpenAIEmbeddings()
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                return self.get_index_info(name, name_or_bot)
            except Exception as e:
                print("ERRR WHILE CREATING TH INDEX:", e)
            return None



    async def aget_index(self, name: str = "similarity"):
        """
        Get/Create index from name (if not exist new one is been created
        """

        print("Check for index...")
        indexes = await sync_to_async(pc.list_indexes)()
        if not indexes or len(indexes) == 0:
            print("NO EXISTING INDEX -> Create")
            try:
                await sync_to_async(pc.create_index)(
                    name=name,
                    dimension=1024,  # for case of use OpenAIEmbeddings()
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="gcp",
                        region="us-east-1"
                    )
                )
                print("Index created")
                indexes = await sync_to_async(pc.list_indexes)()

            except Exception as e:
                print("COULD NOT CREATE INDEX CAUSE THE FOLLOWING ERROR:", e)
                return None
        return await sync_to_async(self.filter_index)(name, indexes)


    async def get_pc_vector_store(
        self,
        bot,
        index_name: str = "similarity",
        vs_info: None = None,
        dataset_id: str or None = None,
    )-> None:
        print("GET PC VS...")

        index = await self.aget_index(index_name)  # todo get form host
        if index is None:
            return None

        print("TRY GET PCVS FROM NAMESPACE:", bot.name)

        if bot.name:
            try:
                if vs_info and vs_info.is_prepared:
                    vs=None
                    if vs is not None and isinstance(vs, int):
                        print("EXISTING VS FROM NAMESPACE SET. RETURN...")
                        return vs
                    elif isinstance(vs, str):
                        print("vs--------------------------------------------------:", vs)
                elif not vs_info or not vs_info.is_prepared and dataset_id:
                    vs = await self.create_new_vs_from_namespace(
                        namespace=bot.name,
                        dataset_id=dataset_id,
                    )
                    if vs is not None and isinstance(vs, int):
                        print("SET PC INFO INSTANCE TO TRUE FOR FURTHER REQUESTS...")
                        await sync_to_async(self.upgrade_pc_info)(bot)
                    print("RETURN VS...")
                    return vs
            except Exception as e:
                print("COULD FIND EXISTING VS FROM NAMESPACE ERROR:", e)

        return None


    ####

    async def get_idk_vs(self, bot_name, vs_info):
        vs = None
        idk_answers = [  # todo ausbauen
            "Ich kann die Informationen nicht finden",
            "Entschuldigung, ich kann dir damit nicht helfen",
            "Der context enthält die informationen nicht.",
        ]
        index = await sync_to_async(self.get_index)(bot_name, "similarity")

        if index is None:
            return None

        try:
            if bot_name != "testing":
                if vs_info and vs_info.idk_is_prepared:
                    print("EXISTING IDK VS FOUND...")
                    """vs = PineconeVectorStore(
                        namespace=f"idk-{bot_name}",
                        embedding=embeddings,
                        index_name=index.name
                    )"""
                    vs_info.idk_is_prepared = True
                    vs_info.save(update_fields=["idk_is_prepared"])
                else:
                    print("NO IDK VS SET, CREATE ANEW ONE...")
                    """vs = await PineconeVectorStore.afrom_texts(
                        texts=idk_answers,
                        namespace=f"idk-{bot_name}",
                        embedding=embeddings,
                        index_name=index.name
                    )"""
            else:

                """print("EXISTING IDK VS FOUND...")
                vs = PineconeVectorStore(
                    namespace=f"idk-{bot_name}",
                    embedding=embeddings,
                    index_name=index.name
                )"""

                print("NO IDK VS SET, CREATE ANEW ONE...")
                """vs = await PineconeVectorStore.afrom_texts(
                    texts=idk_answers,
                    namespace=f"idk-{bot_name}",
                    embedding=embeddings,
                    index_name=index.name
                )"""

            print("RETURN IDK VS...")
            return vs
        except Exception as e:
            print("COULD FIND EXISTING IDK VS FROM NAMESPACE ERROR:", e)

        print("CREATE NEW...")

        """vs = await PineconeVectorStore.afrom_texts(
            texts=idk_answers,
            index_name=index.name,
            embedding=embeddings,
            namespace="idk"  # filter here for some keywords
        )
        return vs"""

    async def handle_metadata_oversize(self, index: Index, namespace, split_docs, index_name):
        # todo if still too big,
        try:
            print("TRY RESIZE METADATA...")
            #
            #await self.short_string_simple(split_docs)
            print("TRY AGAIN CREATE VS FROM SHORTED DOCS...")
            vs = None
            """await PineconeVectorStore.afrom_documents(
                documents=split_docs,
                index_name=index_name, # the Index class has not attr name - just the py index function takes it as arg
                embedding=embeddings,
                namespace=namespace,  # filter here for some keywords
            )"""
            print("VS CREATION SECOND TRY SUCCESFULLY...")
            return vs
        except PineconeException as e:
            print("COULD NOT RESIZE THE METADATA:", e)
            try:
                print("DELETE THE WHOLE NAMESPACE")

                # Delete all vectors from the specified namespace
                #await self.short_string_simple(split_docs)
                print("index, split_docs, namespace", index, len(split_docs), namespace)

                """vs = await PineconeVectorStore.afrom_documents(
                    documents=split_docs,
                    index_name=index_name,
                    embedding=embeddings,
                    namespace=namespace,  # filter here for some keywords
                )"""
                return vs

            except Exception as e:
                print("COULD NOT CREATE VS FROM RESIZED METADATA AT THIRD TRY:", e)
        return None

    async def create_new_vs_from_namespace(self, namespace: str, dataset_id: str, index_name: str = "similarity"):
        index: Index = await sync_to_async(self.get_index)(namespace, index_name)
        if index is None:
            return None

        try:
            split_docs = await self.prepare_data.get_prepare_split_docs(dataset_id=dataset_id)
            if not split_docs:
                print("SPLIT DOCS NOT FOUND..")
                return None
            try:
                print("CREATE VS FROM DOCS...")
                # short
                #resizer = MetadataSizeHandler(split_docs=split_docs)
                #shorted_docs = await resizer.short_string_simple()
                #if not shorted_docs:
                #    return None

                # upsert
                upserter = VectorUpserter()
                success: bool or None = await upserter.upsert_process(split_docs, index, namespace)

                if isinstance(success, bool):
                    vs = None
                    """PineconeVectorStore(
                        namespace=namespace, embedding=embeddings, index_name=index_name
                    )"""
                    print("ASYNC VS FROM DOCS CREATED...")
                    return vs

            except PineconeException as e:
                print("ERROR WHUILE PREPARE THE DATA OCCURRED:", e)
                # todo @first short every data

                # Initialize the index
                #return await self.handle_metadata_oversize(index, namespace, split_docs)

            except Exception as e:
                print("ERROR WHUILE PREPARE THE DATA OCCURREDqq22222222:", e)
                return

        except Exception as e:
            print("ERROR WHUILE PREPARE THE DATA 555:", e)
        print("CREATE NEW VS FAILED...")
        return



###################################

embedder = get_embedder()


class VectorUpserter:
    def __init__(self, embedding_model: str = EMBEDDING_MODEL[1], batch_size: int = 10):
        self.embedding_model = embedding_model
        self.batch_size = batch_size
        self.bucket = GBucket("bestbrain")

    def create_embeddings(self, doc: Document, index: int, try_index:int=0) -> dict:
        if try_index >=5:
            return None
        try_index = 0
        try:

            embed=embedder.encode(json.dumps(
                {
                    "content":doc.page_content,
                    "meta":doc.metadata
                }
            ))
            """client.embeddings.create(
                input=doc.page_content, model=self.embedding_model
            )"""

            #source = doc.metadata["source"] if doc.metadata["source"] and len(str(doc.metadata).encode("utf-8")) <= 40960 else "unknown"

            return {
                "id": str(index),
                "values": embed,
            }

        except RateLimitError as e:
            print("RATElIMITeRROR:", e)
            time.sleep(5)
            try_index += 1
            return self.create_embeddings(doc, index, try_index)

        except Exception as e:
            print("ERROR WHILE GENERATE THE EMBEDDINS:", e)
            # todo right error handling
            try_index += 1

    async def process_embeddings(self, docs: List[Document]) -> list:
        print("START PROCESSING EMBEDDINGS...")
        embed_tasks = []
        for i, doc in enumerate(docs):
            if doc is not None:
                embed_tasks.append(asyncio.to_thread(self.create_embeddings, doc, i + 1))

        results = await asyncio.gather(*embed_tasks)
        print("FINISHED PROCESSING EMBEDDINGS TASK:", type(results))
        return results



    async def upsert_pc(
            self, embeds:List, pinecone_index: Index, namespace: str
    ) -> List[Dict] or None:
        """
        Creates embeddings, splits large batches, and upserts vectors to Pinecone.
        IF the namespace desnt exist, pc will create a new one
        """
        try:
            print("START PC EMBEDDING PROCESS...")

            batch_size = 100

            tasks = []
            for i in range(0, len(embeds), batch_size):
                batch_embeds = embeds[i : i + batch_size]
                task = asyncio.create_task(
                    sync_to_async(pinecone_index.upsert)(
                        vectors=batch_embeds, namespace=namespace, show_progress=True, batch_size=batch_size
                    )
                )
                tasks.append(task)

            await asyncio.gather(*tasks)  # Gather results
            print("UPSERT completed for all batches.")
            return True

        except Exception as e:  # Consider catching specific exceptions like PineconeException
            print(f"ERROR during upsert_process: {e}")
        return None


class MetadataSizeHandler:

    def __init__(self, split_docs):
        self.split_docs: List[Document] = split_docs

    def short_metadata(self, doc, max_length_bytes):
        for key, value in doc.metadata.items():
            if "source" not in key:
                doc.metadata[key] = ""
            byte_content = str(value).encode("utf-8")  # Convert value to string first
            print("KEY.", key, "BYTES.", len(byte_content))
            if len(byte_content) > max_length_bytes:
                doc.metadata[key] = byte_content[:max_length_bytes].decode("utf-8", "ignore")
                print("UPGRADED KEY.", key, "UPGRADED BYTES.", len(byte_content))

    async def short_string_simple(self):
        """Shortens page_content within each Document if it exceeds max_bytes."""
        print("SHORT DOCs...")
        try:
            max_lengths = [40000, 20000, 10000, 5000]

            for doc in self.split_docs:
                m_s = len(str(doc.metadata).encode("utf-8"))
                content_s = len(str(doc.page_content).encode("utf-8"))
                print("METADATA SIZE:", m_s)
                print("PAGE CONTENT SIZE:", content_s)
                print("SUMMAIZED SIZE:", content_s + m_s)
                if "text" in doc.metadata:
                    print("CUT METADATA...")
                    doc.metadata["text"] = ""

                for max_length in max_lengths:
                    if m_s <= max_length:
                        break

                    await sync_to_async(self.short_metadata)(doc, max_length)
                    metadata_bytes = len(str(doc.metadata).encode("utf-8"))

                    if metadata_bytes <= max_length:
                        print(f"METADATA REDUCED TO {max_length} BYTES")
                        break

                print(
                    f"METADATAAAAAAAA BEFORE PINECONE: {len(str(doc.metadata).encode('utf-8'))} {doc.metadata}"
                )
                return self.split_docs

        except Exception as e:
            print(f"ERROR WHILE SHORTING STRING SIMPLE: {e}")
            return None
    # todo 1 morgen get ehlp in ppinecone forum


    async def remove_stop_words(self):
        # todo
        return
"""
import asyncio
import numpy as np
import faiss
import random
import time

# Simulated synthetic cell processes
PROCESSES = ["gene_expression", "metabolism", "signaling", "protein_folding", "transport", "energy_regulation"]

# Number of stored states (simulated embeddings)
NUM_STATES = 10_000_000  # 10M past states
DIMENSIONS = 512  # Each embedding is 512-dimensional

# Initialize FAISS index for similarity search (L2 distance)
index = faiss.IndexFlatL2(DIMENSIONS)
stored_states = np.random.rand(NUM_STATES, DIMENSIONS).astype(np.float32)  # Fake data
index.add(stored_states)  # Load into FAISS

async def similarity_search(query_embedding):
    D, I = index.search(np.array([query_embedding]), k=1)  # Top-1 closest match
    return I[0][0], D[0][0]  # Return closest state index and distance

async def process_cell_function(process_name):
    while True:
        query_embedding = np.random.rand(DIMENSIONS).astype(np.float32)  # Random current state
        closest_state, distance = await similarity_search(query_embedding)
        print(f"[{process_name}] Retrieved state {closest_state} (distance: {distance:.4f})")
        await asyncio.sleep(random.uniform(0.001, 0.01))  # Simulating process time

async def synthetic_cell_cpu():
    tasks = [process_cell_function(name) for name in PROCESSES]
    await asyncio.gather(*tasks)

# Run the synthetic cell CPU
asyncio.run(synthetic_cell_cpu())


"""
"""
moleküle vorschlagen -> suchen dauert lang
gt o gan


-> spätr pipe für alle G zu data, jedes data repräsentiert node im Graphen (sozusagen graph im graph)






"""