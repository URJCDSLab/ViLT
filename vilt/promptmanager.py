# -*- coding: utf-8 -*-

from os.path import isfile, join
from pathlib import Path
import os


class PromptManager:
    """
    Manages prompt files by reading and storing them in a dictionary.
    """

    def __init__(self):
        """
        Initializes the PromptManager by setting the prompts directory and loading prompt files.
        """
        self.prompts = {}
        self.path_dir = Path(__file__).parent / '../prompts'
        self.read_prompts()

    def read_prompts(self):
        """
        Reads all `.prompt` files from the prompts directory and stores them in a dictionary.
        """
        files = os.listdir(self.path_dir)
        for file in files:
            file_path = join(self.path_dir, file)
            if isfile(file_path) and file.endswith('.prompt'):
                with open(file_path, 'r', encoding='utf-8') as document:
                    text = document.read()
                    name = file.split('.')[0]
                    self.prompts[name] = text
