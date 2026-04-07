# Rosyai-v2
RosyAI Assistant is a powerful, modular virtual assistant built using Python, designed to automate tasks, process intelligent commands and enhance productivity through smart integrations. Inspired by advanced AI assistants like Jarvis, RosyAI combines voice interaction, web automation and messaging capabilities into a unified and extensible system.


# 🌸 RosyAI Assistant

RosyAI is a powerful, extensible AI assistant built using Python. It combines automation, intelligent command processing, and messaging integration (like WhatsApp) to act as a personal virtual assistant similar to Jarvis.
# 🌸 She can do conversations with you like a friend and learn new things about you
---

## 🚀 Features

- 🧠 Intelligent AI command handling  
- 💬 WhatsApp automation (send/read messages)  
- 🗣️ Voice response (Text-to-Speech)  
- 🌐 Web search & automation  
- 📊 Real-time progress updates  
- 🎯 Task automation (open apps, execute commands)  
- 🧩 Modular and scalable architecture
- 🌸 For remembering anything just say **Remember** before saying anything

---

## 📁 Project Structure

```
RosyAI/
│
├── jarvis_ai.py                  # 🚀 Main entry point (run this file)
├── rosyai3.py                   # 🧠 Core AI logic & command handling
├── command_parser.py            # 📝 Parses user commands
├── task_planner.py              # 📊 Plans tasks intelligently
├── task_executor.py             # ⚙️ Executes planned tasks
├── agent_brain.py               # 🤖 Central decision-making system
│
├── external_llm.py              # 🌐 External AI/LLM integration
├── llm_mistral.py               # 🧠 Mistral AI model integration
│
├── memory.py                    # 💾 Basic memory system
├── memory_system.py             # 🧠 Advanced memory handling
├── vector_memory.py             # 🔍 Embedding-based memory
├── rosy_memory.json             # 🗂️ Stored assistant memory
│
├── vision_loop.py               # 👁️ Continuous vision processing loop
├── screen_vision.py             # 🖥️ Screen understanding system
├── ultra_vision.py              # 🔬 Advanced vision intelligence
├── vision_yolo.py               # 🎯 Object detection (YOLO)
├── vision_memory.json           # 📸 Stores visual memory
├── camera_awarness.py           # 👥 Detects people in camera
├── camera.py                    # 📷 Camera interface
│
├── wake_word.py                 # 🎙️ Wake word detection
├── audioio.py                   # 🔊 Audio input/output processing
├── temp_voice.wav               # 🎧 Temporary voice file
│
├── web_control.py               # 🌐 Web automation (basic)
├── web_control2.py              # 🌍 Advanced web control
│
├── whatsapp_rosy.py             # 💬 WhatsApp automation module
├── whatsapp_command_handler.py  # 📩 WhatsApp command handler
│
├── file_agent.py                # 📁 File operations handler
├── code_executer.py             # 💻 Executes code dynamically
├── music_agent.py               # 🎵 Music control system
│
├── Heyrosy.ppn                 # 🎤 Wake word model (Porcupine)
│
├── modeltesting.py              # 🧪 Model testing & debugging
│
├── control/
│   └── automation.py            # 🤖 Automated voice commands
│
├── auth/
│   ├── face_auth.py             # 🧑 Face authentication system
│   ├── voice_auth.py            # 🎙️ Voice authentication
│   ├── enroll_face.py           # 📸 Register face data
│   └── enroll_voice.py          # 🎤 Register voice data
├── tts/
|   ├── sarvam_tts2.py           # 🔊 Speaking reply
|   ├── emotional_tts.py         # 🔊 Fallback if API key is not working
│
├── requirements.txt             # 📦 Project dependencies
└── README.md                    # 📘 Documentation
```

---

## 🧠 System Overview

RosyAI is designed as a **multi-agent intelligent assistant system**, combining:

- 🤖 AI reasoning (agent_brain, LLM modules)  
- 👁️ Vision intelligence (YOLO, screen & camera awareness)  
- 🎙️ Voice interaction (wake word + authentication)  
- 💬 Communication automation (WhatsApp integration)  
- 🧠 Memory systems (JSON + vector memory)  
- ⚙️ Task execution pipeline (plan → execute → respond)  

---

## 🔥 Key Capabilities

