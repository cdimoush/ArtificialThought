import yaml
import os

class FileHandler:
    def __init__(self, config_path):
        self.config = self.load_file_params(config_path)

    def list_files_in_directory(self):
        """
        Lists files in the specified directory path.
        """
        files = []
        for dir in self.config['directories']:
            if not os.path.isdir(dir):
                print(f"Directory '{dir}' does not exist.")
            else:
                files.append(os.listdir(dir))
        return files

    def load_file(self, file_name):
        """
        Loads the content of the specified file, if it exists in the directory.
        """
        filepath = os.path.join(self.directory_path, file_name)
        if os.path.isfile(filepath):
            with open(filepath, 'r') as file:
                return file.read()
        else:
            print('Invalid file path')
            return None
        
    def load_file_params(self, config_path):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config