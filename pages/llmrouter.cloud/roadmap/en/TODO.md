## 🚀 Level 1 (dev/test)

This level is currently ongoing, and new features are being updated continuously.

- Complete integration with LM Studio
- Guardrails response returned as a stream for streaming
- Integration with the native Anthropic API (currently possible via the standard OpenAI API)
- Extend masking rules (EN, US)
- Add a service for prompt‑injection‑type guardrails
- Update the frontend for ConfigsManager and Anonymizer (+chat)
- API support for RAG‑style applications (embeddings)

---  

## ⚙️ Level 2 (prod)

This level introduces **llm-router** as a component of a larger ecosystem.

- **Scalability**: Provide solutions that enable scaling `llm-router` for very specific tasks
- **Security**: Introduce mechanisms based on Kafka communication
- **Agenticity**: Integration with local agent systems

---  

## 🛡️ Level 3 (pain)

This level addresses business problems.

- **Security and data protection**: Integration with SIEM‑type systems
- **Scalability**: `llm-router-node` as a layer operating in various subnets (router integrator)
- **Document transfer**: Secure document transfer in chat‑style conversations

---  

## 🔮 Level 4 (future)

This level contains very long‑term plans; these are research projects.

- RPC protocol for broadcasting tasks in trusted subnets (`llm-router-grpc`)
- Communication based on transmitting information over blockchain (`llm-router-protocol`)
- Integration of `llm-router` with `llm-router-grpc` and `llm-router-protocol` as the most secure solution for
  information transmission  