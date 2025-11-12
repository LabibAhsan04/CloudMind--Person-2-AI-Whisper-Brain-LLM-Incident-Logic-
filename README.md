# CloudMind – Person 2 🧠  
### AI Whisper Brain | Logic & Communication Microservice  

This repository contains my individual contribution (**Person 2**) to **CloudMind**, an AI-driven microservice platform collaboratively developed with a team of students at the University at Buffalo.  
My module was responsible for handling **text-based requests**, performing **logical processing**, and managing **inter-service communication** between multiple AI microservices using **FastAPI**.

---

## 🚀 Overview  
CloudMind is a distributed AI system built using microservices architecture. Each “Person” acts as an intelligent unit with a specific role (text, logic, memory, or data).  
**Person 2** serves as the **communication and reasoning layer**, responsible for:  

- Receiving and interpreting text or logic-based queries.  
- Routing and processing data asynchronously between other AI modules.  
- Maintaining smooth inter-service communication via RESTful APIs.  
- Handling request-response synchronization with concurrency control.

---

## 🧩 Features  
- **FastAPI-based backend** for lightweight, scalable performance.  
- **Async/Await architecture** for handling multiple AI requests efficiently.  
- **API-to-API communication** to coordinate between “Person” modules.  
- **Error handling & logging** for clean and consistent responses.  
- Modular design for easy integration into larger distributed systems.  

---

## ⚙️ Tech Stack  
| Component | Technology |
|------------|-------------|
| Language | Python 3.12 |
| Framework | FastAPI |
| Libraries | Uvicorn, Requests, JSON, AsyncIO |
| Tools | Git, VS Code, Docker |
| Architecture | RESTful Microservices |

---

## 🧠 Example Workflow
1. Client sends a text request to Person 2’s FastAPI endpoint.  
2. Person 2 interprets the request and determines which service to call.  
3. The module asynchronously fetches data or logic from other “Person” services.  
4. Response is returned to the client with structured and processed output.  

```bash
# Example Run
uvicorn main:app --reload
