
from flask import Flask, request, jsonify
import uuid
import threading

from .message_routing import MessageRouting
from .io import load_json


app = Flask(__name__)

# Incarcam fisierul config.json
config = load_json('config.json')

# Instantiem handler-ul pentru mesaje RabbitMQ
message_router = MessageRouting(config)

thread_message_routing = threading.Thread(target=message_router.run, daemon=True) # metoda run() asculta inQueue
# daemon = True -> thread secundar, programul nu asteapta ca thread-ul sa se termine. Cand script-ul principal se inchide, toate thread-urile daemon sunt oprite instant
thread_message_routing.start()

@app.route('/countObjects', methods=['POST'])
def count_objects():
    data = request.get_json()
    print("Am primit request:", data)
    
    if not data:
        return jsonify({"error": "Nu am primit date valide!"}), 400
    
    # Generam un ID unic pentru corelare (request <-> reply)
    correlation_id = str(uuid.uuid4())
    
    # Trimitem mesajul in coada YOLO si asteptam raspunsul
    # PRACTIC, aici Flask pune in responses[correlation_id] o coada locala si publica mesajul in outQueue (task_queue), cu proprietatea reply_to=inQueue (response_queue)
    result = message_router.publish_message(
        message_body=data,
        queue=config["endpoint"]["outQueue"],
        correlation_id=correlation_id,
        reply_to=config["endpoint"]["inQueue"]
    )
    
    if result is None:
        return jsonify({"error": "Timeout la asteptarea raspunsului de la worker"}), 504
    
    return jsonify(result) # app.py returneaza JSON ca raspuns HTTP catre test_request.py

if __name__ == '__main__':
    app.run(port=5000)
    
    
    
    