- Face + Voice Authentication 🔐  
- Real-time Camera Awareness 👥  
- Smart Task Planning & Execution ⚡  
- AI Chat + External LLM Support 🧠  
- WhatsApp Automation 💬  
- Screen + Object Detection 👁️
- Open Websites and automates youtube
- Scroll Down and up
- File, Code & Music Control 📁🎵💻
- And have many other things that you can use to automate your computer

---

> ⚡ RosyAI is not just an assistant — it's a complete AI ecosystem.

---

## ⚙️ Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/cutads-tech/Rosyai-v2.git
cd rosyai
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ System Requirements

- Python 3.10 or higher  
- Microsoft Edge (for WhatsApp Web automation)  
- EdgeDriver (matching your Edge version)  
- Internet connection  
---

## ▶️ Usage
First Download Tesseract OCR from official with latest version and also add its path to .env file, here is the link from sourceforge but you can download from official github repository

**[Tesseract-OCR](https://sourceforge.net/projects/tesseract-ocr.mirror/files/latest/download)**

Then Download **Edge Driver** (latest version) from here


**[Miscrosoft Edge Driver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)**
## Get API Keys, All API keys used in this project are free and you can get it from here free

**[Sarvam API Key for TTS]**
**[Sarvam APi](https://login.sarvam.ai)**

**[Openrouter API keys]**
**[Openrouter API](https://openrouter.ai/)**

**[Porcupine Access Key and download Key Words File saying " HEY ROSY " or other your favourite word]**
**[Porcupine Access Key](https://picovoice.ai/platform/porcupine)**

**[Google Gemini API Key]**
**[Google Gemini API Key](https://ai.google.dev/gemini-api/docs/api-key)**
## LLM MODEL
**We used Mistral 7B instruct in this project and you can use your own or any other llm model that can your pc support in running normaly**
**[Mistral 7B Instruct]**
**[Mistral 7B Instruct](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2)**

## Also configure .env file before running this code

## 📦 Dependencies

Main libraries used:

- `pyttsx3` or `gTTS` (Text-to-Speech)  
- `selenium` or `playwright` (Browser automation)  
- `requests` (API calls)  
- `json` (Data storage)  

Install all dependencies:

```bash
pip install -r requirements.txt
```

Run the assistant using:

```bash
python jarvis_ai.py
```

---

## 💡 Example Commands

- "Open YouTube"
- "Open youtube and search latest songs"
- "Send message to  on WhatsApp"
- Whatsapp command   --->     " message to Ananya saying how are you "
- "Search Python automation"  
- "Start scanning network"  
- "Tell me the weather"
- "First see rosy_ai.py code fully before running"

---

## 🧠 Vision Memory System

RosyAI can store and recall object positions using a JSON-based memory system.

### Example:

```python
import json

def save_target(name, pos):
    with open("vision_memory.json", "r") as f:
        data = json.load(f)

    data[name] = pos

    with open("vision_memory.json", "w") as f:
        json.dump(data, f)
```

---

## 🔧 Configuration

You can customize RosyAI easily:

- ✏️ Edit `rosyai3.py` → Add new commands  
- 💬 Modify `whatsapp_command_handler.py` → Improve messaging logic  
- 🚀 Extend `jarvis_ai.py` → Add new integrations  
- **`jarvis_ai.py`** This is main file you can run this file and assistant starts. 
---

## 🔒 Security Notes

- ❌ Do NOT hardcode credentials  
- 🔐 Use environment variables for sensitive data  
- ⚠️ Be cautious with automation scripts  
- 🔑 Protect API keys and tokens  

---

## 🛠️ Future Improvements

- 🤖 Advanced AI (GPT integration)  
- 📱 Android app integration
- Instagram and other apps automation
- Improve its own code
- Use your system fully
- Improve its memory
- Learn everything
- Also other things you can suggest me
---

## 🤝 Open Source

This is fully opensource , You can use it in your code and edit this code fully.

### Steps:

1. Fork the repository  
2. Create a new branch  
3. Make your changes  
4. Commit and push  
5. Open a Pull Request  

---

## 👨‍💻 Author

**Cutads-Tech**  
AI Developer | Automation Enthusiast  


---

## 📬 Contact

For support or suggestions, feel free to open an issue.

---

> ⚡ "Build your own Jarvis with RosyAI"
