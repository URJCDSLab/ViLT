# -*- coding: utf-8 -*-

from vilt.promptmanager import PromptManager
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs.llm_result import LLMResult
from langchain_community.llms import Ollama
from typing import Any, Dict, List
from dotenv import load_dotenv
from pathlib import Path
from queue import Queue
import logging
import threading
import time
import json
import os

def delete_rubbish(db_path):
    """
    Deletes unnecessary files from the database directory.

    Parameters
    ----------
    db_path : str
        Path to the database directory.
    """
    for file in os.listdir(db_path):
        f_file = os.path.join(db_path, file)
        if os.path.isdir(f_file):
            for i_file in os.listdir(f_file):
                p_file = os.path.join(f_file, i_file)
                if os.path.isfile(p_file) and i_file.endswith(".pickle"):
                    os.unlink(p_file)


def exist_embeddings(db_path):
    """
    Checks if embeddings exist in the specified directory.

    Parameters
    ----------
    db_path : str
        Path to the database directory.

    Returns
    -------
    exists : bool
        True if embeddings exist, False otherwise.
    """
    exists = False
    if os.path.exists(db_path):
        list_files = os.listdir(db_path)
        i = 0
        while i < len(list_files) and not exists:
            if list_files[i].endswith(".sqlite3"):
                exists = True
            else:
                i = i + 1
    return exists


class Chatbot:
    """
    Chatbot class that manages interactions using an LLM model.
    """

    def __init__(self, prompt, selected_career, selected_subject, use_openai=True, processed_docs=None):
        """
        Initializes the Chatbot with a prompt, career, and subject.

        Parameters
        ----------
        prompt : str
            The template prompt for the chatbot.
        selected_career : str
            The career the chatbot is focused on.
        selected_subject : str
            The subject associated with the chatbot.
        use_openai : bool, optional
            Whether to use OpenAI models (default is True).
        processed_docs : str, optional
            Path to processed documents (default is None).
        """
        self.template = prompt
        self.career = selected_career
        self.subject = selected_subject
        self.qa_chain = None
        self.llm = None
        self.prompt_queue = Queue()
        self.sse_event_queue = Queue()
        self.response_thread = None
        project_folder = Path(__file__).parent / '..'
        self.processed_docs = project_folder / 'processed_docs' if processed_docs is None else project_folder / processed_docs
        self.text = ''
        self.use_openai = use_openai
        load_dotenv(override=True)
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_KEY')

    def send_sse_data(self):
        """
        Handles server-sent events (SSE) for streaming chatbot responses.
        """
        response_thread = None
        while True:
            if not self.prompt_queue.empty():
                if response_thread and response_thread.is_alive():
                    continue

                prompt = self.prompt_queue.get()
                self.text += '\n' + prompt + '\n' if self.text else prompt + '\n'
                query = {'input': prompt}
                callbacks = {'config': {'callbacks': [StreamHandler(self.sse_event_queue)]}}
                response_thread = threading.Thread(target=self.qa_chain.invoke, args=(query,), kwargs=callbacks)
                response_thread.start()

            while not self.sse_event_queue.empty():
                sse_event = self.sse_event_queue.get()
                if 'content' in sse_event.keys():
                    self.text += str(sse_event['content'])
                yield f"data: {json.dumps(sse_event)}\n\n"

            time.sleep(1)

    def init_openai_llm(self):
        """
        Initializes an OpenAI-based language model.
        """
        try:
            self.llm = ChatOpenAI(model="gpt-3.5-turbo", streaming=True, temperature=0.0, callbacks=[])
        except Exception as e:
            logging.error(f"OpenAI failed to initialize: {e}.")

    def configure_local_llm(self, db_path):
        """
        Configures a local LLM using Ollama and LangChain.

        Parameters
        ----------
        db_path : str
            Path to the database containing embeddings.
        """
        try:
            delete_rubbish(db_path)
            llm = Ollama(
                base_url=os.getenv('URL_OLLAMA'),
                model='llama3.2',
                temperature=0.0,
                mirostat_tau=0.0,
                top_k=10,
                top_p=0.1,
                num_ctx=4096
            )
            embeddings = FastEmbedEmbeddings()
            vector_store = Chroma(persist_directory=db_path, embedding_function=embeddings)
            retriever = vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": 20,
                    "score_threshold": 0.1,
                },
            )
            prompt = PromptTemplate.from_template(self.template)
            document_chain = create_stuff_documents_chain(llm, prompt)
            self.qa_chain = create_retrieval_chain(retriever, document_chain)
            logging.info("LLM successfully initialized with langchain embeddings.")
        except Exception as e:
            logging.error(f"LLM failed to initialize: {e}")

    def configure_llm(self, db_path):
        """
        Configures the chatbot with OpenAI LLM and vector embeddings.

        Parameters
        ----------
        db_path : str
            Path to the database containing embeddings.
        """
        try:
            delete_rubbish(db_path)
            embedding = FastEmbedEmbeddings()
            vectordb = Chroma(persist_directory=db_path, embedding_function=embedding)
            retriever = vectordb.as_retriever(search_kwargs={'k': 10})
            prompt = PromptTemplate.from_template(self.template)
            question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
            self.qa_chain = create_retrieval_chain(retriever, question_answer_chain)
            logging.info("LLM successfully initialized with langchain embeddings.")
        except Exception as e:
            logging.error(f"LLM failed to initialize: {e}")

    def train(self):
        """
        Trains the chatbot using available embeddings.

        Returns
        -------
        bool
            True if training was successful, False otherwise.
        """
        correct = False
        db_path = os.path.join(str(os.path.join(self.processed_docs, self.career)), self.subject)
        if exist_embeddings(db_path):
            if self.use_openai:
                self.init_openai_llm()
                self.configure_llm(db_path)
            else:
                self.configure_local_llm(db_path)
            correct = True
        return correct



