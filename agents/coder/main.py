"""

pip install ray spacy paramiko docker boto3
"""

import os
import time
import ray
import openai
import spacy
import networkx as nx
import paramiko
import docker
import boto3
import subprocess
import logging

# Initialize Ray for parallel execution
ray.init(ignore_reinit_error=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load NLP Model
nlp = spacy.load("en_core_web_sm")

# OpenAI API Key (set your environment variable)
openai.api_key = os.getenv("OPENAI_API_KEY")

# AWS Configuration (if using cloud instances)
ec2 = boto3.client("ec2")


def refine_instruction(raw_instruction):
    """Refine and categorize instructions using GPT-4"""
    prompt = f"Break down the following instruction into logical steps:\n{raw_instruction}"
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": prompt}]
    )
    return response['choices'][0]['message']['content']


@ray.remote
def execute_task(task):
    """Execute a task using an AI coding agent."""
    logging.info(f"Executing task: {task}")
    code_prompt = f"Generate a Python script to accomplish the following task:\n{task}"
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": code_prompt}]
    )
    code = response['choices'][0]['message']['content']

    with open("generated_script.py", "w") as f:
        f.write(code)

    return "generated_script.py"


@ray.remote
def run_script(script_path):
    """Run the generated script inside a Docker container."""
    logging.info(f"Running script: {script_path}")
    client = docker.from_env()
    container = client.containers.run(
        "python:3.9",
        command=["python", f"/workspace/{script_path}"],
        volumes={os.getcwd(): {'bind': '/workspace', 'mode': 'rw'}},
        detach=True
    )
    logs = container.logs().decode()
    container.stop()
    return logs


@ray.remote
def debug_script(script_path):
    """Perform automated debugging on a failed script."""
    logging.info(f"Debugging script: {script_path}")
    result = subprocess.run(["pylint", script_path], capture_output=True, text=True)
    errors = result.stderr
    if errors:
        fix_prompt = f"Here is the Python script:\n{open(script_path).read()}\n\nHere are the errors:\n{errors}\nFix these issues and improve the script."
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": fix_prompt}]
        )
        fixed_code = response['choices'][0]['message']['content']
        with open(script_path, "w") as f:
            f.write(fixed_code)
    return script_path


# Main Execution Pipeline
def run_ai_coding_agent(user_input):
    logging.info("Starting AI Coding Agent")
    refined_steps = refine_instruction(user_input)
    steps = refined_steps.split("\n")

    task_refs = [execute_task.remote(step) for step in steps]
    script_paths = ray.get(task_refs)

    for script in script_paths:
        logs = run_script.remote(script)
        output = ray.get(logs)
        if "error" in output.lower():
            script = debug_script.remote(script)
            ray.get(script)
            logs = run_script.remote(script)
            output = ray.get(logs)

    logging.info("All scripts executed successfully")
    return "Pipeline Completed!"


if __name__ == "__main__":
    instruction = "Build an API that scrapes weather data and provides a forecast model."
    run_ai_coding_agent(instruction)
