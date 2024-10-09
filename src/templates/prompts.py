final_prompt_sql_template = """Zostaje Ci zadane pytanie: „{question}”.
                Też masz zapytanie do bazy danych sql: {request_to_sql}.
                Otrzymujesz także następujące dane z bazy danych, które są zawierają w sobie odpowiedź na pytanie: „{result}”.
                Korzystając wyłącznie z tych danych, które podałem, krótko i precyzyjnie, ale informatywnie odpowiedz na pytanie. Nie dodawaj nic zbędnego i nie udzielaj wyjaśnień — odpowiadaj tylko na temat. Przy przeliczeniu w celu rozdzielenia wykorzystuj przycinek. 
                """

prompt_to_sql_database_template = """Jesteś modelem AI, którego zadaniem jest generowanie zapytań SQL na podstawie mojego opisu. Twoim celem jest wygenerowanie poprawnego zapytania SQL do bazy danych, składającej się z tabel połączonych ze sobą kolumnami z sufiksem id. Te kolumny są używane wyłącznie do łączenia tabel i nie można ich używać do porównywania danych.

                Model nie może używać żadnych danych, które nie zostały bezpośrednio podane w zapytaniu. Model nie może tworzyć ani wymyślać wartości takich jak teacherid, subjectid lub jakichkolwiek innych wartości. Jeśli takie dane są wymagane, ale nie zostały dostarczone w pytaniu, model powinien odpowiedzieć, że nie posiada wystarczających danych do wygenerowania zapytania.

                Jako odpowiedź powinieneś napisać tylko zapytanie do bazy dannych

                Dodatkowo:

                Jeśli w dwóch lub więcej tabelach występują kolumny o tych samych nazwach, należy jasno określić, do której tabeli odnosi się każda kolumna, używając aliasów tabel. To pomoże uniknąć błędów dwuznaczności.
                Jeśli w zapytaniu użytkownika wspomniany jest dzień tygodnia, model powinien uzyskać id tego dnia z tabeli days.
                Kiedy połańczasz tablicy między sobą za pomocą lessons.classid zawsze korzystaj się z polecenia lessons.classid LIKE '%' || table_name.column_name || '%'
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
                Pytanie: Wypisz przedmiot który ma 2cT drugą lekcją we wtorek? SQLQuery: SELECT su.name FROM subjects AS su INNER JOIN lessons AS le ON su.subjectid = le.subjectid INNER JOIN classes AS cl ON le.classid LIKE '%' || cl.classid || '%' INNER JOIN cards AS ca ON le.lessonid = ca.lessonid INNER JOIN days AS da ON ca.daysbinary = da.daysbinary WHERE cl.name = '2cT' AND (da.name = 'Wtorek' OR da.name = 'wtorek') AND ca.period = 2; SQLResult: programowanie obiektowe Answer: Drugą lekcją we wtorek 2cT ma programowanie obiektowe
                Pytanie: Kiedy 2cT ma lekcje testowania i dokumentacji? SQLQuery:  SELECT da.name FROM days as da INNER JOIN cards AS ca ON da.daysbinary = ca.daysbinary INNER JOIN lessons AS le ON ca.lessonid = le.lessonid INNER JOIN classes AS cl ON le.classid LIKE '%' || cl.classid || '%' INNER JOIN subjects AS su ON le.subjectid = su.subjectid WHERE cl.name = '2cT' AND (su.name = 'testowanie i dokumentacja' OR su.short_name = 'testowanie i dokumentacja'); SQLResult: Poniedziałek Answer: 2cT ma lekcję testowania i dokumentacji w poniedziałek
                Pytanie: Wypisz wszystkie lekcje które ma 2cT w środę? SQLQuery: SELECT su.name FROM subjects AS su INNER JOIN lessons AS le ON su.subjectid = le.subjectid INNER JOIN classes AS cl ON le.classid LIKE '%' || cl.classid || '%' INNER JOIN cards AS ca ON le.lessonid = ca.lessonid INNER JOIN days AS da ON ca.daysbinary = da.daysbinary WHERE cl.name = '2cT' AND (da.name = 'Środa' OR da.name = 'środa'); SQLResult zajęcia z wychowawcą, matematyka, podstawy baz danych, podstawy baz danych, chemia, Przedmiot prcodawcy, Przedmiot prcodawcy, informatyka Answer: 2cT ma zajęcia z wychowawcą, matematyka, podstawy baz danych, podstawy baz danych, chemia, Przedmiot prcodawcy, Przedmiot prcodawcy, informatyka w środę

                Pytanie: {}
                """

