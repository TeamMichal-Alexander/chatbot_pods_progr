To launch with project you need to install all liraries and run 2 coomands from main directory:
--
~~~
chroma run --path src/chromadb --port 8001
~~~
~~~
ssh -L 9999:10.192.168.112:8010 -p8007 <imię użytkownika>@10.192.168.112  
~~~
Potem wprowadź hasło
~~~
python3 src/app.py
~~~
~~~
python3 site_QandA/manage.py runserver
~~