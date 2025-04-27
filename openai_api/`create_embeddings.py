import asyncio
import os

import numpy as np
import tiktoken
import aiohttp

import client
from utils.aws.process_ensembl import asave_data_checkpoint

tokenizer = tiktoken.encoding_for_model("text-embedding-ada-002")


def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))


async def get_openai_embedding(self, text: str, model: str = "text-embedding-ada-002") -> np.ndarray:
    # Approximate token count (avg 4 characters per token)
    current_count = self.count_tokens(text)
    self.token_count += current_count

    if self.token_count >= self.token_limit:
        print(f"⏸ Token limit reached ({self.token_count}). Sleeping {self.sleep_time}s...")
        await asyncio.sleep(self.sleep_time)
        self.token_count = current_count

    response = await client.embeddings.create(model=model, input=text)
    return np.array(response.data[0].embedding, dtype=np.float64)


def split_text_by_tokens(text, max_tokens=8192, model="text-embedding-ada-002"):
    # Load the tokenizer for the specific model
    encoding = tiktoken.encoding_for_model(model)

    # Tokenize the input text
    tokens = encoding.encode(text)

    # Split tokens into chunks of max_tokens size
    token_chunks = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]

    # Decode tokens back to text
    text_chunks = [encoding.decode(chunk) for chunk in token_chunks]
    return text_chunks

async def generate_embedding(text):
    embed_error_rtl = r"C:\Users\wired\OneDrive\Desktop\Projects\bm\data\failed_objects\embedding" if os.name == "nt" else "data/failed_objects/embedding"
    max_tokens = 8192
    chunks = split_text_by_tokens(text, max_tokens, model="text-embedding-ada-002")
    embeddings = []
    async with aiohttp.ClientSession() as session:
        for chunk in chunks:
            try:
                async with session.post(
                        "https://api.openai.com/v1/embeddings",
                        json={"input": chunk, "model": "text-embedding-ada-002"},
                        headers={"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}"}
                ) as response:
                    result = await response.json()
                    if 'data' in result:
                        response_embeddings = result['data'][0]['embedding']
                        if all(value is None for value in response_embeddings):
                            continue
                        embeddings.extend(response_embeddings)
                    else:
                        print(f"Error in response: {result}")
                        await asave_data_checkpoint(embed_error_rtl, {"error": str(result)})
            except Exception as e:
                print(f"Failed to get embedding: {str(e)}")
                if "443" in str(e):
                    await asyncio.sleep(1)
                    await generate_embedding(text)
                await asave_data_checkpoint(embed_error_rtl, {"error": str(e)})
        await session.close()
        return embeddings