async def gen_answer(
    rerank_docs,
    document_chain,
    query
):
    print("START ANSWER GENERATION...")
    try:
        # Load every message from the conversation Model in the chat history

        response = await document_chain.ainvoke(
            {
                "message": query,
                "context": rerank_docs,
            }
        )

        print(f"ANSWER: {response}")
        return response
    except Exception as e:
        print("COULD NOT GENERATE THE ANSWER CAUSE THE FOLLOWING ERROR:", e)
        return None