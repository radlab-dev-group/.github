## 🚀 Poziom 1 (dev/test)

Ten poziom aktualnie się dzieje, kolejne funkcjonalności są na bieżąco aktualizowane

- ✅ Dokończyć integrację z LM Studio
- ✅ Odpowiedź z guardrails zwracana jako strumień dla strumienia
- ✅ Integracja z natywnym api Anthropic (aktualnie możliwa integracja przez standard OpenAI)
- Rozszerzenie reguł maskowania (EN, US)
- Dodanie serwisu dla guardrails typu prompt injection
- Uaktualnić frontend dla ConfigsManagera oraz Anonimizera (+chat)
- ✅ Obsługa API do aplikacji RAG-style (embeddings)

---

## ⚙️ Poziom 2 (prod)

Ten poziom, wprowadza llm-router jako element większego ekosystemu

- **Skalowalność**: Udostępnie rozwiązania umożliwiajacego wyskalowanie `llm-routera` do bardzo specyficznych zadań
- **Bezpieczeństwo**: Wprowadzenie mechanizmów opartych o komunikację w Kafce (wysyłane są zadania)
- **Agentowość**: Integracja z lokalnymi systemami egentowymi

---

## 🛡️ Poziom 3 (pain)

Ten poziom, rozwiązuje problemy biznesowe

- **Bezpieczeństwo i ochrona danych**: Integracja z systemami typu SIEM
- **Skalowalność**: `llm-router-node` jako warstwa działająca w róznych podsieciach (integrator routerów)
- **Przesyłanie dokumentów**: bezpieczne przesyłanie dokumentów w rozmowach typu chat

---

## 🔮 Poziom 4 (future)

Ten poziom, zawiera bardzo dalekosiężne plany, są to projekty badawcze

- Protokół RPC dla rozgłaszania zadań w zaufanych podsieciach (`llm-router-gprc`)
- Komunikacja oparta na przesyłaniu informacji w blockchain (`llm-router-protocol`)
- Integracja `llm-router` z `llm-router-gprc` oraz `llm-router-protocol` jako najbezpieczniejszego rozwiązania do
  przesyłania informacji