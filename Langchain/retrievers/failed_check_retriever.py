from langchain_core.output_parsers import StrOutputParser

from Dashboard.bot.Langchain import get_llm_openai
from Dashboard.bot.Langchain.retrievers.multi_query_retriever_config import get_prompt_template

CHECK_FAILED_TEMPLATE = f"""
You are a specialist in classifying given texts.

You will receive a  question and a anwer to that question.

You will classify the answer in either

section: "FAILED" - if the given answer does not possibly answer the question (e.g. content like "I don't know)

or section "SUCCESS" - If the given answer could answer the question correctly.

You will just return the name of one of the sections ("FAILED" OR "SUCCESS") nothing else.


"""
TEMPLATE = get_prompt_template(CHECK_FAILED_TEMPLATE)
LLM = get_llm_openai(
    model="gpt-3.5-turbo",
    temp=0,
    max_t=50
)


def failed_content_check(question: str, answer: str) -> list[str] or None:
    print("DECOMPOSE QUERIES...")
    try:
        query: str = f"Question: {question} \n Answer: {answer}"

        chain = (TEMPLATE | LLM | StrOutputParser())

        classification = chain.invoke({"question": query})
        print("CLASSIFICATION RESPONSE:", classification)

        return classification
    except Exception as e:
        print("COULD NOT GET :", e)

    return None
