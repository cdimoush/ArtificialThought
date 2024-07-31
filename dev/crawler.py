import os

def load_file(file_path):
    """
    Load the content of a file.

    Parameters:
    file_path (str): The path to the file to be loaded.

    Returns:
    str: The content of the file.
    """
    file_name = os.path.basename(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content = f"# File: {file_name}\n{content}\n\n"
            return content
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return ''

def find_python_files(top_level_dir):
    """
    Traverse the directory to find all Python files and read their contents.

    Parameters:
    top_level_dir (str): The top-level directory to start the search from.

    Returns:
    list: A list containing the contents of all Python files.
    """
    python_files_content = []
    for root, _, files in os.walk(top_level_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                content = load_file(file_path)
                python_files_content.append(content)
    return python_files_content

def write_to_file(content, output_file):
    """
    Write the aggregated content to an output file.

    Parameters:
    content (list): List of strings containing the content of all Python files.
    output_file (str): The file path where the content will be written.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
    except Exception as e:
        print(f"Error writing to file {output_file}: {e}")

def main():
    """
    Main function to find Python files in a directory and write their content
    to a single output file.
    """
    top_level_dir = 'C:\\Users\\Conner\\Home\\Projects\\ArtificialThought'
    output_file = 'source_code.py'

    files_content = []

    # Load app.py
    app_path = os.path.join(top_level_dir, 'app.py')
    app_content = load_file(app_path)
    files_content.append(app_content)

    # Load all src files
    src_dir = os.path.join(top_level_dir, 'src')
    content = find_python_files(src_dir)
    files_content.extend(content)

    # Write the content to the output file
    write_to_file(files_content, output_file)

if __name__ == "__main__":
    main()