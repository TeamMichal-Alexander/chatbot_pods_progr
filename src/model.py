import logging

import ollama
import chromadb
import pdfplumber

from copy_ollama_function_ChatOllama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from connect import ask_ollama_server


import os

class I:
    def __init__(self):
        pass

class Model:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.model_embedding = "mxbai-embed-large"
        self.model = "llama3.1"
        self.llm_model_for_sql = ChatOllama(model='llama3.1')
        self.prompt = ("""Jesteś botem Q&A, ode mnie otrzymasz fragmenty tekstu z planu nauki języka polskiego w szkole ponadpodstawowej, ten plan jest dokładny. Otrzymasz również pytanie, na które musisz odpowiedzieć, opierając się na fragmentach tekstu. Twoja odpowiedź powinna być dokładna, bez zbędnych informacji, ale informatywna i rozszerzona. Ponadto, jeśli to konieczne, możesz zacytować części tekstu w swojej odpowiedzi. Jeśli nie znasz odpowiedzi, poproś o przekształcenie pytania. 
Oto fragmenty tekstu: [{}]
Pytanie: [{}]""")
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(name="docs")
        self.document = self._read_document()
        self.database_filename = './content/plan_lekcji10.db'
        self.db_path = os.path.join(os.getcwd(), self.database_filename)
        self.db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
        self._embedding_document()
        self.chain = create_sql_query_chain(self.llm_model_for_sql, self.db)
        self.sql_prompt_extractor = lambda x: x[x.find('SELECT'):] + ";" if x[x.find('SELECT'):].count(';') == 0 else x[
                                                                                                                      x.find(
                                                                                                                          'SELECT'):x.rfind(
                                                                                                                          ';') + 1]
        self.prompt_to_codellama = """Jesteś modelem AI, którego zadaniem jest generowanie zapytań SQL na podstawie mojego opisu. Twoim celem jest wygenerowanie poprawnego zapytania SQL do bazy danych, składającej się z tabel połączonych ze sobą kolumnami z sufiksem id. Te kolumny są używane wyłącznie do łączenia tabel i nie można ich używać do porównywania danych.

        Model nie może używać żadnych danych, które nie zostały bezpośrednio podane w zapytaniu. Model nie może tworzyć ani wymyślać wartości takich jak teacherid, subjectid lub jakichkolwiek innych wartości. Jeśli takie dane są wymagane, ale nie zostały dostarczone w pytaniu, model powinien odpowiedzieć, że nie posiada wystarczających danych do wygenerowania zapytania.

        Jako odpowiedź powinieneś napisać tylko zapytanie do bazy dannych

        Dodatkowo:

        Jeśli w dwóch lub więcej tabelach występują kolumny o tych samych nazwach, należy jasno określić, do której tabeli odnosi się każda kolumna, używając aliasów tabel. To pomoże uniknąć błędów dwuznaczności.
        Jeśli w zapytaniu użytkownika wspomniany jest dzień tygodnia, model powinien uzyskać id tego dnia z tabeli days.
        Przykład struktury bazy danych:

        Tabela periods:
        periodid, period, name, short, starttime, endtime
        Tabela subjects:
        subjectid, name, short
        Tabela teachers:
        teacherid, firstname, lastname, short, gender, color
        Tabela classrooms:
        classroomid, name, short, capacity
        Tabela groups:
        groupid, name, classid, entireclass, divisiontag, studentcount
        Tabela lessons:
        lessonid, classid, subjectid, teacherid, classroomid, groupid, periodspercard, periodsperweek
        Tabela days:
        dayid, name, short, binary
        Tabela classes:
        classid, name, short, teacherid, classroomid, grade
        Instrukcje:

        Używaj JOIN, aby łączyć tabele na podstawie kolumn z sufiksem id.
        Nie używaj tych kolumn do filtrowania ani porównywania danych.
        Zawsze używaj LIMIT 1, jeśli użytkownik nie określił liczby wyników.
        Nigdy nie zapytuj o wszystkie kolumny z tabeli — wybieraj tylko te kolumny, które są potrzebne do odpowiedzi na pytanie.
        Nazwy kolumn otaczaj w podwójnych cudzysłowach (").
        Używaj funkcji date('now'), aby uzyskać bieżącą datę, jeśli pytanie dotyczy "dzisiaj".
        Wykorzystuj tylko te kolumny, które istnieją w bazie danych, i unikaj zapytań o nieistniejące kolumny.
        Nie wykonuj żadnych dodatkowych porównań na podstawie danych, których nie ma w zapytaniu użytkownika.
        Nie twórz żadnych wartości identyfikatorów (np. teacherid, subjectid), jeśli nie zostały one jawnie podane w zapytaniu.
        Jeśli w kilku tabelach istnieją kolumny o takich samych nazwach, zawsze określaj, z której tabeli pochodzi dana kolumna, używając aliasów tabel.
        Jeśli użytkownik wspomina o dniu tygodnia, model powinien uzyskać odpowiednie id dnia z tabeli days.
        Jeśli użytkownik nie dostarczył wystarczających danych, odpowiedz, że nie możesz wygenerować zapytania.
        Jeśli pytanie zawiera odniesienie do bieżącej daty, używaj informacji dostępnych w bazie danych.
        Jeśli użytkownik nie określa liczby wyników, zwracaj tylko jeden rekord przy użyciu LIMIT.
        Uporządkuj wyniki, aby zwrócić najbardziej informacyjne dane, jeśli to konieczne.
        Nigdy nie używaj kolumn z sufiksem id do filtrowania ani porównywania, a jedynie do JOIN.
        Odpowiadaj ściśle w formacie zapytania SQL, bez komentarzy i zbędnych wyjaśnień.
        Nazwy dni tygodnia powinni się zaczynać z dużej litery.

        Przykłady: 
        Pytanie: "Jakiego wychowawcę ma 2cT?" SQLQuery: SELECT T2."firstname", T2."lastname" FROM "classes" AS T1 INNER JOIN "teachers" AS T2 ON T1."teacherid" = T2."teacherid" WHERE T1."name" = '2cT' LIMIT 1; SQLResult: Paweł|Ostrowski Odpowiedź: Wychowawca w klasie 2cT to Paweł Ostrowski.
        Pytanie: Kto prowadzi lekcji edb? SQLQuery: SELECT T5.firstname, T5.lastname FROM lessons AS T3 INNER JOIN subjects AS T4 ON T3.subjectid = T4.subjectid INNER JOIN teachers AS T5 ON T3.teacherid = T5.teacherid WHERE T4.short_name = 'edb' OR T4.name = 'edb'; SQLResult: Aleksander|Ciwoniuk Odpowiedź: Lekcje edb prowadzi Aleksander Ciwoniuk
        Pytanie: Wypisz przedmiot który ma 2cT drugą lekcją we wtorek? SQLQuery: SELECT su.name FROM subjects AS su INNER JOIN lessons AS le ON su.subjectid = le.subjectid INNER JOIN classes AS cl ON le.classid = cl.classid INNER JOIN cards AS ca ON le.lessonid = ca.lessonid INNER JOIN days AS da ON ca.daysbinary = da.daysbinary WHERE cl.name = '2cT' AND (da.name = 'Wtorek' OR da.name = 'wtorek') AND ca.period = 2; SQLResult: programowanie obiektowe Answer: Drugą lekcją we wtorek 2cT ma programowanie obiektowe
        Pytanie: Kiedy 2cT ma lekcje testowania i dokumentacji? SQLQuery:  SELECT da.name FROM days as da INNER JOIN cards AS ca ON da.daysbinary = ca.daysbinary INNER JOIN lessons AS le ON ca.lessonid = le.lessonid INNER JOIN classes AS cl ON le.classid = cl.classid INNER JOIN subjects AS su ON le.subjectid = su.subjectid WHERE cl.name = '2cT' AND (su.name = 'testowanie i dokumentacja' OR su.short_name = 'testowanie i dokumentacja'); SQLResult: Poniedziałek Answer: 2cT ma lekcję testowania i dokumentacji w poniedziałek
        Pytanie: Wypisz wszystkie lekcje które ma 2cT w środę? SQLQuery: SELECT su.name FROM subjects AS su INNER JOIN lessons AS le ON su.subjectid = le.subjectid INNER JOIN classes AS cl ON le.classid = cl.classid INNER JOIN cards AS ca ON le.lessonid = ca.lessonid INNER JOIN days AS da ON ca.daysbinary = da.daysbinary WHERE cl.name = '2cT' AND (da.name = 'Środa' OR da.name = 'środa'); SQLResult zajęcia z wychowawcą, matematyka, podstawy baz danych, podstawy baz danych, chemia, Przedmiot prcodawcy, Przedmiot prcodawcy, informatyka Answer: 2cT ma zajęcia z wychowawcą, matematyka, podstawy baz danych, podstawy baz danych, chemia, Przedmiot prcodawcy, Przedmiot prcodawcy, informatyka w środę

        Pytanie: {}
        """


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

        print(results['documents'])
        data = "\n".join([doc[0] for doc in results['documents']])

        output = ask_ollama_server(
            model=self.model,
            prompt=self.prompt.format(data, question)
        )

        return output['response']


    def ask_sql(self, question):
        error = 0
        print(1)
        response = None
        for i in range(10):
            response = self.chain.invoke({"question": self.prompt_to_codellama.format(question)})
            try:
                print(i)
                answer = self.db.run(self.sql_prompt_extractor(response))
                if len(answer) != 0:
                    break
            except Exception as e:
                logging.info(e)
        else:
            error = 1
        if error == 0:
            db_context = self.sql_prompt_extractor(response)
            db_answer = self.db.run(db_context)
            print(db_context)
            print(db_answer)
            human_qry_template = """Zostaje Ci zadane pytanie: „{question}”.
Otrzymujesz także następujące dane z bazy danych: „{result}”.
Korzystając wyłącznie z tych danych, które podałem, krótko i precyzyjnie, ale informatywnie odpowiedz na pytanie. Nie dodawaj nic zbędnego i nie udzielaj wyjaśnień — odpowiadaj tylko na temat. Przy przeliczeniu w celu rozdzielenia wykorzystuj przycinek. 
"""
            print(human_qry_template.format(question=question, result=db_answer))
            response = ask_ollama_server(prompt=human_qry_template.format(question=question, result=db_answer), model=self.model)
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

