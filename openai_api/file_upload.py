from openai import OpenAI
client = OpenAI()


def upload(from_path=None, from_str_content=None, purpose=None):
    if from_path is not None:
        content=open(from_path, "rb")
    else:
        content = from_str_content
    file = client.files.create(
        file=content,
        purpose=purpose or "betse_sim_data"
    )
    print("File created")
    return file.id



def query_file(files:list or str, prompt):
    if isinstance(files, str):
        files = [files]

    content = []
    for file in files:
        content.append(
            {
                "type": "file",
                "file": {
                    "file_id": file.id,
                }
            },
        )
    content.append(
        {
            "type": "text",
            "text": prompt,
        },
    )
    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ]
    )
    response=completion.choices[0].message.content
    print("response", response)
    return response