import asyncio
import time

from asgiref.sync import sync_to_async
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from datetime import date

from Langchain import llm


def get_formatted_date():
    """
        Year: year
        Month: month
    """
    today = date.today()
    formatted_date = f"Year: {today.year}\nMonth: {today:%B}"  # %B for full month name
    return formatted_date


def get_prompt():
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                TEMPLATE
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

def get_main_template(format_date):
    return f"""
                   You are an support assistant for a website.
                    You will answer short and precise.
                   You will find the right answer for the question if you search on the right place!
                   
                    Context:
                    Current date: {format_date}""" + """\n\n{context}"""
TEMPLATE = get_main_template(get_formatted_date())
PROMPT = get_prompt()

def get_chat_template():  # todo
    print("GENERATE THE CHAIN...")
    try:
        prompt = PROMPT
        print("PROMPT GENERATED...")
        chain = (prompt | llm | StrOutputParser())  # await sync_to_async(create_stuff_documents_chain)(llm=llm, prompt=prompt)
        print("CHAIN GENERATED...")
        return chain
    except Exception as e:
        print("ERROR GENERATE THE DOC CHAIN:", e)


"""
Verify data accuracy and synthesize information. 
Always include the provided webpage for reference.
"""
"""
history = ChatMessageHistory()
async def create_history(
        question,
        client_id,
        user,
        user_bot,
        user_plan
):

    try:
        print("ADDING MESSAGES TO THE CONVERSATION...")
        start = time.time()

        conversation: Conversation = await handle_conv(client_id, user, user_bot, user_plan)
        all_messages = await sync_to_async(list)(conversation.qa.all())

        print("ALL MESSAGES SET:", all_messages)
        for message_block in all_messages:
            print("ADDING QUESTION TO THE CONV:", message_block.question)
            await sync_to_async(history.add_user_message)(message_block.question or "")

            print("ADDING ANSWER TO THE CONV:", message_block.answer)
            await sync_to_async(history.add_ai_message)(message_block.answer or "")

        await sync_to_async(history.add_user_message)(question)


        print("FINAL CONV HISTORY:", history)
        end = time.time()
        print("CREATE HISTORY TIME:", end - start)
        return history
    except Exception as e:
        print("COULD NOT ADD THE CONV, CAUSE E:", e)"""
