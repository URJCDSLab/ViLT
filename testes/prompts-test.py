# -*- coding: utf-8 -*-
from vilt.promptmanager import PromptManager
import logging

logging.basicConfig()
logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)
promptmanager = PromptManager()
for name, prompt in promptmanager.prompts.items():
    logging.info('\n' + name + ': \n' + prompt)