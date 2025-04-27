"""
This process is very well described in the individually.png image under extracted.langchain

Difference to Decomposition:
After creating the queries we let generate for each docuemnt "stack" that has been picked an answer.
This answers will the be used to generate the final answer. ( just try it out )

pros : instead of composition process is this async runnable + customizable
This process + normla way incl reranking:
1. generate queries
2. get docs for each
3. generate answer from docs for each
4. append answer to Document structure
5. rerank docs ( if answer was idk, it will become a lower rank ) -> get highest 6
6. short them
7. generate answer from it

pros : async ( mostly part )
cons: ?,
todo: improve that process with more own ideas

"""

from typing import List

from langchain import hub
from langchain_core.documents import Document


rag_prompt = hub.pull("rlm/rag-prompt")


""" very good results! but slow
retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 4,
                "fetch_k": 40  # play araound
            },
            search_type="mmr"  # || similarity_score_threshold
        )
        docs: List[Document] = await retriever.ainvoke(query)
"""




"""
        
retriever = vectorstore.as_retriever(
    search_kwargs={
        'score_threshold': 0.7,  # just docs with a score over .8 will get returned
        "k": 4
    },
    search_type="similarity_score_threshold",  # just say here to filter for threshold score
    cache_policy="lru"
) #   # for now just rerank integrated. later short also
"""
""" --->get_docs_from_query_optimized
# todo before in context: short the docs
answer = (rag_prompt | llm | StrOutputParser()).invoke({
    "context": docs,
    "question": query
})
print("ANSWER GENERATED:", answer) --->

answer_list.append(answer)

answer_doc = Document(page_content=answer, metadata={}) --->
docs.append(answer_doc)

print("DOC LIST EXTENDED...")
---> """