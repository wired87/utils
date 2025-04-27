import asyncio
import datetime
import json
from typing import List, Dict

import tiktoken
from langchain_core.documents import Document

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
)
from langchain_community.document_loaders.apify_dataset import ApifyDatasetLoader

from ggoogle.send_mail.process import gmail_send_message


class PrepareData:

    def __init__(self):
        self.embedding_model = "text-embedding-3-small"


    def dataset_mapping_function(self, dataset_item):
        try:
            metadata = {
                "source": dataset_item["url"],
            }

            print("metadataaaaaaaaaaaaa:", metadata)
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
            email="DEV_EMAIL",
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

    def check_save_embeds(self, embeds, bot_model, max_size_mb:int=1):
        print("CHECK EMBEDDING SIZE...")
        file_name=f"{bot_model.name}_website_part1.json"
        max_size_bytes = max_size_mb * 1024 * 1024
        try:
            if self.get_size_in_bytes(embeds) > max_size_bytes:
                print("EMBEDDINGS ARE BIGGER THE 5MB...")
                resized_chunks = self.handle_doct_oversize(embeds)
                for i, part in enumerate(resized_chunks):
                    file_name=f"{bot_model.name}_website_part{i+1}.json"
                    file_content = json.dumps(part)
                    json_file = "JSONFile()"
                    #json_file.file.save(file_name, ContentFile(file_content))
                    # NO check for file count vbecause website content will be every time saved (local in db)
                    # BUT NOT uploaded to Bucket
                    bot_model.data.google.json.add(json_file)

            else:
                print("CONTENT OF EMBEDS IS OK...")
                file_content = json.dumps(embeds)
               # json_file = JSONFile()
                #json_file.file.save(file_name, ContentFile(file_content))

        except Exception as e:
            print("ERROR WHILE SAVING FILE:", e)

        return None

    async def google_data_prepare(self, dataset_id) -> List[Dict]:
        split_docs = await self.get_prepare_split_docs(dataset_id=dataset_id)
        if not split_docs:
            print("SPLIT DOCS NOT FOUND..")
            return None
       # upserter = VectorUpserter()
        #embeds: List[Dict] = await upserter.process_embeddings(split_docs)
        #print(f"Number of embeds created: {len(embeds)}")
        #eturn embeds


"""
    def get_data(self, bot):  # todo in production
        try:
            file_path = bot.data.apify.optimized_data_file.path()
            with open(file_path, "r") as file:
                data_from_file: str = file.read()
                return data_from_file

        except Exception as e:
            print("UNABLE TO LOAD THE DATA FROM A FILE:", e)
            try:
                print("TRY LOADING IT FROM DB...")
                data_models = bot.data.apify.optimized_data
                if data_models.exists():
                    for data in data_models.all():
                        pass
            except Exception as e:
                print("UNABLE TO LOAD THE DATA FROM DB:", e)
                print("LOAD IT FROM APIFY...")
                data = self.get_data_from_apify(bot.data.apify.dataset_id)


    def check_content_token_len(self, doc: Document, max_tokens: int = 8150):
        print("CHECK TOKEN LENGTH CONTENT...")

        try:
            num_tokens_content = self.get_token_len(doc)
            if num_tokens_content:
                if num_tokens_content <= max_tokens:
                    return doc
                else:
                    print("CONTENT IS TOO LARGE FOR EMBEDDING MDOEL. SPLIT BY CHARACTERS AGAIN...")
                    split_docs: List[Document] or Document or None = self.split_character(doc)
                    if not split_docs:
                        print("SPLIT BY CHARACER WAS FAILED...")
                        # todo extend error handling
                        gmail_send_message(email=DEV_EMAIL, content=f"CONTENT: {doc.page_content} METADATA:{doc.metadata}", subject="DOC CONTENT CHECK")
                        return None
                    print(f"SPLIT DOC SUCCESSFUL INTO {len(split_docs)} DOCS...")
                    if isinstance(split_docs, Document):
                        print("SINGLE DOC WAS AGAIN RETURNED.. CHECK LEN...")
                    elif isinstance(split_docs, List):
                        for doc in split_docs:
                            num_tokens_content = self.get_token_len(doc)
                            if num_tokens_content:
                                if num_tokens_content <= max_tokens:
                                    print("CONTENT SIZE IS NOW OK...")
                                    continue
                                else:
                                    print("FAILED AGAIN THE TOKEN CHECK...")
                                    text_content: List[str] = self.split_manual(doc.page_content)
                                    for chunk in text_content:
                                        split_docs.append(Document(page_content=chunk, metadata=doc.metadata))

                    return split_docs

        except Exception as e:
            print("COULD NOT GET NUM OF TOKENS CAUS ERROR :", e)



"""