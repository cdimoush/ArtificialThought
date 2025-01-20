Artificial Thought
================== 
Exploring augmentation of workflow with LLMs and the Langchain library.

Main Ideas:
1. Custom Roles and Prompt Templates
2. Linear Chains
3. Rag Agents

---
# Using Artificial Thought
This is a streamlit application that can be deployed from file `app.py`.

```bash
streamlit run app.py
```

## Agent Registration and Instantiation

In the `ArtificialThought` application, agents are registered and instantiated through a combination of configuration files and class decorators. The `agents.yaml` file defines the configuration for each agent, specifying details like the model and type. The `AgentRegistry` class maintains a registry of agent classes, which are registered using the `@register_agent` decorator. When an agent is needed, the `AgentHandler` reads the configuration, retrieves the appropriate class from the registry, and creates an instance of the agent.

### Example: Adding a Pinecone Agent

To add a Pinecone agent to the application, follow these steps:

1. **Define the Agent in `agents.yaml`:**

   ```yaml
   pinecone_agent:
     model_provider: "openai"
     model: "gpt-4o-mini"
     type: "pinecone"
     role: "Agent is hooked up to pinecone vector db and uses RAG to answer user queries"
   ```

2. **Implement the Agent Class:**

   Create a new file, `pinecone_agent.py`, in the `src/agents/implementations` directory and define the agent class:

   ```python
   from src.agents.base_agent import ChainableAgent, register_chain
   from src.agents.agent_registry import register_agent

   @register_agent
   class PineconeAgent(ChainableAgent):
       def __init__(self, title, **kwargs):
           super().__init__(title, **kwargs)
           # Initialize Pinecone-specific components here

       @register_chain
       def _build_chain(self):
           # Define the chain logic for the Pinecone agent
           pass
   ```

3. **Ensure the Agent is Registered:**

   The `@register_agent` decorator automatically registers the `PineconeAgent` class with the `AgentRegistry`, making it available for instantiation based on the configuration in `agents.yaml`.

By following these steps, the Pinecone agent will be integrated into the application and can be selected and used like any other agent.

---

# Log
## 2025-1-20
Cleaning up the project for 2025 and making a Rag Agent for the Isaac Sim / Isaac Lab documentation.
