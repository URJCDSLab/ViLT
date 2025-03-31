# -*- coding: utf-8 -*-

from vilt.promptmanager import PromptManager
from dotenv import load_dotenv
import logging
import openai
import ast
import os


class KeywordsManager:
    """
    Manages the extraction of keywords from student queries during chatbot interactions.
    """

    def __init__(self):
        """
        Initializes the KeywordsManager by loading environment variables and setting up the prompt.
        """
        load_dotenv(override=True)
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_KEY')
        prompt_manager = PromptManager()
        self.prompt = prompt_manager.prompts['openai_keywords']

    def generate_keywords(self, text):
        """
        Extracts keywords from a given text using an AI model.

        Parameters
        ----------
        text : str
            The input text to analyze and extract keywords from.

        Returns
        -------
        response : list
            A list of extracted keywords as strings.
        """
        response = []
        if text:
            question = self.prompt + '"' + text + '"'
            messages = [
                {'role': 'user', 'content': question},
                {'role': 'system', 'content': 'You are a linguistic expert.'}
            ]

            try:
                completion = openai.chat.completions.create(
                    model='gpt-3.5-turbo', messages=messages, temperature=0
                )
                if completion.choices:
                    response = ast.literal_eval(dict(completion.choices[0].message)['content'])
            except ValueError:
                logging.info('Response provided is not correct.')

        return response
