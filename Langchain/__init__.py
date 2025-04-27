"""import os

from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from openai import OpenAI



# OPEN AI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))











"""
import os

from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
import dotenv

dotenv.load_dotenv()

ALL_MODELS = [
    "gpt-4-turbo",
    "gpt-4o", #lower costs,
    "gpt-3.5-turbo"
]


LANGCHAIN_EMBEDS = OpenAIEmbeddings(chunk_size=350, openai_api_key=os.environ.get("OPENAI_API_KEY"))  # before at 1

llm = ChatOpenAI(
    model=ALL_MODELS[1],
    temperature=0,
     api_key=os.environ.get("OPENAI_API_KEY"),
    # max_tokens=100,
    model_kwargs={
        "top_p": .5,  # 0 - 1
        "frequency_penalty": .5,  # 0 = many word repetitions 1 = More diverse language
        "presence_penalty": 0  # add new words to the generated text 0 means no. -> reduces the creativity
    }
)