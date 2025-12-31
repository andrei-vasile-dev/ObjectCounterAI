
---

# 🤖 AI Service with Flask, YOLO, and TTS

> **A modular AI ecosystem** designed to process images and text, perform object detection via **YOLOv8**, and synthesize voice responses using **Coqui TTS**, all orchestrated through **RabbitMQ**.

---

## 📝 Project Overview
This project implements a distributed AI service. It receives an image and a descriptive prompt, identifies objects using **Ultralytics YOLO**, and generates a natural-sounding audio response. The architecture is built on a producer-consumer model to ensure scalability and decoupling.

### 🚀 Key Features
*   ✅ **Object Detection:** High-performance detection using YOLOv8.
*   ✅ **Speech Synthesis:** Text-to-Audio conversion via Coqui TTS.
*   ✅ **Asynchronous Messaging:** Robust communication between services using RabbitMQ.
*   ✅ **REST API:** Centralized coordination through a Flask endpoint (`/countObjects`).
*   ✅ **Automated Testing:** Integrated validation script for end-to-end testing.

---

## 🏗️ Project Architecture

The system is organized into specialized modules for easy maintenance and scaling:

```markdown
app/
 📂 app.py                 # Main Flask REST API
 📂 message_routing.py     # RabbitMQ routing logic & thread management

images/
 📂 sample_images          # Test dataset & documentation assets

workers/
 📂 yolo_worker.py         # Object Detection service (Inference)
 📂 tts_worker.py          # Text-to-Speech synthesis service

tests/
 📂 test_request.py        # Automated endpoint testing script

📄 config.json             # RabbitMQ & Service credentials
📄 requirements.txt        # Project dependencies
```

### 🔄 System Workflow (End-to-End)
The data flows through the system following this pipeline:
`Client` → `Flask` → `task_queue` → `YOLO` → `tts_queue` → `TTS` → `response_queue` → `Flask` → `Client`

---

## 🛠️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/<your-name>/countObjects_AI.git
cd countObjects_AI
```

### 2️⃣ RabbitMQ Configuration
The message broker is essential for inter-service communication.
*   **Windows (Recommended):**
    1.  Install **Erlang**: [erlang.org/downloads](https://www.erlang.org/downloads)
    2.  Install **RabbitMQ**: [rabbitmq.com/download.html](https://www.rabbitmq.com/download.html)
    3.  Start the RabbitMQ service.
*   **Management UI:** Access [http://localhost:15672](http://localhost:15672) (Default: `guest/guest`).

### 3️⃣ Environment Setup (Anaconda)
We recommend using a dedicated environment to avoid dependency conflicts.
```bash
# Create environment
conda create -n countObjects_AI python=3.10

# Activate environment
conda activate countObjects_AI

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Running the Services

To run the full pipeline, open **4 separate terminals**, activate the environment in each, and execute the following commands in order:

```bash
# Terminal 1: Core API
python -m app.app

# Terminal 2: Computer Vision Worker
python -m workers.yolo_worker

# Terminal 3: Speech Synthesis Worker
python -m workers.tts_worker

# Terminal 4: Test Execution
python -m tests.test_request
```

---

## 📺 Demos & Visuals

Behold the system in action. *(Please allow 2-3 minutes for the GIFs to fully load due to high resolution)*.

### 🔹 Demo 1: Object Identification
![Run Test 1](https://raw.githubusercontent.com/andrei-vasile-dev/ObjectCounterAI/main/images/gif1.gif)

### 🔹 Demo 2: Complex Scenario
![Run Test 2](https://raw.githubusercontent.com/andrei-vasile-dev/ObjectCounterAI/main/images/gif2.gif)

---

## 🔍 Detailed Technical Description

The application functions as a **distributed AI system** processing JSON payloads:

**Input Request:**
 ```json
  {
    "id": "req_001",
    "text": "How many cars are represented in the image?"
  }
  ```

### **The Processing Chain:**
1.  **Flask Entry Point:** Receives the request and pushes the metadata to the `task_queue`.
2.  **YOLO Worker:** Pulls the task, performs inference using the `YOLOv8n` model, and generates a textual summary (e.g., *"There are 6 object(s) of type 'car' in the image."*).
3.  **TTS Worker:** Receives the text via `tts_queue` and uses the **Coqui TTS** library to synthesize a `.wav` file.
4.  **Data Encoding:** The audio is converted to `base64` and sent back via `response_queue`:
    ```json
    {
      "mesaj": "There are 6 object(s) of type 'car' in the image.",
      "audio_base64": "<base64_encoded_string>"
    }
    ```
5.  **Response Delivery:** The `MessageRouting` component (running in a dedicated thread within Flask) matches the response to the initial HTTP request and delivers it to the client.

---
