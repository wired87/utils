import asyncio
import re


from langchain_community.utilities.apify import ApifyWrapper

from dotenv import load_dotenv

load_dotenv()

apify = None #ApifyWrapper()

# todo evtl datenscutz ausbeziehen
# todo irgendiwe das modell anpassen (temp usw.)

def get_contact_data(text):
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    phone_pattern = re.compile(r'\+?\d{2}[\d -]{8,}\d')
    emails = email_pattern.findall(text)
    phones = phone_pattern.findall(text)
    contact_info = {
        "emails": emails,
        "phones": phones
    }
    return contact_info


"""
contact_info = get_contact_data(text)
f"Contact Emails: {', '.join(contact_info['emails']) if contact_info['emails'] else 'No emails found'}\n" \
f"Contact Phones: {', '.join(contact_info['phones']) if contact_info['phones'] else 'No phones found'}\n\n" \
"""





# 'canonicalUrl": dataset_item.get("canonicalUrl", ""),
#           "referrerUrl": dataset_item.get("referrerUrl", "")'
#                    f"Date: {dataset_item.get('date', 'No date')}\n" \1






"""
async def get_queries_from_question(question: str, vectorstore) -> List[Document] or None:
    print("GET QUERIES FROM QUESTION: ", question)
    retriever = MultiQueryRetriever.from_llm(  # MultiQueryRetriever will generate 5 versions of the inputted question
        vectorstore.as_retriever(),
        # "Value of chinks that may have the biggest chance to include the wanted answer"
        llm=llm,
        include_original=True
    )

    try:
        queries: List[Document] = await retriever.ainvoke(question)
        print("QUERIES CREATED: ", queries)

        return queries

    except Exception as e:
        print("ERROR CREATING THE QUERIES   :", e)
            get_docs_from_ensemble_retriever(
        question=query,
        retriever=vectorstore.as_retriever(),
        docs=docs)
            
"""


async def get_docs_from_query(query, vectorstore):
    return vectorstore.similarity_search(query)


async def optimize_docs(queries: list, vectorstore):
    print("QUERIES RECEIVED IN OPTIIZED DOCS:", queries)

    task = [get_docs_from_query(query, vectorstore) for query in queries]
    print("TASKS RECEIVED IN OPTIIZED DOCS:", task)

    all_docs = await asyncio.gather(*task)
    print("ALL SEARCHED DOCS: ", all_docs)

    flattened_docs = [doc for sublist in all_docs for doc in sublist]

    print("ALL FLATTEND DOCS: ", flattened_docs)

    return flattened_docs











"""
 filtered_question = filter_question_with_embeddings(
    query.page_content,
    vectorstore.as_retriever()
)
print("FILTERED QUESTION:", filtered_question)
"""

"""
todo

- cache layer with Self-Query (caching for performing similar functions without having to go through the pipeline everytime)
- Contextual Compression with a DocumentCompressionPipeline
- LLMLingua for optimization of token usage
- A Cross-Encoder is also very useful to enhance relevenacy and reliability. 

- Implementing algorithms like the Matryoshka Retriever can boost speed significantly while maintaining relevancy. 

- Remember you will need to implement not only RAG but actual computer science concepts as well. 
- Beware of pre-mature optimization, you can always speed things up later.
- Such as algorithms, caching, threading, queues, etc. To really get the performance of something that is production ready.
- Then you will have to look at other aspects - such as prompt engineering



MULTIRETRIEVER
retriever = MultiQueryRetriever.from_llm(  # MultiQueryRetriever will generate 5 versions of the inputted question
        vectorstore.as_retriever(k=10),
        # "Value of chinks that may have the biggest chance to include the wanted answer"
        llm=llm,
        include_original=True
    )
    docs = retriever.ainvoke(question)  # gets list of docs by all different queries


    
    docs = retriever.get_relevant_documents(question) # gets list of docs by all different queries
    print("LEN RETRIEVER:", len(docs))
    for doc in docs:
        print("RETRIEVER DOCS:", doc)

    return docs

BASE RETRIEVER:  retriever = vectorstore.as_retriever(
        k=10)  # "Value of chinks that may have the biggest chance to include the wanted answer"
    print("RETRIEVER INVOKE RESULT: ",retriever.invoke(question))
    return retriever.invoke(question)


def creat_vectorstore_get_retriever(data, question):
    # todo production vectorstore db alternative ( chat below)

    print("CREATE VECTORSTORE...")
    all_docs = []
    vectorstore = Chroma.from_documents(
        documents=data,
        embedding=embeddings  # before blank
    )

    try:
        queries = get_chain_queries(question)
        print("ADD QUERIES:", queries, "TO VECTOR STORE...")
        retriever = vectorstore.as_retriever()
        retriever.ainvoke(question)
        compressed_docs = filter_question_with_embeddings(question, retriever)

    except Exception as e:
        print("Error:", e)


    for query in all_queries:
        document_retriever = vectorstore.as_retriever(k=4)
        all_docs.append(document_retriever.invoke(query))

"""

