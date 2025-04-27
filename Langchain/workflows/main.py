
from Dashboard.bot.Langchain.classes.load_prepare_data import PrepareData
from Dashboard.bot.Langchain.pinecone.vectorstore import PCVectorStore


prepare_data = PrepareData()
create_vs = PCVectorStore()


async def gen_answer(
    chat_history,
    rerank_docs,
    document_chain
):
    print("START ANSWER GENERATION...")
    try:
        # Load every message from the conversation Model in the chat history

        response = await document_chain.ainvoke(
            {
                "messages": chat_history.messages,
                "context": rerank_docs,
            }
        )

        print(f"ANSWER: {response}")
        return response
    except Exception as e:
        print("COULD NOT GENERATE THE ANSWER CAUSE THE FOLLOWING ERROR:", e)
        return None



""" ID: HIER KLAPÜPT ALLES
        optimized_docs = await get_optimized_from_queries_and_docs(question, await vectorstore)

        if not optimized_docs:
            return None

        elif isinstance(optimized_docs, str):
            return optimized_docs

        document_chain = await sync_to_async(get_chat_template)()
        
         async def check_cache_entries(self, question, cache_name, user, plan):
        print("CHECKING CACHE ENTRIES...")
        start = time.time()
        # check cache
        cache_tools = RedisSemanticCacheTools(
            cache_name=cache_name,
            user=user,
            async_call=True
        )

        result = await cache_tools.acheck_input(question, plan)

        end = time.time()

        print("SEARCH CACHE TIME:", end - start)

        if result:
            return {
                    "status_code": 200,
                    "response": result
                }
def gen_answer(
        conversation: Conversation,
        dataset_id: str,
        question: str,
        bot_name: str
):

    vectorstore = create_vs.get_pc_vector_store(
        namespace=bot_name,
        dataset_id=dataset_id,
    )

    if not vectorstore:
        return None

    # todo implement cache

    try:

        optimized_docs = asyncio.run(get_optimized_from_queries_and_docs(question, vectorstore))

        if not optimized_docs:
            return None
        elif isinstance(optimized_docs, str):
            return optimized_docs

        document_chain = get_chat_template()

        # Load every message from the conversation Model in the chat history
        chat_history = create_history(conversation, question)

        response = document_chain.invoke(
            {
                "messages": chat_history.messages,
                "context": optimized_docs,
            }
        )

        print(f"ANSWER: {response}")
        return response
    except Exception as e:
        print("COULD NOT GENERATE THE ANSWER CAUSE THE FOLLOWING ERROR:", e)
        return None

"""


