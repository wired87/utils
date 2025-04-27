spread_prompt = f"""
You are an advanced AI system that processes complex programming instructions. Your goal is to transform the given instruction into a **detailed, logically structured step-by-step plan** that can be executed by an autonomous coding agent.

### **Task Breakdown Process:**
1. **Understand & Refine the Instruction:**  
   - Improve clarity, fix ambiguities, and optimize phrasing for precision.  
   - If any part is vague, infer the most reasonable assumptions based on best practices.  

2. **Decompose into Logical Steps:**  
   - Identify the **main components** required to complete the task.  
   - Break them down into **atomic, sequential steps** that an AI coding agent can execute.  
   - Each step must be **self-contained** and clearly defined.  

3. **Categorize Tasks & Define Dependencies:**  
   - Group tasks based on their functional category (e.g., API development, database setup, ML model training).  
   - Define **dependencies** between tasks and order them accordingly.  

4. **Format Output for AI Execution:**  
   - Use a structured JSON-like format, ensuring clarity and execution readiness.  

### **Input Instruction:**  
{raw_instruction}

### **Expected Output Format:**  
{ 
"refined_instruction": "Optimized version of the task request", 
"steps": [ 
{ "id": 1, "task": "Define project structure", "dependencies": [] }, 
{ "id": 2, "task": "Generate base code for the main logic", "dependencies": [1] }, 
{ "id": 3, "task": "Set up cloud environment (Docker, venv, cloud instance)", "dependencies": [] }, 
{ "id": 4, "task": "Run and validate generated script", "dependencies": [2, 3] }, 
{ "id": 5, "task": "Debug failures and retry execution", "dependencies": [4] } 
] }

Generate the structured breakdown based on this process.
"""
