import logging

import ollama
import chromadb
import pdfplumber

from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_experimental.llms.anthropic_functions import prompt

from connect import ask_ollama_server
from templates.prompts import final_prompt_sql_template, prompt_to_sql_database_template, final_prompt_with_pdf_template

import os

class I:
    def __init__(self):
        pass

class Model:
    def __init__(self, pdf_path: str, working_with_ollama_server=True):
        self.logger = logging.getLogger(__name__)
        self.working_with_ollama_server = working_with_ollama_server
        logging.basicConfig(filename='py_log.log', encoding='utf-8', level=logging.DEBUG)
        self.pdf_path = pdf_path
        self.model_embedding = "mxbai-embed-large"
        self.model = "llama3.1"
        if self.working_with_ollama_server:
            from copy_ollama_function_ChatOllama import ChatOllama
            self.ollama_generate = ask_ollama_server
        else:
            from langchain_community.chat_models import ChatOllama
            self.ollama_generate = ollama.generate
        self.llm_model_for_sql = ChatOllama(model='llama3.1')
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(name="docs")
        self.document = self._read_document()
        self.database_filename = os.path.abspath(os.path.join(os.path.dirname(__file__), '../content/plan_lekcji10.db'))
        self.db_path = os.path.join(os.getcwd(), self.database_filename)
        self.db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
        self._embedding_document()
        self.chain = create_sql_query_chain(self.llm_model_for_sql, self.db)
        self.sql_prompt_extractor = lambda x: x[x.find('SELECT'):] + ";" if x[x.find('SELECT'):].count(';') == 0 else x[x.find('SELECT'):x.rfind(';') + 1]


    def _read_document(self):
        text = ""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        document = text.split('---')
        for i in text.split('___'):
            document.append(i)
        return document


    def _embedding_document(self):
        for i, d in enumerate(self.document):
            response = ollama.embeddings(model=self.model_embedding, prompt=d)
            embedding = response["embedding"]
            self.collection.add(
                ids=[str(i)],
                embeddings=[embedding],
                documents=[d])


    def collection_is_empty(self):
        all_data = self.collection.peek(limit=1)
        return len(all_data['ids']) == 0


    def ask_pdf(self, question: str) -> str:
        response = ollama.embeddings(
            prompt=question,
            model=self.model_embedding)

        results = self.collection.query(
            query_embeddings=[response["embedding"]],
            n_results=2)

        self.logger.info(results['documents'])
        data = "\n".join([doc[0] for doc in results['documents']])

        output = self.ollama_generate(
            model=self.model,
            prompt=final_prompt_with_pdf_template.format(data, question)
        )

        return output['response']


    def _generate_prompt_to_sql(self, question):
        for i in range(20):
            try:
                response = self.chain.invoke({"question": prompt_to_sql_database_template.format(question)})
                answer = self.db.run(self.sql_prompt_extractor(response))
                if len(answer) > 0:
                    return response
                else:
                    continue
            except Exception as e:
                self.logger.info(f'{i} trying was unsuccessfully')
        return None


    def ask_sql(self, question):
        response = self._generate_prompt_to_sql(question)
        if response:
            db_context = self.sql_prompt_extractor(response)
            db_answer = self.db.run(db_context)
            self.logger.info(db_context)
            self.logger.info(db_answer)
            self.logger.info(final_prompt_sql_template.format(question=question, result=db_answer, request_to_sql=db_context))
            if self.working_with_ollama_server:
                response = self.ollama_generate(prompt=final_prompt_sql_template.format(question=question, result=db_answer, request_to_sql=db_context), model=self.model)
            else:
                response = ollama.generate(prompt=final_prompt_sql_template.format(question=question, result=db_answer, request_to_sql=db_context), model=self.model)
            return response['response']
        else:
            return 'Niestety nie udało się znaleść jakiejkolwiek informacji, sprobójcie przeformulować prompt lub zapytajcie o czymś innym'

    def ask_api(self, _json: dict):
        question = _json.get('question')
        selected_option = _json.get('file')
        if selected_option == "polski":
            answer = self.ask_pdf(question)
        else:
            answer = self.ask_sql(question)
        json_answer = {'answer': answer}
        return json_answer

