from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from Langchain import llm
from Langchain.chat_preparation import get_formatted_date
from datetime import date


def get_formatted_date():
    """
        Year: year
        Month: month
    """
    today = date.today()
    formatted_date = f"Year: {today.year}\nMonth: {today:%B}"  # %B for full month name
    return formatted_date


def get_main_template(format_date):
    return f"""
                   Your task is to answer suggest gene ontology term documents based o the message.
                    You will answer short and precise.
                   You will find the right answer for the question if you search on the right place!

                    Context:
                    Current date: {format_date}""" + """\n\n{context}"""

def get_prompt():
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                get_main_template(get_formatted_date())
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

def get_chat_template():  # todo
    print("GENERATE THE CHAIN...")
    try:
        prompt = get_prompt()
        print("PROMPT GENERATED...")
        chain = (prompt | llm | StrOutputParser())  # await sync_to_async(create_stuff_documents_chain)(llm=llm, prompt=prompt)
        print("CHAIN GENERATED...")
        return chain
    except Exception as e:
        print("ERROR GENERATE THE DOC CHAIN:", e)