final_prompt_with_pdf_template = ("""Jesteś botem Q&A, ode mnie otrzymasz fragmenty tekstu z planu nauki języka polskiego w szkole ponadpodstawowej, ten plan jest dokładny. Otrzymasz również pytanie, na które musisz odpowiedzieć, opierając się na fragmentach tekstu, ale niektóre fragmenty tekstu mogą nie pasować do pytania lub zawierac kompletnie inną informację. Możesz korzystać się z kilku fragmentów dla swojej odpowiedzi. Fragmenty tekstu będą rozdzielony dwoma Enter'ami lub \n\n. Niektóre fragmenty mogą zawierać podszebną informację, ale jeszcze niepodszebną, dlatego możesz jeżeli takie fragmenty będą podane, znaleść w nich podszebną informacę i skorzystać się z niej. Twoja odpowiedź powinna być dokładna, informatywna i rozszerzona. Ponadto, jeśli to konieczne, możesz zacytować części tekstu w swojej odpowiedzi. 
        Oto fragmenty tekstu: [{}]
        Pytanie: [{}]""")


prompt_to_model_for_chunking_text_template = """Zadanie:

Podziel tekst na fragmenty o długości około 100-150 słów. Jeżeli w tekście pojawia się lista, znajdź nagłówek nad nią i zwróć listę w formacie: || Nagłówek :: Lista ||. Jeśli nie ma nagłówka, zwróć listę w formacie || Bez nagłówka :: Lista ||. Nagłówek to tekst, który znajduje się bezpośrednio przed listą i może być oddzielony jako osobna linia lub kończyć się dwukropkiem.

Przykład działania:

Tekst wejściowy:

Rano:
Obudzić się.
Zrobić ćwiczenia.
Zjeść śniadanie.
Plany na dzień:
Iść do sklepu.
Zakończyć projekt.
Zorganizować spotkanie.
Praca nad projektem idzie zgodnie z planem, ale ważne jest, aby pamiętać o kilku kluczowych punktach:

Wyznaczać cele na tydzień.
Robić codzienne raporty.
Analizować postępy.
Oczekiwany rezultat:

|| Rano :: - Obudzić się.

Zrobić ćwiczenia.
Zjeść śniadanie. ||
|| Plany na dzień :: - Iść do sklepu.

Zakończyć projekt.
Zorganizować spotkanie. ||
Praca nad projektem idzie zgodnie z planem, ale ważne jest, aby pamiętać o kilku kluczowych punktach:

|| Bez nagłówka :: - Wyznaczać cele na tydzień.

Robić codzienne raporty.
Analizować postępy. ||
Twój tekst:

{}"""

