"""
The hyde process simply generates a hypothetical document of the asked question.
This document then wil embedded to a datastructure with the question to generate the answer from it

pros: faster, efficient
cons: complex

-> maybe connect with current workflow?

"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from Dashboard.bot.Langchain import llm
from Dashboard.bot.Langchain.retrievers.multi_query_retriever_config import get_prompt_template

HYDE_PROMPT = """Please write a scientific paper passage to answer the question
Question: {question}
Passage:"""



def gen_answer_hyde(question: str, retriever) -> str or None:
    print("HYDE PROCESS STARTED...")
    try:
        hyde_template = get_prompt_template(HYDE_PROMPT)
        print("PROMPT CREATED:", hyde_template)
        generate_docs_for_retrieval = (
                hyde_template | llm | StrOutputParser()
        )

        retrieval_chain = generate_docs_for_retrieval | retriever
        print("PROMPT CREATED:", hyde_template)

        retrieved_docs = retrieval_chain.invoke({"question": question})
        print("HYDE DOCS RECEIVED:", retrieved_docs)


        template = """Answer the following question based on this context:
        
        {context}
        
        Question: {question}
        """

        prompt = ChatPromptTemplate.from_template(template)

        final_rag_chain = (
            prompt
            | llm
            | StrOutputParser()
        )

        response = final_rag_chain.invoke({"context": retrieved_docs, "question": question})
        print("GENERATED RESPONSE HYDE:", response)

        return response
    except Exception as e:
        print("ERROR AT HYDE PROCESS:", e)
        return None
