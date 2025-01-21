# File: agents.py
import importlib
import pathlib

# Get the path of the current file
current_path = pathlib.Path(__file__).parent

# Get the path of the implementations directory
implementations_path = current_path / 'implementations'

# Initialize an empty list to store the imported agent classes
agent_classes = []

# Iterate over all .py files in the implementations directory
for file_path in implementations_path.glob('*.py'):
    # Get the module name (file name without .py extension)
    module_name = file_path.stem
    
    # Import the module
    module = importlib.import_module(f'src.agents.implementations.{module_name}')
    
    # Add any classes from the module that end with 'Agent' to the agent_classes list
    agent_classes.extend([getattr(module, name) for name in dir(module) 
                          if name.endswith('Agent') and name != 'BaseAgent'])

# Make the agent classes available for import from this module
__all__ = [cls.__name__ for cls in agent_classes]

# You can also print out the loaded agents for debugging
print(f"Loaded agents: {', '.join(__all__)}")
