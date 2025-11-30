## 🚀 Project Roadmap **LLM‑Router**

### 📍 Level 1 – **Dev / Test**

**Current stage** – we are introducing core features and integrations.

| Task                                                                   | Goal                                                       | Status         |
|------------------------------------------------------------------------|------------------------------------------------------------|----------------|
| Finish integration with **LM Studio**                                  | Full support for local models                              | 🔄 in progress |
| Streamed return of **guardrails**                                      | Response delivered as a stream instead of a single payload | 🔄 in progress |
| Integration with the native **Anthropic** API                          | Support Anthropic beyond the OpenAI layer                  | 🔄 in progress |
| Extend masking rules (EN, US)                                          | Better data protection for English (US) languages          | 🔄 in progress |
| Add a **guardrails** service for *prompt injection*                    | Detect and block unwanted prompts                          | 🔄 in progress |
| Update the frontend for **ConfigsManager** and **Anonymizer** (+ chat) | Friendly UI for managing configurations and anonymization  | 🔄 in progress |
| API support for **RAG‑style** (embeddings)                             | Support for RAG‑type applications for handling embeddings  | 🔄 in progress |

---

### 📍 Level 2 – **Prod**

**Introducing LLM‑Router** as a component of a distributed production ecosystem.

| Area            | Initiative                                                      | Description                                                   |
|-----------------|-----------------------------------------------------------------|---------------------------------------------------------------|
| **Scalability** | Solutions that allow scaling LLM‑Router for very specific tasks | Modular architecture, autoscaling in a private cloud          |
| **Security**    | Mechanisms based on **Kafka** communication (task queuing)      | Task isolation, monitoring, retry‑policy                      |
| **Agenticity**  | Integration with local agent systems                            | Collaboration with local agents, e.g., code‑generating agents |

---

### 📍 Level 3 – **Pain**

**Solving key business problems**.

| Category                         | Action                                                                                      | Benefit                                                           |
|----------------------------------|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| **Security and data protection** | Integration with **SIEM** (Security Information & Event Management) systems                 | Early incident detection and full auditability                    |
| **Scalability**                  | Introduce **llm‑router‑node** as a layer operating in multiple sub‑nets (router integrator) | Distributed processing, subnet integration, increased performance |
| **Document transfer**            | Secure document transfer in web applications (API + WEB)                                    | Layer ensuring document safety, full auditability                 |

---

### 📍 Level 4 – **Future**

**Long‑term, research projects** – building cutting‑edge solutions.

| Project                                                | Description                                             | Potential Impact                                      |
|--------------------------------------------------------|---------------------------------------------------------|-------------------------------------------------------|
| **llm‑router‑grpc**                                    | RPC protocol for broadcasting tasks in trusted sub‑nets | Ultra‑low latency, efficient inter‑node communication |
| **llm‑router‑protocol**                                | Communication based on **blockchain**                   | Immutability, transparency, resistance to tampering   |
| **Integration of LLM‑Router with gRPC and blockchain** | The most secure solution for information transmission   | Comprehensive security, auditable data flow           |

---

### 🎯 Summary

The roadmap clearly defines development stages from a **pilot test environment** to **global, research‑driven
innovations**. Each level focuses on specific priorities – from integration and basic functionality, through scalability
and production‑grade security, to advanced data‑protection solutions and distributed processing. This approach gives the
project solid foundations while remaining open to future breakthrough technologies.