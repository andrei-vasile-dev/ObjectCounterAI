
# Script care se ocupa de generarea fisierului audio

import json;
import base64
import pika
from pika import BasicProperties
import uuid
import os
from TTS.api import TTS

# Initializare TTS
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

# Conectare la RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()
channel.queue_declare(queue="tts_queue", durable=True)
channel.queue_declare(queue="response_queue", durable=True)

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        mesaj = data["mesaj"]
        print("[TTS] Text primit:", mesaj)
        
        # creem un nume unic pentru fisierul audio
        audio_path = f"output_{uuid.uuid4().hex}.wav"
        
        # apelam functia TTS care creeaza fisierul audio cu continutul variabilei mesaj la audio_path
        tts.tts_to_file(text=mesaj, file_path=audio_path)
        
        # deschidem fisierul, citim datele binare si le encodam in base64
        # rezultatul va fi un string ce va putea fi inclus intr-un JSON
        with open(audio_path, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        # deoarece nu mai avem nevoie de el, vom sterge fisierul de pe disk
        os.remove(audio_path)
        
        response = {
            "mesaj": mesaj,
            "audio_base64": audio_base64
        }
        
        print("[TTS] Raspunsul va fi trimis in coada:", properties.reply_to)
        channel.basic_publish(
            exchange="",
            routing_key=properties.reply_to,
            properties=BasicProperties(
                correlation_id=properties.correlation_id,
                content_type='application/json',
                delivery_mode=2
            ),
            body=json.dumps(response)
        )
    except Exception as e:
        print(f"[EROARE] in callback TTS: {e}")
        
# Ascultare pe coada
channel.basic_consume(queue="tts_queue", on_message_callback=callback, auto_ack=True)
print("[TTS] Ascult pe tts_queue...", flush=True)
channel.start_consuming()
        
        