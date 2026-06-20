# Technical Design Documents (TDDs)

Design docs for the **Multilingual Smart Airport Wayfinding Assistant**. Start
with TDD-00; each component has its own TDD. Track execution in
[`../PROGRESS.md`](../PROGRESS.md).

| TDD | Component | Status |
|---|---|---|
| [TDD-00](TDD-00-System-Overview.md) | System overview & architecture (master) | 🟢 |
| [TDD-01](TDD-01-ASR-Whisper.md) | STT — fine-tuned Whisper (Darija/Arabic) | 🟡 |
| [TDD-02](TDD-02-LLM-Agent.md) | LLM agent (LangGraph orchestration) | ⚪ |
| [TDD-03](TDD-03-Agent-Tools.md) | Agent tools + flight data API | ⚪ |
| [TDD-04](TDD-04-RAG-KnowledgeBase.md) | Airport knowledge base & RAG | ⚪ |
| [TDD-05](TDD-05-TTS.md) | Text-to-Speech (multilingual) | ⚪ |
| [TDD-06](TDD-06-Backend-API.md) | Backend REST API & WebSockets | ⚪ |
| [TDD-07](TDD-07-Frontend.md) | Web demo frontend (Next.js) | ⚪ |
| [TDD-08](TDD-08-Evaluation.md) | Evaluation & testing | ⚪ |
| [TDD-09](TDD-09-Deployment.md) | Deployment & DevOps (Docker) | ⚪ |

**Template per TDD:** Purpose → Requirements satisfied → Design/Architecture →
Interfaces & data contracts → Dependencies → Open questions/risks → Task checklist.

Legend: ⚪ Not started · 🟡 In progress · 🟢 Done · 🔵 Blocked
