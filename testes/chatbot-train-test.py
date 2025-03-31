# -*- coding: utf-8 -*-

from vilt.chatbotmanager import Chatbot
from vilt.promptmanager import PromptManager
import logging


logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)
promptmanager = PromptManager()
career = 'GCID'
subject = 'Inferencia Estadística'
processed_docs = 'processed_docs'

# Entrenamiento con ChatGPT
chatbot_gpt = Chatbot(promptmanager.prompts['openai_explicative'], career, subject, use_openai=True, processed_docs=processed_docs)
chatbot_gpt.train()

# Entrenamiento con OLlama
chatbot_llama = Chatbot(promptmanager.prompts['local_explicative'], career, subject, use_openai=False, processed_docs=processed_docs)
chatbot_llama.train()
