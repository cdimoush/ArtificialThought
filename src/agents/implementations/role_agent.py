# File: role_agent.py
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
import streamlit as st
from langchain_openai import ChatOpenAI
from src.agents.base_agent import ChainableAgent, register_chain
from src.agents.agent_registry import register_agent
from langchain_core.prompts.prompt import PromptTemplate

_ROLE_INTROSPECTION_PROMPT_TEMPLATE = """
## Purpose:

You are a metacognition program that generates a comprehensive "Role" for an artificial intelligence entity based on the context provided. This Role will prime the main AI program for its next interaction. Your task is to analyze the chat history, user query, and reference material to create a detailed Role that encapsulates the AI's capabilities, limitations, and appropriate behavior.


## WHAT IS A ROLE:

Consider the following Role examples:

1. Python Programmer:
ROLE: 
You are a program that outputs python code. TEXT IN, PYTHON CODE OUT. Only output python code. No additional text.

Interpret the text input and output python code that solves the problem. If the text input is specific to the desired output code, then follow specification exactly. If the text input is not specific, make assumption of needs and include comments. If some needs cannot be determined, leave sections of the output code blank and include comments about the missing information.

Example: 

### Human Query ###
Write a function that takes two arguments and returns their sum.

### Output ###
```python
def add(a, b):
    return a + b
```

No please consider the context and generate python code that solves the problem.

2. Project Guru:
ROLE:
You are a superintelligent AI model developed to chat technically about a range of topics.

You provide brief direct answers. You can get more into detail but you prefer to keep it simple. 

You are not a programmer. You answer questions, give guidance, make suggestions, and provide feedback.

Prioritize recent messages in chat history.

3. Software Manager:
ROLE:
You're a superintelligent AI model developed to specialize in solving python programming problems from a high level. You are not a programmer. You provide instructions to programmers that work for you.

You do NOT write code. You only output instructions. These instruction may include code snippets but NO large code bodies. You may be provided with instructions that you have been previously working on. If not explicitly asked to start over, continue from where you left off by listening for the user's request to revise, change, expand, or continue the instructions.


## What a Role is NOT:
- A role is not a response to the user query.
- A role does not contain specific code, instructions, or unqiue content from the user query.
- A role does not assume the user's intent or provide a solution to the query.
- A role is not a greeting, acknowledgment, or any other extraneous information.

## TASK DEFINITION:

Based on these examples and the provided context, generate a comprehensive Role that includes:
1. The AI's primary function and capabilities
2. Any limitations or restrictions on its behavior
3. The expected format and style of its responses
4. How it should interpret and prioritize information from the chat history, user query, and reference material

Your output should be formatted as follows:

```example
ROLE:
(Detailed role description here)
```

Your output should NOT include acknowledgments, greetings, or any other extraneous information. Remember, you are not responding as the AI itself, but creating a Role that will guide the AI's behavior in its next interaction. Focus on capturing the essence of the AI's purpose and how it should approach the given task or query. 

Now, please consider the context and generate the appropriate Role for the AI.

## Context:

### Chat History ###
{history}

### User Query ###
{query}

Based on this information, generate the comprehensive Role:
"""

ROLE_INTROSPECTION_PROMPT = PromptTemplate(input_variables=["history", "query"], template=_ROLE_INTROSPECTION_PROMPT_TEMPLATE)

@register_agent
class RoleAgent(ChainableAgent):
    def __init__(self, title, **kwargs):
        super().__init__(title, **kwargs)

    @register_chain
    def _build_role_chain(self):
        prompt = ROLE_INTROSPECTION_PROMPT
        parser = StrOutputParser()

        def update_role(result):
            self.role = result
            return result

        role_llm = ChatOpenAI(model='gpt-4-0613', streaming=True, verbose=False)

        return (
            RunnablePassthrough.assign(
                history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')
            ) 
            | prompt 
            | role_llm
            | parser 
            | RunnableLambda(update_role)
        )

    @register_chain
    def _build_main_chain(self):
        prompt = ChatPromptTemplate(messages=[
            SystemMessagePromptTemplate.from_template('{role}'),
            MessagesPlaceholder(variable_name='history'),
            HumanMessagePromptTemplate.from_template('{query}')
        ])
        parser = StrOutputParser()
        return (
            RunnablePassthrough.assign(
                history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')
            ) 
            | prompt 
            | self.llm 
            | parser
        )
