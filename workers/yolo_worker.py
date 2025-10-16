
import json
import pika
from pika import BasicProperties
import numpy as np
from PIL import Image
from ultralytics import YOLO
import re
import os

# Incarcarea modelului YOLOv8 pre-antrenat
model = YOLO("yolov8n.pt")

# Conectarea la RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()

# Declararea cozilor
channel.queue_declare(queue="task_queue", durable=True)
channel.queue_declare(queue="tts_queue", durable=True)

def callback(ch, method, properties, body):
    print("[YOLO]: Primit task nou")
    
    data = json.loads(body)
    index = data["id"]
    text_instruction = data["text"].lower()
    
    # Cautam fisierul imaginii pe disc
    image_path = f"images/{index}.jpg"
    if not os.path.exists(image_path):
        raspuns = {
            "mesaj:": f"Imaginea cu indexul {index} nu a fost gasita."
        }
    else:
        image = Image.open(image_path).convert("RGB")
        img_array = np.array(image)
        
        # Rulam detectia Yolo pe imagine
        results = model(img_array)[0]
        
        # Extragem etichetele detectate
        labels = [model.names[int(cls)] for cls in results.boxes.cls]
        
        # Extragem obiectul cautat din intrebare
        match = re.search(r"how many\s+(\w+)", text_instruction)
        if match:
            object_plural = match.group(1)
            object_singular = object_plural.rstrip("s")
        else:
            object_singular = ""
            
        # Numaram obiectele detectate de acel tip
        numar = sum(1 for label in labels if label.lower().rstrip("s") == object_singular)
        
        raspuns = {
            "mesaj": f"There are {numar} object(s) of type '{object_singular}' in the image."
        }
        
        print("[YOLO]: Trimit raspuns in coada tts_queue:", raspuns)
        print("[YOLO] Trimit catre tts_queue cu reply_to=", properties.reply_to)
        
        channel.basic_publish(
            exchange="",
            routing_key="tts_queue",
            body=json.dumps(raspuns),
            properties=BasicProperties(
                correlation_id=properties.correlation_id,
                reply_to=properties.reply_to,
                content_type='application/json',
                delivery_mode=2  # mesaj persistent (scris pe disk, in eventualitatea ca serverul RabbitMQ este oprit, mesajul nu se pierde si va fi primit cand serverul reporneste)
            )
        )
        
channel.basic_consume(queue="task_queue", on_message_callback=callback, auto_ack=True)    
print("[YOLO]: Worker asculta pe task_queue")
channel.start_consuming()