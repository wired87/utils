"""
Normally in rag and multi query processing we would filter for each question soe docs.
This docs we put then together, filter them for the best n and give it to the llm.
#

When doing decompression,
we first take the filtered docs from reformulated query 1 and generate an answer from it.
Then we take this answer and put it into the Document list from query 2.
This process we repeat for every generated question and get the final answer.

The process is well described in decomposition.png cbf@ extracted.langchain

Cons: this may take longer, the normal workflow of filtering the best is just thorugh differnet ways acessible
Pros: may cleaner answers
"""
from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser

from Dashboard.bot.Langchain import llm
from Dashboard.bot.Langchain.retrievers.multi_query_retriever_config import decompose_query, get_prompt_template

PROMPT = """
Here is the question you need to answer:
\n --- \n {question} \n --- \n

Here is additional context relevant to the question:

\n --- \n {context} \n --- \n

Use the above context and any background question + answer to answer the question: \n {question}
"""

TEMPLATE = get_prompt_template(PROMPT)




def format_question_pair(question, answer):
    return f"Question{question} \n Answer:{answer}\n\n".strip()


def get_answer_question(questions, retriever):
    Q_A_PAIRS = ""
    print("GEN ANSWERS FROM QUESTIONS ( DECOMPOSE )...")
    index = 1
    answer = ""
    try:
        for query in questions:
            rag_chain = (
                {
                    "context": itemgetter("question") | retriever,
                    "question": itemgetter("question"),
                    "q_a_pairs": itemgetter("q_a_pairs")
                }
                | TEMPLATE
                | llm
                | StrOutputParser()
            )

            answer = rag_chain.invoke(
                {
                    "question": query,
                    "q_a_pairs": Q_A_PAIRS
                }
            )
            print(f"ANSWER {index}: {answer}")
            qa_pair = format_question_pair(query, answer)
            Q_A_PAIRS = Q_A_PAIRS + "\n---\n" + qa_pair
            index += 1

        print(f"Q_A_PAIRS: {Q_A_PAIRS}")
        return answer
    except Exception as e:
        print("ERROR WHILE PROCESSING get_answer_question CAUSE ERROR:", e)


async def parallelized_decompose_process(question: str, vectorstore):
    try:
        gen_queries = await decompose_query(question)
        return get_answer_question(gen_queries, vectorstore.as_retriever())
    except Exception as e:
        print("ERROR DECOMPOSE PROCESS:", e)


