import re
import os
import ast
import json
import textwrap
import typer
from typing import List, Tuple

class FileOperations:
    @staticmethod
    def load_reference_dir(dirpath):
        """
        Load reference code from all files in a directory.
        """
        reference_code = ''
        for file_name in os.listdir(dirpath):
            file_path = os.path.join(dirpath, file_name)
            if os.path.isfile(file_path):
                reference_code += f'*{file_name}*\n'
                reference_code += FileOperations.load_reference_code(file_path)
                reference_code += '\n'
        return reference_code

    @staticmethod
    def load_reference_code(file_path, load_python_functions=False):
        """
        Load reference code from a file.
        """
        _, file_extension = os.path.splitext(file_path)

        ext_map = {
            'py': 'python',
            'java': 'java',
            'js': 'javascript',
            'html': 'html',
            'css': 'css',
            'cpp': 'c++',
            'yaml': 'yaml',
            'json': 'json',
            'ipynb': 'ipynb'
        }

        file_name = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as fin:
            file_content = fin.read()
        try:
            ext = ext_map[file_extension[1:]]
            if ext == 'ipynb':
                reference_code = FileOperations.load_notebook_code(file_content, load_python_functions)
            elif ext == 'python' and load_python_functions:
                reference_code = FileOperations.load_python_functions(file_content)
            else:
                reference_code = f'```{ext}\n{file_content}\n```'
        except KeyError:
            ext = 'unknown'

        reference_code = f'*{file_name}*\n' + reference_code
        return reference_code


    @staticmethod
    def load_python_functions(file_content):
        """
        Load specific functions or classes from a Python file.
        """
        # Parse the file content into an Abstract Syntax Tree (AST)
        module = ast.parse(file_content)
        # Extract all function definitions and class definitions from the AST
        functions = [node for node in module.body if isinstance(node, ast.FunctionDef)]
        classes = [node for node in module.body if isinstance(node, ast.ClassDef)]
        # Initialize a dictionary to map function names to their respective class names
        func_class_dict = {}
        # Also, map the function names to the class name in func_class_dict
        for class_ in classes:
            class_functions = [node for node in class_.body if isinstance(node, ast.FunctionDef)]
            functions.extend(class_functions)
            for func in class_functions:
                func_class_dict[func.name] = class_.name
        # Get the names of all functions and classes
        function_names = [func.name for func in functions]
        class_names = [class_.name for class_ in classes]
        # Print the names of all classes and functions for the user to select from
        typer.secho('\nLoading classes and functions from the module...\n', fg=typer.colors.WHITE, bold=True)
        typer.secho('Classes...', fg=typer.colors.GREEN, bold=True)
        for i, class_name in enumerate(class_names):
            typer.secho(f'{i + 1}. {class_name}', fg=typer.colors.WHITE)
        typer.secho('Functions...', fg=typer.colors.GREEN, bold=True)
        for i, func_name in enumerate(function_names, start=len(class_names) + 1):
            if func_name in func_class_dict:
                typer.secho(f'{i}. {func_name} ({func_class_dict[func_name]})', fg=typer.colors.WHITE)
            else:
                typer.secho(f'{i}. {func_name}', fg=typer.colors.WHITE)
        # Initialize a list to store the selected items
        selected_items = []
        # Keep asking the user for their choice until they enter a non-integer
        typer.secho('\nEnter the number of the function or class you want to load: ', fg=typer.colors.MAGENTA, bold=True)
        typer.secho('(Note: Enter key to exit) ', fg=typer.colors.MAGENTA, bold=True)
        while True:
            choice = input()
            if not choice.isdigit():
                break
            try:
                # If the choice is a valid integer, add the corresponding item to the selected_items list
                item_index = int(choice) - 1
                if item_index < len(classes):
                    selected_items.append(classes[item_index])
                else:
                    selected_items.append(functions[item_index - len(classes)])
            except (ValueError, IndexError):
                typer.secho('Invalid choice', fg=typer.colors.RED)
        # Print the number of items that will be loaded
        typer.secho(f'Loading {len(selected_items)} items...', fg=typer.colors.GREEN)
        # If no items were selected, return the entire file content
        if len(selected_items) == 0:
            reference_code = file_content
        else:
            # Otherwise, generate the reference code from the selected items
            reference_code = ''
            selected_items_grouped = {}
            # Group the selected items by their class
            for item in selected_items:
                if isinstance(item, ast.FunctionDef) and item.name in func_class_dict:
                    class_name = func_class_dict[item.name]
                    if class_name not in selected_items_grouped:
                        selected_items_grouped[class_name] = []
                    selected_items_grouped[class_name].append(item)
                else:
                    # If the item is not a function or its class was not selected, add it to the reference code directly
                    code_block = ast.unparse(item)
                    code_block = FileOperations.extract_comments(code_block, file_content)
                    reference_code += f'{code_block}\n'
            # For each class, add its definition and its functions to the reference code
            for class_name, items in selected_items_grouped.items():
                class_def = f'class {class_name}:\n'
                reference_code += class_def
                for item in items:
                    code_block = '\n'.join((f'\t{line}' for line in ast.unparse(item).split('\n')))
                    code_block = FileOperations.extract_comments(code_block, file_content)
                    reference_code += f'{code_block}\n\n'
        # Wrap the reference code in a Python code block
        reference_code = f'```python\n{reference_code}\n```'
        return reference_code
   
    @staticmethod
    def extract_comments(extracted_code, file_content):
        """
        Take code extracted from unparsed AST and insert comments from the original file.

        Args:
            extracted_code (str): The code extracted from the unparsed AST.
            file_content (str): The content of the original file.
        """
        # Strip all lines in the file content, and store in list
        file_lines = [line.strip() for line in file_content.split('\n')]
        ast_lines = extracted_code.split('\n')
        modified_ast_lines = []
        for line in ast_lines:
            if line.strip() in file_lines:
                line_index = file_lines.index(line.strip())
                # Check the lines immediately above for comments
                if line_index > 0 and file_lines[line_index - 1].startswith('#'):

                    # Extract the comment
                    comment = file_lines[line_index - 1]
                    # Get the whitespace at the beginning of the line
                    whitespace = line[:len(line) - len(line.lstrip())]
                    # Use textwrap.indent() to add the correct indentation to the comment
                    comment = textwrap.indent(comment, whitespace)
                    modified_ast_lines.append(comment)
                # Remove previous lines from file lines
                file_lines = file_lines[line_index + 1:]

            modified_ast_lines.append(line)
        # Return the modified unparsed AST with the comments inserted
        return '\n'.join(modified_ast_lines)

    @staticmethod
    def load_notebook_code(file_content, load_python_functions=False):
        """
        Load code blocks from a Jupyter Notebook.
        """
        notebook_content = json.loads(file_content)
        code_blocks = []
        for cell in notebook_content['cells']:
            if cell['cell_type'] == 'code':
                # Preprocess the code to remove or comment out any lines that start with a `%`.
                code = ''.join(cell['source'])
                code = re.sub(r'^%.*$', '#\g<0>', code, flags=re.MULTILINE)
                code_blocks.append(code)
            # No markdown cells for now.
            # elif cell['cell_type'] == 'markdown':
                # Include the content of markdown cells.
                # code_blocks.append(''.join(cell['source']))
        reference_code = '\n'.join(code_blocks)
        if load_python_functions:
            return FileOperations.load_python_functions(reference_code)
        return f'```python\n{reference_code}\n```'
