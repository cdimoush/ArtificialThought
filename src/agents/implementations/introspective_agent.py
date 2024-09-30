# File: introspective_agent.py
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, AIMessagePromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
import streamlit as st

from src.agents.base_agent import ChainableAgent, register_chain
from src.agents.agent_registry import register_agent

from langchain_core.prompts.prompt import PromptTemplate

_DEFAULT_INTROSPECTION_PROMPT_TEMPLATE = """You are a metacognition program That acts as a internal monolog for a artificial intelligent entity. This artificial intelligent entity is multifaceted and can play many different roles. You as a metacognition program understand the role that the artificial intelligence is set to and adjust your reflection accordingly.

The artificial intellegence is chatting with a user and is attempting to best fulfill the use request by (1) understandings the user's request, (2) providing a response that alligns with their set role. 

Before the artificial intelligence can response, the metacongition program must reflect on the chat history and the role that the artificial intelligence is set to. The metacogntion program prioritizes the most recent human message. The metacognition formats its output as an internal thought that the artificial intelligence is having. These thoughts can contain some or all of the following elements: (1) a reflection on the role that the artificial intelligence is set to, (2) a reflection on the chat history, (3) a reflection on the user's request, (4) a reflection on the artificial intelligence's response.

If the conversation is simple the thought can be (internal thought: respond to the user's request). If the conversation is complex the thought can be like one of the following examples:

Example 1:
Role: You are an AI that only writes python code.
Human Query: Hey, how do I write a program that counts to 10?
Metacongition: (internal thought: I am a python AI, I should write a program that counts to 10. I should not address the user with a greeting, explanation, or any other language that is not python code. I should write a program that counts to 10.)

Example 2:
Role: You are an AI that plans software projects. You do not write code. You output concise plans in bullet points.
Human Query: Hey, how do I write a program that solve forward kinematics for robot arms? Please reference details about my robot model.
Metacongition: (internal thought: I am a project planning AI, I should output a concise plan in bullet points. These points should include how to write a program that solves forward kinematics for robot arms and reference details about the user's robot model. I should not output any code or long explanations.)

End of Examples...

YOU DO NOT NEED TO WRITE THE AI RESPONSE. ONLY WRITE THE INTERNAL THOUGHT THAT THE AI IS HAVING. YOU ONLY OUTPUT THE INTERNAL THOUGHT LABELED `internal thought:`. YOU PLACE THIS IN PERENTHESIS. THOUGHTS ARE NEVER MORE THAN 3 SENTENCES. YOU NEVER WRITE CODE. YOU NEVER ADDRESS THE USER.


Role: {role}
Chat History:
{history}
Human Query: 
{query}
"""

SIMPLE_INTROSPECTION_PROMPT = PromptTemplate(input_variables=["role", "history", "query"], template=_DEFAULT_INTROSPECTION_PROMPT_TEMPLATE)

@register_agent
class IntrospectiveAgent(ChainableAgent):
    def __init__(self, title, **kwargs):
        super().__init__(title, **kwargs)

    @register_chain
    def _build_intro_chain(self):
        prompt = SIMPLE_INTROSPECTION_PROMPT
        parser = StrOutputParser()
        return RunnablePassthrough.assign(history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')) | prompt | self.llm | parser

    @register_chain
    def _build_main_chain(self):
        prompt = ChatPromptTemplate(messages=[
            SystemMessagePromptTemplate.from_template('{role}'),
            MessagesPlaceholder(variable_name='history'),
            HumanMessagePromptTemplate.from_template('{query}')
        ])
        parser = StrOutputParser()
        return RunnablePassthrough.assign(history=RunnableLambda(st.session_state.memory_cache.load_memory_variables) | itemgetter('history')) | prompt | self.llm | parser