prompt_to_generate_shorter_text_for_embedding_template = """Wygeneruj opis tekstu, który zostanie użyty do tworzenia osadzania (embedding) i Retrieval-Augmented Generation (RAG). Opis powinien mieć do 50 znaków i zawierać kluczowe słowa, które występują w tekście. Te słowa kluczowe powinny oddawać istotę treści i pomagać w skutecznym odnalezieniu tekstu na podstawie odpowiednich zapytań. Twoim celem jest zapewnienie maksymalnie precyzyjnego wydobycia tekstu na podstawie tych słów. Jeżeli w tekscie się spotyka lista, to opis obowiązkowo powinien zawierac nagłówek tej listy. Odpowiedź powinna wyglądać w następny sposób:'
To jest opis twojego tekstu: 
"tutaj opis"
'. 

Przykład 1: '
Tekst: Treści nauczania – wymagania szczegółowe
Na III etapie edukacyjnym obowiązuje utrwalanie, poszerzanie i doskonalenie wiadomości
i umiejętności nabytych w szkole podstawowej.
ZAKRES PODSTAWOWY ZAKRES ROZSZERZONY
I. Kształcenie literackie i kulturowe.
1. Czytanie utworów literackich. Uczeń:
1) rozumie podstawy periodyzacji
literatury, sytuuje utwory literackie
w poszczególnych okresach:
starożytność, średniowiecze, renesans,
barok, oświecenie, romantyzm,
pozytywizm, Młoda Polska,
dwudziestolecie międzywojenne,
literatura wojny i okupacji, literatura lat
1945–1989 krajowa i emigracyjna,
literatura po 1989 r.;
2) rozpoznaje konwencje literackie
i określa ich cechy w utworach
(fantastyczną, symboliczną,
mimetyczną, realistyczną,
naturalistyczną, groteskową);
3) rozróżnia gatunki epickie, liryczne,
dramatyczne i synkretyczne, w tym:
gatunki poznane w szkole podstawowej
oraz epos, odę, tragedię antyczną,
psalm, kronikę, satyrę, sielankę, balladę,
dramat romantyczny, powieść poetycką,
a także odmiany powieści i dramatu,
wymienia ich podstawowe cechy
gatunkowe;
4) rozpoznaje w tekście literackim środki
wyrazu artystycznego poznane w szkole
podstawowej oraz środki znaczeniowe:
oksymoron, peryfrazę, eufonię,
hiperbolę; leksykalne, w tym
frazeologizmy; składniowe: antytezę,
paralelizm, wyliczenie, epiforę, elipsę;
wersyfikacyjne, w tym przerzutnię;

To jest opis twojego tekstu: 
"Treści nauczania, wymagania szczegółowe, III etap edukacyjny, zakres podstawowy, zakres rozszerzony"
'

Przykład 2: '
Tekst: Szkoła  ponadpodstawowa  — język  polski   
25 sporządza bazę danych;  
11)  korzysta z zasobów multimedialnych, 
np. z:  bibliotek, słowników on- line, 
wydawnictw e -book, autorskich stron 
internetowych; dokonuje wyboru źródeł 
internetowych, uwzględniając kryterium 
poprawności rzeczowej oraz krytycznie 
ocenia ich zawartość;  
12)  wykorzystuje formę projektu 
w przygotowaniu i prezentowaniu oraz 
popularyzowaniu swoich zainteresowań 
i osiągnięć;  
13) zna pojęcie hipertekstu; rozpoznaje jego realizacje internetowe oraz pozainternetowe; określa ich funkcje w komunikacji, umiejętnie z nich 
korzysta w gromadzeniu informacji.  
 
 
Lektura obowiązkowa  
ZAKRES PODSTAWOWY  ZAKRES ROZSZERZONY  
1) Biblia , w tym fragmenty Księgi Rodzaju, Księgi 
Hioba, Księgi Koheleta, Pieśni nad Pieśniami, 
Księgi Psalmów , Apokalipsy wg św. Jana;  
2) Jan Parandowski, Mitologia, część I Grecja ; 
3) Homer, Iliada (fragmenty), Odyseja 
(fragmenty);  
4) Sofokles, Antygona;  
5) Horacy  – wybrane utwory;  
6) Bogurodzica; Lament świętokrzys ki 
(fragmenty); Legenda o  św. Aleksym 
(fragmenty); Rozmowa Mistrza Polikarpa ze 
Śmiercią  (fragmenty);  
7) Kwiatki świętego Franciszka z Asyżu 
(fragmenty);  
8) Pieśń o Rolandzie (fragmenty);  
9) Gall Anonim, Kronika polska (fragmenty);  
10) Dante Alighieri, Boska komedia (fragmenty);  
11) Jan Kochanowski, wybrane pieśni, w tym: 
Pieśń IX ks. I, Pieśń V ks. '

To jest opis twojego tekstu: 
"Szkoła  ponadpodstawowa , 25 sporządza bazę danych , lista lektur obowiązkowych , zakres podstawowy , zakres rozszerzony"
'


Tekst, który powinieneś opisać: 
{}
"""