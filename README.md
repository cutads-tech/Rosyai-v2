# Rosyai-v2
RosyAI Assistant is a powerful, modular virtual assistant built using Python, designed to automate tasks, process intelligent commands and enhance productivity through smart integrations. Inspired by advanced AI assistants like Jarvis, RosyAI combines voice interaction, web automation and messaging capabilities into a unified and extensible system.
# 🌸 RosyAI Assistant

RosyAI is a powerful, modular AI assistant built using Python. It combines voice interaction, computer vision, task automation, and messaging integration into a single intelligent system inspired by Jarvis.

RosyAI is designed as a **multi-agent AI ecosystem**, capable of understanding commands, planning tasks, executing actions, and interacting with the real world using voice, camera, and web automation.

---

## 🚀 Features

- 🧠 Intelligent command understanding & execution  
- 🎙️ Wake word detection (Hey Rosy)  
- 🔐 Face + Voice authentication system  
- 👁️ Real-time camera awareness (detect people)  
- 🖥️ Screen & object detection (YOLO + OCR)  
- 💬 WhatsApp automation  Example - "say message to Ananya saying Hello"
- 🌐 Web automation & control  
- 📊 Task planning and execution pipeline  
- 🧩 Modular architecture (easy to extend)  
- 🧠 Memory system (JSON + vector memory)  

---

## 📁 Project Structure

```
RosyAI/
│
├── jarvis_ai.py                  # 🚀 Main entry point
├── rosyai3.py                   # 🧠 Core AI logic
├── command_parser.py            # 📝 Command parser
├── task_planner.py              # 📊 Task planner
├── task_executor.py             # ⚙️ Task executor
├── agent_brain.py               # 🤖 AI brain
│
├── external_llm.py              # 🌐 External LLM APIs
├── llm_mistral.py               # 🧠 Mistral integration
│
├── memory.py                    # 💾 Basic memory
├── memory_system.py             # 🧠 Advanced memory
├── vector_memory.py             # 🔍 Vector memory
├── rosy_memory.json             # 📂 Stored memory
│
├── vision_loop.py               # 👁️ Vision loop
├── screen_vision.py             # 🖥️ Screen understanding
├── ultra_vision.py              # 🔬 Advanced vision
├── vision_yolo.py               # 🎯 Object detection
├── vision_memory.json           # 📸 Vision memory
├── camera_awarness.py           # 👥 Camera awareness
├── camera.py                    # 📷 Camera interface
│
├── wake_word.py                 # 🎙️ Wake word detection
├── audioio.py                   # 🔊 Audio processing
├── temp_voice.wav               # 🎧 Temp audio file
│
├── web_control.py               # 🌐 Web automation
├── web_control2.py              # 🌍 Advanced web control
│
├── whatsapp_rosy.py             # 💬 WhatsApp automation
├── whatsapp_command_handler.py  # 📩 WhatsApp commands
│
├── file_agent.py                # 📁 File handling
├── code_executer.py             # 💻 Code execution
├── music_agent.py               # 🎵 Music control
│
├── Heyrosy.ppn                  # 🎤 Wake word model
├── modeltesting.py              # 🧪 Testing
│
├── control/
│   └── automation.py            # 🤖 Automation system
├── tts/
│   ├── emotional_tts.py         # Offline TTS fallback
│   ├── sarvam_tts2.py           # Main TTS rendering
│
├── auth/
│   ├── face_auth.py             # 🧑 Face authentication
│   ├── voice_auth.py            # 🎙️ Voice authentication
│   ├── enroll_face.py           # 📸 Enroll face
│   └── enroll_voice.py          # 🎤 Enroll voice
│
├── requirements.txt             # 📦 Dependencies
└── README.md                    # 📘 Documentation
```

---

## ⚙️ Installation

### 1️⃣ Clone Repo
```bash
git clone https://github.com/cutads-tech/Rosyai-v2.git
cd Rosyai-v2
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 First Configure .env file and other tools and all APIs are free

### 🧠 LLM APIs

- **OpenRouter (FREE models available)**  
  👉 **[Openrouter API Key](https://openrouter.ai/)**

- **Google Gemini API (Free tier)**  
  👉 **[Google API Key](https://ai.google.dev/)**

- **Mistral 7B Instruct (Free / Open)**  
  👉 **[Mistral 7B Instruct](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2)**

---

### 🔊 Text-to-Speech

- **Sarvam TTS (Free)**  
  👉 **[Sarvam TTS](https://www.sarvam.ai/)**

---

### 🎙️ Wake Word Detection

- **Porcupine Access Key (Free tier)**  
  👉 **[Porcupine Access Key](https://console.picovoice.ai/)**

  **If you want to use any other wake word then get wake words PPN file from above link and save rename it to Heyrosy.ppn**

---

### 🌐 Browser Automation

- **Microsoft Edge WebDriver**  
  👉 **[Edge Driver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)**

---

### 👁️ OCR (Text Detection)

- **Tesseract OCR (Free & Open Source)**  
  👉 **[Tesseract OCR](https://github.com/tesseract-ocr/tesseract)**

---
### 3️⃣ Run Assistant
```bash
python jarvis_ai.py
```
## 🧠 System Architecture

RosyAI works in a pipeline:

```
Voice Input / Command
        ↓
Command Parser
        ↓
Agent Brain (AI Decision)
        ↓
Task Planner
        ↓
Task Executor
        ↓
Modules (Vision / WhatsApp / Web / File)
        ↓
Voice Output / Action
```

---

## 🔥 Key Capabilities

- 🔐 Secure authentication (face + voice)  
- 🤖 AI-based decision making  
- 👁️ Real-time vision processing  
- 💬 Messaging automation  
- 🌐 Web control  
- 🧠 Memory + learning system  for remembering just say "remember" before anythig and she remembers that thing
- Send Messages to whatsapp
- Scroll Up and Down
- Automate commands
- Control Browser
- Open and search on youtube and can do many other things

---

## 🔒 Security Notes

- Do NOT expose API keys  
- Use `.env` file for secrets  
- Keep authentication data secure  

---

## 🛠️ Future Improvements

- 🧠 Self-learning AI  
- 📱 Android app integration  
- 🎙️ Better voice recognition  
- 🌍 Multi-language support  
- 🤖 Autonomous task execution
- Improve its own code
- If you want to add another feature tell me
---
# IMPORTANT
**We did not use voice and face authentication in this code but filed are there, you can integrate these code files if you have clear camera in your PC**
## 🤝 Contributing

1. Fork repo  
2. Create branch  
3. Make changes  
4. Commit & push  
5. Open Pull Request  

---

## 👨‍💻 Author

**Cutads-Tech** 

---

> ⚡ Build your own Jarvis with RosyAI
