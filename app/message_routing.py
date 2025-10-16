
import pika
import json
import threading
from queue import Queue, Empty
import time

class MessageRouting:
    def __init__(self, config):
        self.config = config
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=config["rabbitmq"]["host"])
        )
        self.channel = self.connection.channel()
        
        self.channel.queue_declare(queue=config["endpoint"]["outQueue"], durable=True)
        self.channel.queue_declare(queue=config["endpoint"]["inQueue"], durable=True)
        
        # responses = { correlation_id: (Queue, timestamp) }
        self.responses = {}
        self.lock = threading.Lock()
        
        # Pornim thread-ul de curatare automata
        cleaner = threading.Thread(target=self.cleanup_responses, daemon=True)
        cleaner.start()
        
    # functie prin care punctul Flask solicita procesare si asteapta raspunsul worker-ilor
    # aceasta blocheaza pana functia run() primeste mesajul cu acelasi correlation_id si il pune in coada locala    
    def publish_message(self, message_body, queue, correlation_id, reply_to):
        print(f"[~] Astept raspuns cu correlation_id = {correlation_id}...")
        
        q = Queue()
        with self.lock:
            # salvam momentul inregistrarii
            self.responses[correlation_id] = (q, time.time())
            
        # Dupa ce am inregistrat correlation_id putem trimite mesajul
        self.channel.basic_publish(
            exchange='',
            routing_key=queue,
            properties=pika.BasicProperties(
                reply_to=reply_to,
                correlation_id=correlation_id,
                content_type='application/json'
            ),
            body=json.dumps(message_body)
        )
        
        try:
            # timeout mai generos pentru pipeline YOLO + TTS
            result = q.get(timeout=40) #publish_message blocheaza pana cand run() primeste mesajul cu acelasi correlation_id si il pune in coada locala
            print("[->] Raspuns primit de la worker:")
            return result
        except Empty:
            print("[X] Timeout: Nu am primit raspuns.")
            return None
    
    # functie care asculta continuu, primeste raspunsurile din cozile RabbitMQ si le livreaza catre partile care le asteapta in functia publish_message    
    def run(self):
        print("[MessageRouting] >> Thread-ul de ascultare a pornit.")
        
        def callback(ch, method, properties, body):
            correlation_id = properties.correlation_id
            
            with self.lock:
                if correlation_id in self.responses:
                    q, _ = self.responses[correlation_id]
                    q.put(json.loads(body)) # cand se intampla asta se deblocheaza functia publish_message
                    print("[=>] Raspuns livrat catre publish_message.")
                else:
                    print("[!] Raspuns intarziat, dar il ignoram (correlation_id necunoscut)")
                    
        # Creem un nou canal doar pentru ascultare
        consume_connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.config["rabbitmq"]["host"])
        )
        
        consume_channel = consume_connection.channel()
        consume_channel.queue_declare(queue=self.config["endpoint"]["inQueue"], durable=True)
        
        consume_channel.basic_consume(
            queue=self.config["endpoint"]["inQueue"],
            on_message_callback=callback,
            auto_ack=True
        )
        
        print("[MessageRouting] Ascult pe response_queue...")
        consume_channel.start_consuming() # blocheaza thread-ul in loop de consum
        
    def cleanup_responses(self):
        
        # Sterge correlation_id-urile mai vechi de 60 de secunde, pentru a preveni leak-rui de memorie.
        while True:
            now = time.time()
            with self.lock:
                to_delete = [
                    cid for cid, (_, ts) in self.responses.items()
                    if now - ts > 60
                ]
                for cid in to_delete:
                    del self.responses[cid]
                    print(f"[Cleaner] -> correlation_id expirat sters: {cid}")
            time.sleep(5)
            
    def send_stop_signal(self):
        try:
            self.connection.close()
        except:
            pass