# todo config arg from invoke (BaseRetrievier) methhod
"""


def creat_vectorstore_get_retriever(data, question):
    print("CREATE VECTORSTORE...")

    vectorstore = Chroma.from_documents(
        documents=data,
        embedding=OpenAIEmbeddings(chunk_size=1) # before blank
    )

    retriever = MultiQueryRetriever.from_llm( # MultiQueryRetriever will generate 5 versions of the inputted question
        vectorstore.as_retriever(k=10)
        # "Value of chinks that may have the biggest chance to include the wanted answer"
    )

    return retriever.invoke(question)
    
    """

"""

def get_split_text():
    print("SPLIT THE DOCS..")
    return TextSplitter(
        chunk_size=100,
        chunk_overlap=50  # before 20 ->  check
    )


def get_embeddings():
    print("GET EWMBEDDINGS...")
    embeddings = OpenAIEmbeddings(
        deployment="your-embeddings-deployment-name",
        model="your-embeddings-model-name",
        openai_api_base="https://your-endpoint.openai.azure.com/",
        openai_api_type="azure",
    )

def create_data_process(data_url):
    print("BEGIN CRAWL THE DATA...")
    try:
        loader = apify.call_actor(
            actor_id="apify/website-content-crawler",
            run_input={"startUrls": [{"url": data_url}]},
            dataset_mapping_function=lambda item: dataset_mapping_function(item),
        )
        apify_model = ApifyDatasetModel.objects.create(
            dataset_id=loader.dataset_id,
        )
        apify_model.save()
        print("APIFY MODEL CREATED:", apify_model)

        bot_data_model = BotData.objects.create(
            apify=apify_model,
            url=data_url
        )
        print("BOT DATA MODEL CREATED:", bot_data_model)

        bot_data_model.save()
        return bot_data_model
    except Exception as e:
        print("ERROR WHILE GETTING THE LOADER AND CRATING TH DATASET:", e)
    return None
    


For data where the relationship between data points is very important a GraphDB is better than a 
VectorDB GraphDB(they are often used together). 

Using Multi-Query and Self-Query with a VectorDB and a lite-weight and cheap LLM, 
such as LLAMA or Mistral from groq, is very important.  
Cohere have a fantastic 32B model perfect for RAG applications, though not as fast as Groq, it is faster than OpenAI.

You will have to develop a pipeline that suits your needs.
There are just some strategies. There are plenty, and the infrastructure design that you implement is based on your requirements. 



for now, get something working within an accuracy and relevancy you think is useful.
For example - adding re-ranking and matryoshka to your current project would go a long way to increasing the relevancy of retrieved chunks.

 Pinecone and Weviate are really good. Ive had great success with Redis' vector offerings, 
 and i have recently started to enjoy working with MongoDB's vector offering. 

gotcha 🙂 Well, you will have to decide what level of accuracy and relevancy is required. 
It tends to be that the more relevant your chunks, 
the more latency (the more computation you need to do). So there is a trade off.

As an example - when i implement multi-query i tend to use parallelism. 
As, synchronously running a DB lookup for every query takes time. 
If you have the same type of query x5 - you are now O(log5) in the best-case scenario. Maybe O5.


So that when frequently used queries come in, 
i have cached the retrieved chunks to prevent having to do a lookup at all. 



later
-- https://www.youtube.com/watch?v=sgnrL7yo1TE
"""
