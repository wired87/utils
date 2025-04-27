import torch
from transformers import BioGptForCausalLM, AutoTokenizer

from gnn.bridge.prompt import TEST_SEQUENCE

model = BioGptForCausalLM.from_pretrained(
    "microsoft/biogpt",
    attn_implementation="sdpa",
    torch_dtype=torch.float16)


tokenizer = AutoTokenizer.from_pretrained("microsoft/biogpt")


if __name__ == "__main__":
    functionalities = "dendrite"# input("start sequence (comma separated)>>>")


    p=f"""
    Suggest coding genes for the wanted FUNCTIONALITIES.
    Implement your genes of choice in the provided SEQUENCE.
    return nothing but the adapted and extended sequence.
    FUNCTIONALITIES: {functionalities} \n\n
    SEQUENCE: {'Hello'} 
    """# todo später einschliff von input für graph model (p->convert->gm)
    embeddings = tokenizer(p, return_tensors="pt", truncation=True, max_length=1024)
    outputs = model(**embeddings)
    logits = outputs.logits
    # Get the predicted token indices for the most likely tokens
    predicted_token_ids = torch.argmax(logits, dim=-2)

    # Decode the token indices back into human-readable text
    decoded_text = tokenizer.decode(predicted_token_ids[0], skip_special_tokens=False)

    # Print the result
    print("Generated Text:")
    print(decoded_text)
