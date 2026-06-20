# Project Requirements — Master IT 2026

> Source: `ProjectsMasterIT2026.pdf`
> **Supervised by:** Abdelhak Mahmoudi
> **Co-Supervised by:** Saad Frihi and Yasine Lehmiani
> Master IT — April, 2025-2026

---

## General Goal (what the professor wants)

All three proposed projects share the same intent, which defines how the work is
evaluated:

1. **Healthcare / pharmacy domain in a Moroccan multilingual context** — the
   solutions must handle **Arabic, Darija, and French** (and code-mixed input).
   This multilingual aspect is the core difficulty, not an afterthought.
2. **Deliver a real, working API service** — every project must be exposed
   through an API that an external application could call. A notebook or a script
   alone is not acceptable.
3. **Own and adapt the ML model — do NOT just wrap a commercial API.** The
   professor wants the model to be *fine-tuned / trained / adapted* to the
   domain and to the local languages using your own prepared dataset. Wrapping a
   black-box SaaS API (e.g. generic chat or speech API) is not the goal, because
   there would be no ML contribution to evaluate. Dataset construction and model
   implementation are explicitly graded deliverables.

---

## Project #1: Arabic/Darija Patient Assistance Chatbot API

**Context:** Users express medication needs through short, incomplete, informal,
or voice-based messages, often mixing Arabic, Darija, and French. An intelligent
assistant should interpret these and turn them into structured information for
downstream systems.

**Description:** Design and implement an intelligent chatbot service, exposed via
an API, that helps users formulate medication-related requests. It accepts text
and/or voice input, analyzes content, identifies user intent, and extracts
relevant info (medication names, quantities, other details). It must support
multilingual / code-mixed interaction (Arabic, Darija, French) and return a
**structured interpretation** of the request — not only free-form responses.
Combines NLP, speech processing, and backend API development.

**Main Objectives**
- Design a conversational assistance system for medication-related requests
- Process user input in text and/or voice format
- Support multilingual / code-mixed interaction (Arabic, Darija, French)
- Extract useful structured information from unstructured requests
- Expose the final system through an API

**Expected Output**
- Study of the problem and related work
- Design of the chatbot architecture and processing pipeline
- Implementation of the NLP and/or speech processing components
- Development of an API service for interacting with the system
- Test scenarios and evaluation of the obtained results

---

## Project #2: Medication Box Recognition API Using Computer Vision and OCR

**Context:** Recognizing a medication from an image of its box is useful but
challenging: visual similarity between products, varying image quality, and
multilingual text (Arabic and French) on packaging. Reliable identification
requires combining image analysis with text extraction and matching.

**Description:** Develop a service that recognizes a medication from a
user-provided image. It analyzes the visual content, extracts text via **OCR**,
and compares results against a **reference medication database** to identify the
most likely product. Particular attention to multilingual packaging and
robustness under realistic conditions (blur, lighting variation, partial
visibility). Delivered as an API. Combines computer vision, OCR, text matching,
and backend service development.

**Main Objectives**
- Study medication identification from packaging images
- Develop a computer vision and OCR pipeline for recognition
- Handle Arabic and French text appearing on medication boxes
- Match extracted information against a medication reference database
- Expose the final recognition system through an API

**Expected Output**
- Review of methods related to OCR and image-based recognition
- Design of the proposed recognition pipeline
- Construction or preparation of a medication image dataset
- Implementation of the recognition and matching system
- Development of an API for querying the service
- Experimental evaluation and analysis of system performance

---

## Project #3: Medication Demand Prediction and Restocking Recommendation API

**Context:** Efficient inventory management is a major challenge in pharmacy.
Poor demand anticipation causes stock shortages, missed sales, or overstocking.
Predictive models based on historical sales, purchases, and stock movements
support better inventory planning.

**Description:** Develop a predictive service that analyzes historical
pharmacy-related data to estimate future medication demand and generate
restocking recommendations. It uses past sales, purchase records, and stock
levels to identify consumption patterns and decide which products to replenish.
The solution must not be limited to a forecasting model — it must be an
**API-based service** integrable into external information systems. Combines data
analysis, ML forecasting, and service-oriented software development.

**Main Objectives**
- Study demand forecasting and stock management in the pharmaceutical domain
- Analyze historical inventory, purchase, and sales data
- Develop models for demand prediction and restocking support
- Generate structured recommendations for inventory management
- Expose the final system through an API

**Expected Deliverables**
- Analysis of the business and data context of demand prediction
- Preparation and structuring of historical stock and sales data
- Development of forecasting and recommendation models
- Implementation of an API service for prediction and decision support
- Experimental evaluation of the proposed approach

---

## Submission Requirements (apply to all projects)

**Deadline:** June 15th, 2026
> ⚠️ Note: the PDF footer reads "April, 2025-2026" and the stated deadline has
> already passed relative to the current date — confirm the actual deadline with
> the supervisor.

**Deliverables**
1. A Google Drive link to the **PPTX presentation** of the project.
2. A link to the **GitHub repo** containing:
   - The code
   - A `README.md` documenting the source code and the development environment
     setup.
3. A Google Drive link to the **video presentation** covering project
   explanation, environment setup, and a Demo. The video **must not exceed 7
   minutes**.

**Submission Link:** https://forms.gle/pDmMm6HW2BRRN9ZL6
