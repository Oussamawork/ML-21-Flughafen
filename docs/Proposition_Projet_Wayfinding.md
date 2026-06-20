# Multilingual Smart Airport Wayfinding Assistant

**Université Mohammed V – Faculté des Sciences de Rabat**
**Case Study: Sheikh Zayed International Airport (AUH), Abu Dhabi**

*(Approved project proposition — domain differs from the supervisor's pharmacy
project list but follows the same requirements. See `../PROJECT_REQUIREMENTS.md`.)*

## Context

Modern airports are complex, fast-paced environments where passengers must
simultaneously process real-time information: gate changes, flight delays,
service locations, and tight schedules. This is especially acute in multilingual
hubs such as Sheikh Zayed International Airport (AUH), where passengers
communicate in Arabic, English, French, Urdu, and many other languages. Existing
airport information systems rely on static displays and generic announcements
that do not adapt to the individual passenger's situation or preferred language.
An intelligent conversational assistant, connected to live flight data and able
to understand multiple languages, is a high-impact, scalable solution.

## Project Description

Design and implement a **general-purpose intelligent airport wayfinding
assistant**, accessible through a voice and/or text interface, that guides
passengers throughout their airport journey. It processes requests in multiple
languages, identifies the passenger's intent, and responds contextually and
personally. The primary case study is AUH, but the architecture is
**airport-agnostic** and deployable at any international airport with minimal
reconfiguration.

The solution is built on an **agentic architecture**: an LLM orchestrates
specialized tools — real-time flight status lookup, gate/terminal navigation,
nearby services search (restaurants, pharmacies, lounges), and a structured
airport knowledge base queried through **Retrieval-Augmented Generation (RAG)**.
It integrates a **Speech-to-Text (STT)** and **Text-to-Speech (TTS)** pipeline
for hands-free interaction, and is exposed through a **REST API** with a web
interface for demonstration.

**Example interaction:** a passenger asks in Arabic *"ayna bawwabati, rihlati
SV-624"* — the system detects the language, queries the live flight API,
retrieves gate/terminal info from the airport layout, and responds vocally in
Arabic with step-by-step navigation and the updated boarding time.

## Main Objectives

- Design a general-purpose agentic architecture based on an LLM with tool-calling
- Integrate a real-time flight data API (status, gate assignments, delays)
- Implement a multilingual STT/TTS pipeline supporting Arabic, English, French, Darija
- Build a modular, airport-agnostic knowledge base queryable through RAG
- Demonstrate the full system on AUH as a reference case study
- Expose the system through a REST API and an interactive web interface

## Expected Output

- Study of the problem and related work: LLM agents, multilingual NLP (Arabic/Darija), indoor airport navigation
- Design of the system architecture and processing pipeline
- Implementation of the agent tools (flight status, gate finder, services, FAQ)
- Development of the multilingual STT/TTS pipeline with Darija support
- Construction of a reusable airport knowledge base, demonstrated on AUH
- Development of a REST API and a web demonstration interface
- Evaluation of system performance: comprehension accuracy, response latency, answer quality

## Proposed Technology Stack

- **LLM Agent:** LangGraph / LangChain with GPT-4o-mini or Llama 3.1 (via Groq)
- **Speech Recognition:** OpenAI Whisper — **fine-tuned for Arabic/Darija** (see `../asr_finetuning/`)
- **Speech Synthesis:** ElevenLabs or Azure Cognitive Speech Services
- **Flight Data API:** AviationStack or AeroDataBox
- **Vector Database (RAG):** ChromaDB
- **Backend:** FastAPI with WebSockets for real-time interaction
- **Frontend:** Next.js / React with voice interface
- **Containerization:** Docker, deployed on Railway or Render
