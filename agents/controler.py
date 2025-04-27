import asyncio

from vertexai.generative_models import FunctionDeclaration

from gnn.processing.layer.gene.gene_layer import get_gem


class ControlAgentUtils:

    def __init__(self):
        pass


    async def get_function_declarations(self):
        list_tables_func = FunctionDeclaration(
            name="check_content",
            description="Provide a status ",
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "'final' || 'edit'",
                    },
                    "result": {
                        "type": "object",
                        "description": "The adapted code"
                    }
                },
                "required": [
                    "dataset_id",
                ],
            },
        )
        return [list_tables_func]

    async def check(self, prompt, code):
        return f"""
        Check the provided python CLASS and the PROMPT that instructs a LLM to generate it. 
        Focus highly on correctness of the mplementation and improve the code if needed.
        Return nothing but the (adapted) production ready python CLASS 

        PROMPT:
        check({prompt})

        CLASS:
        {code}

        """


class ControlAgent:
    def __init__(self, chat):
        self.chat = chat
        self.utils = ControlAgentUtils()
        self.role = """
        You are a control agent, checking the work of other agents. YOu work allways from higher hierarchy. 
        """


    async def check(self, original_prompt, content):
        loop = asyncio.get_event_loop()

        steps = await loop.run_in_executor(None, get_gem,f"""
                {await self.utils.check(prompt=original_prompt, code=content)}
                 """"", self.chat
        )
        return steps