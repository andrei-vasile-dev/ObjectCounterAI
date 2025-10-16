
import requests
import base64
import uuid
import os
from playsound import playsound

url = "http://127.0.0.1:5000/countObjects"

payload = {
    "id": 3,
    "text": "How many cars are represented in the image?"
}

print("[TEST] Trimit request catre server...")
response = requests.post(url, json=payload)

print("Status code:", response.status_code)

if response.status_code == 200:
    try:
        data = response.json()
    except ValueError:
        print("Raspunsul nu este JSON valid!")
        print(response.text)
        exit(1)
        
        
    mesaj = data.get("mesaj", "(fara mesaj)")
    audio_base64 = data.get("audio_base64", None)
    
    print("\nRaspuns text:", mesaj)
    
    if audio_base64:
        # Creem folder pentru raspunsuri, daca nu exista
        os.makedirs("responses", exist_ok=True)
        audio_filename = os.path.join("responses", f"response_{uuid.uuid4().hex}.wav")
        
        try:
            # Decodam fisierul audio si il salvam local
            audio_bytes = base64.b64decode(audio_base64)
            with open(audio_filename, "wb") as f:
                f.write(audio_bytes)
            
            print(f"Fisier audio salvat ca: {audio_filename}")
        
            # Redam automat fisierul audio
            try:
                playsound(audio_filename)
            except Exception as e:
                print(f"[Atentie] Nu am putut reda automat sunetul: {e}")
                
        except Exception as e:
            print(f"[Eroare] Nu s-a putut salva fisierul audio: ", {e})
else:
    print("Eroare:", response.text)
        