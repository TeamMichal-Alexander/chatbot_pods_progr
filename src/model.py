import logging
from fileinput import filename
from os.path import exists

import ollama
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
import pdfplumber

from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain

from connect import ask_ollama_server
from templates.prompts import *
from langchain_community.embeddings import OllamaEmbeddings
import pickle
from langchain_community.vectorstores import FAISS
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import SimpleDirectoryReader



import os

class Model:
    def __init__(self, pdf_path: str, working_with_ollama_server):
        self.logger = logging.getLogger(__name__)
        self.working_with_ollama_server = working_with_ollama_server
        logging.basicConfig(filename='py_log.log', encoding='utf-8', level=logging.DEBUG)
        self.pdf_path = pdf_path
        self.dict_of_chunks = {}
        self.model_embedding = "mxbai-embed-large"
        self.model = "llama3.1"
        self.pkl_file = 'jezyk-polski.pkl'
        self.faiss_path = 'content/faiss'
        if self.working_with_ollama_server:
            from copy_ollama_function_ChatOllama import ChatOllama
            self.ollama_generate = ask_ollama_server
        else:
            from langchain_community.chat_models import ChatOllama
            self.ollama_generate = ollama.generate
        self.llm_model_for_sql = ChatOllama(model='llama3.1')
        self.path_to_save_chromadb = os.path.abspath(os.path.join(os.path.dirname(__file__), 'chromadb'))
        self.client = chromadb.HttpClient(host='localhost', port=8001)
        self.ollama_embedding_for_chromadb = embedding_functions.OllamaEmbeddingFunction(
            url="http://localhost:11434/api/embeddings",
            model_name=self.model_embedding,
        )
        self.collection = self.client.get_or_create_collection(name="docs", embedding_function=self.ollama_embedding_for_chromadb)
        self.document = self._read_document()
        self.database_filename = os.path.abspath(os.path.join(os.path.dirname(__file__), '../content/plan_lekcji10.db'))
        self.db_path = os.path.join(os.getcwd(), self.database_filename)
        self.db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
        self.list_of_embeded_document = []
        self._embedding_document()
        self.chain = create_sql_query_chain(self.llm_model_for_sql, self.db)
        self.sql_prompt_extractor = lambda x: x[x.find('SELECT'):] + ";" if x[x.find('SELECT'):].count(';') == 0 else x[x.find('SELECT'):x.rfind(';') + 1]


    def make_chunking(self) -> list:
        documents = SimpleDirectoryReader(input_files=[self.pdf_path]).load_data()
        splitter = SemanticSplitterNodeParser(
            buffer_size=3, breakpoint_percentile_threshold=95,
            embed_model=OllamaEmbedding(model_name=self.model_embedding),
        )
        docs = splitter.get_nodes_from_documents(documents)
        with open(self.pkl_file, 'wb') as f:
            pickle.dump([i.get_content() for i in docs], f)
        return [i.get_content() for i in docs]


    def _read_document(self):
        # text = ""
        # with pdfplumber.open(self.pdf_path) as pdf:
        #     for page in pdf.pages:
        #         text += page.extract_text() + "\n"
        # document = text.split('---')
        # for i in text.split('___'):
        #     document.append(i)
        # return document
        if not exists(self.pkl_file):
            self.make_chunking()
        with open(self.pkl_file, 'rb') as f:
            loaded_list = pickle.load(f)
            answer = []
            _ = [answer.append(i) if len(i) > 0 else None for i in loaded_list]
            for i, text in enumerate(answer):
                self.collection.add(documents=text, ids=[f'{i}_id'])
            return answer


    def generate_description_for_embedding(self, data):
        dictionary_of_chunks = {}
        for i, text in enumerate(data):
            key = self.ollama_generate(model=self.model, prompt=prompt_to_generate_shorter_text_for_embedding_template.format(text))['response']
            key = key[key.find('"')+1:key.rfind('"')]
            dictionary_of_chunks[key] = text
        return dictionary_of_chunks


    def _embedding_document(self):
        try:
            self.db_faiss = FAISS.load_local(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', self.faiss_path)), OllamaEmbeddings(model='llama3.1'), allow_dangerous_deserialization=True, )
            keys = [i.page_content for i in self.db_faiss.docstore._dict.values()]
            if len(keys) != len(self.document):
                raise 'len of description not equal len of document'
            for key, value in zip(keys, self.document):
                self.dict_of_chunks[key] = value
            print('all')
        except Exception as e:
            self.logger.warning(f"{e} in _embedding_document function")
            counter = 0
            dict_of_chunks = self.generate_description_for_embedding(self.document)
            self.dict_of_chunks = dict_of_chunks
            self.db_faiss = FAISS.from_texts(
                list(dict_of_chunks.keys()),
                OllamaEmbeddings(model=self.model_embedding)
            )
            self.db_faiss.save_local(self.faiss_path, 'index')
            for i, d in enumerate(dict_of_chunks.keys()):
                counter += 1
                response = ollama.embeddings(model=self.model_embedding, prompt=d)
                embedding = response["embedding"]
                self.list_of_embeded_document.append(embedding)
                self.collection.add(
                    ids=[str(i)],
                    embeddings=[embedding],
                    documents=[d])


    def collection_is_empty(self):
        all_data = self.collection.peek(limit=1)
        return len(all_data['ids']) == 0


    def ask_pdf(self, question: str) -> str:
        # response = ollama.embeddings(
        #     prompt=question,
        #     model=self.model_embedding)
        # print(response)

        # results = self.collection.query(
        #     query_embeddings=[response["embedding"]],
        #     n_results=10)

        embedding_vector = ollama.embeddings(model=self.model_embedding, prompt=question)["embedding"]
        matched_docs = self.db_faiss.similarity_search_by_vector(embedding_vector, k=12)
        print(self.collection.query(query_texts=[question], n_results=10))

        # print(matched_docs)
        print(len(matched_docs))
        matched_docs = [self.dict_of_chunks[i.page_content] for i in matched_docs]
        matched_docs = [f'{i} fragment tekstu: ' + text for i, text in enumerate(matched_docs)]
        matched_docs = "\n\n".join(matched_docs)
        print(matched_docs)
        output = self.ollama_generate(
            model=self.model,
            prompt=final_prompt_with_pdf_template.format(matched_docs, question)
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
            except Exception:
                self.logger.info(f'{i} trying was unsuccessfully')
        return None


    def ask_sql(self, question):
        response = self._generate_prompt_to_sql(question)
        if response:
            db_context = self.sql_prompt_extractor(response)
            db_answer = self.db.run(db_context)
            self.logger.info(db_context)
            self.logger.info(db_answer)
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