class StreamHandler(BaseCallbackHandler):
    """
    Handles streaming events from the LLM and forwards them to the SSE event queue.
    """

    def __init__(self, sse_event_queue):
        """
        Initializes the StreamHandler with a queue for sending SSE events.

        Parameters
        ----------
        sse_event_queue : queue.Queue
            A queue used for streaming server-sent events (SSE).
        """
        super().__init__()
        self.sse_event_queue = sse_event_queue

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """
        Handles the event when a new token is generated by the LLM.

        Parameters
        ----------
        token : str
            The newly generated token.
        """
        self.sse_event_queue.put({'type': 'token', 'content': token.replace('\n', '<br>')})

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """
        Handles the event when the LLM starts processing a request.

        Parameters
        ----------
        serialized : Dict[str, Any]
            Serialized information about the LLM request.
        prompts : List[str]
            List of prompts sent to the LLM.
        """
        self.sse_event_queue.put({'type': 'start'})

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """
        Handles the event when the LLM completes processing a request.

        Parameters
        ----------
        response : LLMResult
            The result returned by the LLM.
        """
        self.sse_event_queue.put({'type': 'end'})

    def on_llm_error(self, error: BaseException, **kwargs) -> None:
        """
        Handles errors that occur during LLM processing.

        Parameters
        ----------
        error : BaseException
            The exception raised during processing.
        """
        self.sse_event_queue.put({'type': 'error', 'content': str(error)})



class ChatbotManager:
    """
    Manages multiple chatbot instances for different users and subjects.
    """

    def __init__(self):
        """
        Initializes the ChatbotManager with an empty chatbot dictionary and a PromptManager instance.
        """
        self.chatbots = {}
        self.promptmanager = PromptManager()
        self.use_openai = True

    def add_chatbot(self, email, selected_career, selected_subject):
        """
        Adds a chatbot for a specific user, career, and subject.

        Parameters
        ----------
        email : str
            The email of the user.
        selected_career : str
            The career associated with the chatbot and the user.
        selected_subject : str
            The subject associated with the chatbot and the user.

        Returns
        -------
        correct : bool
            True if the chatbot was successfully trained and added, False otherwise.
        """
        prompt = self.promptmanager.prompts['openai_explicative'] if self.use_openai else self.promptmanager.prompts['local_explicative']
        chat_bot = Chatbot(prompt, selected_career, selected_subject, self.use_openai)
        correct = chat_bot.train()
        if correct:
            if email not in self.chatbots.keys():
                self.chatbots[email] = []
            self.chatbots[email].append(chat_bot)
        return correct

    def find_chatbot(self, email, selected_career, selected_subject):
        """
        Finds the position of a chatbot for a specific user, career, and subject.

        Parameters
        ----------
        email : str
            The email of the user.
        selected_career : str
            The career associated with the chatbot and the user.
        selected_subject : str
            The subject associated with the chatbot and the user.

        Returns
        -------
        pos : int
            The index of the chatbot in the user's list, or -1 if not found.
        """
        pos = -1
        if email in self.chatbots.keys():
            i = 0
            found = False
            chatbots = self.chatbots[email]
            while i in range(0, len(chatbots) and not found):
                if chatbots[i].career == selected_career and chatbots[i].subject == selected_subject:
                    found = True
                    pos = i
                else:
                    i += 1
        return pos

    def remove_chatbot(self, email, pos):
        """
        Removes a chatbot for a specific user based on its position in the list.

        Parameters
        ----------
        email : str
            The email of the user.
        pos : int
            The index of the chatbot to remove.
        """
        self.chatbots[email].pop(pos)
