

# Ai Service cu Flask, YOLO și TTS

Acest proiect si-a propus să implementeze un **serviciu AI modular** care primește o imagine și un text descriptiv, identifică obiectele din imagine folosind **YOLO (Ultralytics)** și generează un răspuns audio folosind **Coqui TTS**.
Comunicarea dintre componente se realizează prin broker-ul de mesaje RabbitMQ, iar coordonarea este realizată de un endpoint **Flask**.


# Arhitectura proiectului

Structura generală:

```markdown
app/

|-----app.py # Endpoint Flask principal

|-----message_routing.py # Componentă auxiliară din Flask care se ocupă cu logica de rutare a mesajelor RabbitMQ

images/

|-----Câteva imagini pe care poate fi testată aplicația + Gif-urile din secțiunea de mai jos 

workers/

|-----yolo_worker.py # Worker pentru detecție de obiecte (YOLO)

|-----tts_worker.py # Worker pentru generarea audio (TTS)


tests/

|----- test_request.py # Script de testare a endpoint-ului


config.json # Configurația RabbitMQ

requirements.txt # Dependențe
```


### Funcționalități principale
```markdown
- Detectarea obiectelor din imagini folosind YOLOv8
- Generarea unui răspuns audio bazat pe text (Coqui TTS)
- Comunicare asincronă între componente prin RabbitMQ
- Endpoint Flask ('/countObjects') care coordoneaza fluxul
- Testare automată prin script-ul 'tests/test_request.py' 
```


### Fluxul aplicației (end-to-end) este următorul:
```
Client → Flask → „task_queue” → YOLO → „tts_queue” → TTS → „response_queue” → Flask → Client.
```

## Instalare și rulare

Clonează proiectul:
```bash
git clone https://github.com/<numele-tau>/countObjects_AI.git
cd countObjects_AI
```

### Instalare RabbitMQ
- **Pe Windows (recomandat pentru testarea locală):**
1. Descarcă si instalează Erlang:
👉 https://www.erlang.org/downloads
2. Descarcă și instalează RabbitMQ:
👉 https://www.rabbitmq.com/download.html
3. După instalare, pornește serviciul RabbitMQ

Portul 15672 este pentru interfața web de management:
👉 http://localhost:15672, utilizator implicit: guest/guest


## Configurare mediu Anaconda
Proiectul a fost creat și testat într-un mediu Python izolat creat cu **Anaconda**.
### Creare mediu
Creează mediu nou (de exemplu 'countObjects_AI') cu Python 3.10:
```bash
conda create -n countObjects_AI python=3.10
```

### Activează mediul creat:
```bash
conda create -n countObjects_AI python=3.10
```
## Instalare dependențe:
```bash
pip install -r requirements.txt
```

## Rulează serviciile (recomandat din folderul rădăcină a proiectului):
### Se deschid 4 terminale, se activează mediul Anaconda în fiecare, iar apoi se rulează în fiecare terminal câte un serviciu.
```bash
# Terminalul 1
python -m app.app

# Terminalul 2
python -m workers.yolo_worker

# Terminalul 3
python -m workers.tts_worker

# Terminalul 4 (testare endpoint)
python -m tests.test_request
```
## Gif-uri/Demo
În continuare sunt prezentate două demonstrații de rulare ale aplicației. Vă rog să aveți puțină răbdare deoarece se încarcă mai greu (poate dura 2-3 minute). 
### Demo 1:
![Run Test 1](https://raw.githubusercontent.com/andrei-vasile-dev/ObjectCounterAI/main/images/Gif1.gif)

### Demo 2:
![Run Test 2](https://raw.githubusercontent.com/andrei-vasile-dev/ObjectCounterAI/main/images/Gif2.gif)


# Scurtă descriere
 Aplicația este un sistem AI distribuit care procesează cereri sub formă de JSON:
 ```bash
  {
  "id": id_value,
  "text": "How many cars are represented in the image?"
  }
  ```
Pe disk vor exista o serie de n imagini la care se face referire în întrebarea din payload. După ce serverul Flask primește cererea, trimite mesajul într-o coadă RabbitMQ (task_queue) pentru a fi prelucrat de worker-ul YOLO. Acest worker utilizează modelul YOLOv8n (din pachetul Ultralytics) pentru a detecta obiectele din imagine și returnează rezultatul sub formă de text (ex. "There are 6 object(s) of type 'car' in the image.").

 Rezultatul este apoi trimis mai departe, printr-o altă coadă (tts_queue) către worker-ul TTS (Text-to-Speech). Acesta utilizează biblioteca Coqui TTS pentru a genera un fișier audio (.wav) care redă verbal răspunsul. TTS trimite server-ului Flask un mesaj JSON de forma:
  ```bash
  {
  "mesaj": textul sintetizat,
  "audio_base64": "<fisier_audio_codificat_base64>"
  }
  ```

 Mesajul va trimis către server prin coada response_queue.
 În final, Flask primește răspunsul (de fapt clasa MessageRouting, care este un worker intern al aplicației Flask ce rulează într-un thread separat și care face conexiunea cu RabbitMQ), iar acesta îl oferă prin HTTP către script-ul client (test_request.py).