import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from Langchain import llm
from openai_api import client

MULTY_QUERY_PROMPT = """You are an AI language model assistant. Your task is to generate four 
                different versions of the given user question in german to retrieve relevant documents from a vector 
                database. By generating multiple perspectives on the user question, your goal is to help
                the user overcome some of the limitations of the distance-based similarity search.
                Provide these alternative questions separateed by new lines. Original question: {question}"""

DECOMPOSE_PROMPT = """You are a helpful support assistant for a website that 
generates multiple sub-questions related to an input question. 
The Input is all times related to the content of the website \n
The goal is to break down the input into a set 
of sub-problems / sub-questions that can be answers in isolation. \n
Generate multiple search queries related to: {question} \n
Output (3 queries):"""


MULTI_TWO = """You are an AI language model assistant. Your task is to generate four 
                different versions of the given user question in german to retrieve relevant documents from a vector 
                database. By generating multiple perspectives on the user question, the goal is, that the answer of 
                your question provides the requested information. You will be look exactly for the requested information.
                If the input contains just a single word (e.g. "kontakt"), tells you theat the user just wants that 
                provided information.
                Provide these alternative questions separateed by new lines. Original question: {question}"""


def get_prompt_template(template: str):
    return ChatPromptTemplate.from_template(template)


############## LANGCHIAN WAY
def get_multy_query_langchain_way() -> list[str] or None:
    prompt_template = get_prompt_template(MULTY_QUERY_PROMPT)
    try:
        generate_queries = (
                prompt_template
                | llm
                | StrOutputParser()
                | (lambda x: x.split("\n"))
        )

        print("GENERATED QUERIES:", generate_queries)

        return generate_queries

    except Exception as e:
        print(f"COULD NOT GENERATE ULTI QUERIES IN  LANGCHAIN WAY ( E:{e} )...")

################## DECOMPOSE FOR DECOMPOSITION

TEMPLATE = get_prompt_template(MULTY_QUERY_PROMPT)





###############  MY OWN WAY
def get_multy_query(question: str):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": """You are an AI language model assistant. Your task is to generate four 
                different versions of the given user question in german to retrieve relevant documents from a vector 
                database. By generating multiple perspectives on the user question, your goal is to help
                the user overcome some of the limitations of the distance-based similarity search. 
                Provide these alternative questions in the following JSON format:
                {
                    "answer": ["answer1", "answer2", "answer3", "answer4"]
                }
                """},
                {"role": "user", "content": f"Original question: {question}"}
            ]
        )

        response = response.choices[0].message.content
        if isinstance(response, str):
            response = json.loads(response)
        print("RESPONSE ANSWER:", [res for res in response["answer"]])
        return response["answer"]

    except Exception as e:
        print("MULTI QUERY EXCEPTION OCCURRED:", e)
