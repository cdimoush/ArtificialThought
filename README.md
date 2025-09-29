# 🧠 Artificial Thought

**A sophisticated multi-agent LLM orchestration platform built from the ground up**

Transform your workflow with intelligent AI agents that seamlessly integrate RAG, custom prompting, and modular chain architectures. Built on Streamlit and LangChain, this isn't just another chatbot—it's a comprehensive agent management system designed for extensibility and power.

## 🚀 What Makes This Special

- **🔧 Dynamic Agent Registry**: Hot-swappable AI agents with zero-config registration system
- **🧩 Chainable Architecture**: Compose complex reasoning workflows with decorative chain builders
- **🎯 RAG-Powered Intelligence**: Vector database integration with Pinecone for contextual responses
- **⚡ Real-time Streaming**: Live response streaming with custom callback handlers
- **🎨 Modular UI Components**: Clean separation between logic, presentation, and state management

---

## 🎮 Quick Start

```bash
streamlit run app.py
```

Select your agent, ask questions, and watch the magic happen.

## 🏗️ Architecture Deep Dive

### The Agent Registry System
The crown jewel of this architecture—a decorator-driven agent registry that automatically discovers and wires AI agents:

```python
@register_agent
class PineconeAgent(ChainableAgent):
    @register_chain
    def rag_chain(self):
        return (
            RunnablePassthrough.assign(context=get_context_tool)
            | RunnablePassthrough.assign(history=self.fetch_memory())
            | RAG_PROMPT
            | self.llm
            | StrOutputParser()
        )
```

**Key modules that make the magic happen:**

### 🎯 **Core Agent Engine** (`src/agents/`)
- **`agent_registry.py`**: Singleton registry managing agent discovery and instantiation
- **`base_agent.py`**: Abstract base classes with chainable execution patterns
- **`agent_handler.py`**: Runtime agent management and configuration loading
- **`implementations/`**: Concrete agent implementations (Pinecone RAG, role-playing, introspective agents)

### 🔧 **Chainable Agent Framework**
Each agent inherits from `ChainableAgent` and uses the `@register_chain` decorator to build complex reasoning pipelines:
- **Ordered execution**: Chains execute in definition order
- **Memory integration**: Built-in conversation history management
- **Stream handling**: Real-time response streaming with custom callbacks
- **Tool integration**: Seamless function calling and context management

### 🎨 **Modular UI System** (`src/app/`)
- **`ui_component.py`**: Reusable Streamlit components with clean interfaces
- **`chat_interface.py`**: Stateful chat management with message history
- **`initialization.py`**: Session state management and agent bootstrapping

### 🧠 **Smart Memory & Utilities** (`src/utils/`)
- **`memory_handler.py`**: Persistent conversation memory with context awareness
- **`stream_handler.py`**: Custom callback system for real-time streaming
- **`file_operations.py`**: Configuration and data management utilities

## 🔄 How It All Works Together

1. **Agent Discovery**: `@register_agent` decorator auto-registers classes
2. **Configuration Mapping**: YAML configs map to registered agent types
3. **Dynamic Instantiation**: Runtime agent creation based on user selection
4. **Chain Execution**: Decorated methods build and execute LangChain pipelines
5. **Stream Processing**: Custom handlers manage real-time response streaming

### Adding New Agents (The Easy Way)

1. **Define in `config/agents.yaml`:**
```yaml
my_awesome_agent:
  model_provider: "openai"
  model: "gpt-4o-mini"
  type: "custom"
  role: "Your agent's specialized role"
```

2. **Implement with decorators:**
```python
@register_agent
class AwesomeAgent(ChainableAgent):
    @register_chain
    def reasoning_chain(self):
        # Your chain logic here
        return chain
```

3. **That's it!** The registry handles the rest.

---

## 🎭 Featured Agents

- **🔍 IsaacSim Agent**: RAG-powered assistant for Omniverse Isaac Sim/Lab documentation
- **🧠 Pinecone Agent**: Vector database integration with contextual retrieval
- **🎪 Role Agent**: Dynamic role interpretation from conversation context
- **💻 Python Programmer**: Code-focused agent that outputs pure Python solutions
- **👑 Project Guru**: Technical discussion specialist with concise, expert responses
- **🏢 Software Manager**: High-level instruction provider for development teams

## 💡 Design Philosophy

This project demonstrates **AI agent orchestration** with:

- **Zero-config extensibility**: Drop in a new agent file, add a decorator, done
- **Separation of concerns**: Clean boundaries between UI, logic, and configuration
- **Stream-first architecture**: Real-time response handling built from the ground up
- **Memory-aware conversations**: Persistent context across interactions
- **Tool integration**: Seamless function calling and external API management

Built with care, engineered for scale, designed for developers who appreciate clean abstractions and powerful flexibility.

---

*The future of human-AI collaboration starts with better architecture. This is that architecture.* <-- says the AI that wrote the README lol.

I built this when we were still in the chatbot phase and agent-based dev tools were not available. Quickly gave this up for Cursor, Claude Code, and the like but it was fun while it lasted <--- says human that developed this project. 
