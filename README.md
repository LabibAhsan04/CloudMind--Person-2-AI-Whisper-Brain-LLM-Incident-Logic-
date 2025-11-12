# ☁️ CloudMind – Person 2  
### The AI Whisper Brain | LLM + Incident Logic  

This repository contains my **individual contribution (Person 2)** to **CloudMind – Inside the Cloud**, a 24-hour hackathon project built by a 4-person team at the **University at Buffalo**.  
CloudMind reimagines how cloud infrastructure communicates by giving microservices *emotions and voices* — turning system health data into a living, human-like conversation.

---

## 🌍 What Is CloudMind?

Modern cloud systems often fail not because alerts are missing, but because engineers can’t interpret hundreds of metrics fast enough.  
**CloudMind** introduces an *“emotional observability layer”* for infrastructure — letting engineers “feel” system stress instead of sifting through dashboards.

Each microservice (Frontend, API, Database, Cache, Auth) behaves like a character inspired by *Inside Out*, each with its own **emotion** and **personality**:

| Microservice | Emotion | Personality |
|---------------|----------|-------------|
| 🖥️ Frontend | Joy | Loves traffic and users |
| ⚡ API | Anger | Gets frustrated with slow responses |
| 💾 Database | Fear | Panics under heavy load |
| 💨 Cache | Sadness | Tired and fills up quickly |
| 🔐 Auth | Disgust | Snarky, rejects bad requests |

When the system experiences high load or errors, these services “talk” to each other, describing what’s happening in human-like terms:

Joy (Frontend): "Wow, traffic is booming today!"
Fear (Database): "I’m feeling stressed — too many queries!"
Anger (API): "DB, stop lagging! You’re slowing me down!"
CloudMind (System): "Scaling database replicas to handle load."


This storytelling approach helps engineers catch issues faster and understand infrastructure behavior at a glance.

---

## 🧠 What Is Person 2?

**Person 2 = AI Whisper Brain (LLM + Incident Logic)**  

My role was to build the **AI layer** that translates real-time cloud metrics into human-like emotional responses.  
This microservice acts as the *translator* between Prometheus alerts and expressive incident messages.

### 🔧 Responsibilities
- Built `llm_engine.py` to process Prometheus metrics → emotional text.  
- Designed **prompt templates** for each personality (Joy, Anger, Fear, Sadness, Disgust).  
- Integrated **Cohere/Mistral LLM APIs** for language generation.  
- Exposed `/whisper` endpoint via **FastAPI** to receive alerts and return emotional logs.  
- Sent live notifications to **Slack/Discord** through webhooks.  

### 🎯 Goal
To create an **AI voice layer** that gives infrastructure emotions — helping engineers visualize stress, failure, and healing through conversation.

---

## 🧩 System Architecture

Prometheus → Person 2 (AI Whisper Brain)
│
├── LLM Engine → Emotional Response
│
├── Webhook → Slack/Discord Alert
│
└── Sends to UI (Person 3) for Visualization

---

## 🚀 Outcome
- Built a working prototype that **translates live infrastructure metrics into emotional, human-like conversations.**  
- Enabled **real-time incident awareness** through expressive storytelling.  
- Demonstrated how observability can be *understood*, not just *monitored.*  

---

## 📚 Lessons Learned
- Integrating **LLMs** with **real-time monitoring pipelines**  
- **Prompt engineering** for consistent personality-based outputs  
- Managing asynchronous API flows between monitoring and AI services  
- Effective **team collaboration** under 24-hour hackathon constraints  

---

## 👥 Team Overview
| Role | Focus |
|------|--------|
| **Person 1** | Core Backend & Microservice Builder |
| **Person 2 (Me)** | AI Whisper Brain – LLM & Incident Logic |
| **Person 3** | Frontend & Visualization (UI/UX Engineer) |
| **Person 4** | DevOps & SRE Automation (Kubernetes + Prometheus) |

---

## 🏫 Project Context
- **Project:** CloudMind – Inside the Cloud  
- **Duration:** 24-hour hackathon  
- **University:** University at Buffalo  
- **Goal:** Combine AI language models with cloud observability to make infrastructure more intuitive and “alive.”  

---

## 🔗 Connect
👤 **Labib Ahsan**  
📍 Buffalo, NY  
📧 [labibahsan2004@gmail.com](mailto:labibahsan2004@gmail.com)  
💼 [LinkedIn](https://www.linkedin.com/in/labibahsan04) • [GitHub](https://github.com/LabibAhsan04)

---

> *“When cloud systems can whisper their emotions, engineers can finally listen before they crash.”*

---

### 🪄 GitHub “About” Description
> AI microservice (Person 2) that gives cloud infrastructure emotions using FastAPI + LLM logic.  
> Converts real-time Prometheus metrics into human-like conversations.



