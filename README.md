# Multimodal Conversational Emotion and Social Intent Detection

**An AI-powered system for understanding emotions, stress, and social intent through text, voice, and conversational context.**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white" alt="PyTorch" />
  <img src="https://img.shields.io/badge/BERT-111827?logo=huggingface&logoColor=FFBF00" alt="BERT" />
  <img src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white" alt="SQLite" />
</p>

## Overview

Digital conversations often lack the emotional context conveyed through voice, tone, and speaking patterns. Text-only analysis may overlook these signals, while voice-only analysis may miss the semantic meaning of a conversation.

This project explores **multimodal conversational intelligence** by combining Natural Language Processing (NLP), speech feature extraction, and multimodal fusion to identify emotional patterns and social intent.

The system analyzes:

- Text messages using BERT-based NLP.
- Voice recordings using acoustic features such as MFCC, pitch, and energy.
- Chat screenshots using OCR-based text extraction.
- Historical conversational data to generate relationship-related analytics.

The outputs include emotion predictions, social intent, stress indicators, confidence scores, and historical trends.

## Key Features

| Feature | Description |
|---|---|
| Text Emotion Analysis | Detects emotional patterns and social intent from text using BERT. |
| Voice Emotion Analysis | Extracts acoustic features to estimate vocal emotion, stress, and intensity. |
| Multimodal Fusion | Combines text and voice predictions for conversational analysis. |
| Screenshot Analysis | Extracts conversation text from uploaded screenshots using OCR. |
| Conversation History | Stores analyzed conversations for historical reference. |
| Relationship Analytics | Generates day-wise conversational and relationship metrics. |
| Relationship Stage Tracking | Tracks relationship stages using historical conversational patterns. |
| Analytics Timeline | Provides a last-seven-day view of conversational trends. |

## System Architecture

The project follows a modular architecture consisting of text processing, voice processing, multimodal fusion, and conversation analytics.

### Processing Pipeline

1. **Input Collection** – Accepts text messages, voice recordings, or chat screenshots.
2. **Text Processing** – Processes textual input using preprocessing and BERT-based emotion and intent analysis.
3. **Voice Processing** – Extracts acoustic features including MFCC, pitch, and energy.
4. **Multimodal Fusion** – Combines the outputs from text and voice analysis.
5. **Conversation Storage** – Stores messages, predictions, and related metrics.
6. **Relationship Analytics** – Uses historical conversational information to calculate trends and relationship-related indicators.
7. **Visualization** – Presents analysis results and historical trends through the frontend.

### High-Level Architecture

```text
                 USER INPUT
                      |
          +-----------+-----------+
          |           |           |
        TEXT        VOICE      SCREENSHOT
          |           |           |
          v           v           v
       BERT       AUDIO         OCR
      ANALYSIS   FEATURES    EXTRACTION
          |           |           |
          |           |       EXTRACTED
          |           |         TEXT
          |           |           |
          +-----------+-----------+
                      |
                      v
              MULTIMODAL FUSION
                      |
                      v
              FINAL PREDICTIONS
                      |
          +-----------+-----------+
          |           |           |
        Emotion    Social       Stress
                  Intent
                      |
                      v
             CONVERSATION STORAGE
                      |
                      v
            RELATIONSHIP ANALYTICS
                      |
                      v
               FRONTEND DASHBOARD
```

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic |
| NLP | BERT, Hugging Face Transformers |
| Deep Learning | PyTorch |
| Machine Learning | Scikit-learn |
| Audio Processing | Librosa, MFCC, Pitch, Energy |
| OCR and Image Processing | OpenCV, Tesseract OCR, Pillow |
| Database | SQLite |
| ORM / Database Layer | SQLAlchemy |

## Model and AI Components

### 1. Text Modality

**Primary Model: BERT**

The text processing pipeline uses BERT-based contextual representations to analyze conversational text.

Key components:
- Text preprocessing and tokenization.
- Contextual language representation.
- Emotion classification.
- Social intent prediction.

### 2. Speech Modality

The voice processing pipeline extracts acoustic characteristics from speech recordings.

Features include:
- **MFCC:** Represents spectral characteristics of speech.
- **Pitch:** Captures variations in vocal frequency.
- **Energy:** Measures vocal intensity.

These features support voice-level emotion, stress, and intensity estimation.

### 3. Multimodal Fusion

The fusion layer combines the predictions generated by the text and voice pipelines.

It uses weighted multimodal combination to estimate:
- Final emotion.
- Social intent.
- Stress level.
- Prediction confidence.

This approach aims to reduce ambiguity when textual meaning and vocal expression provide different signals.

## API Documentation

The backend exposes REST API endpoints through FastAPI.

Interactive API documentation is available at:

`http://localhost:8005/docs`

### Health and Service

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |

### Text, Voice and Fusion

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/text/analyze` | Analyzes conversational text |
| POST | `/api/v1/voice/analyze` | Analyzes voice recordings |
| POST | `/api/v1/fusion/analyze` | Performs multimodal analysis |

### Conversation Analytics

| Method | Endpoint | Description |
|---|---|---|
| POST | `/test-chat` | Test conversational analysis |
| POST | `/analyze-chat` | Analyzes conversation text |
| POST | `/analyze-chat-image` | Extracts and analyzes chat screenshot content |
| GET | `/conversations/{conversation_id}/relationship-summary` | Retrieves relationship analytics |

## Project Structure

```text
Emotion_detection-austin_commits/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── db/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   │
│   ├── requirements.txt
│   └── scripts/
│
├── publicmain/
│   ├── src/
│   │   ├── components/
│   │   │   └── frontend/
│   │   ├── lib/
│   │   └── pages/
│   │
│   └── package.json
│
└── README.md
```

## Getting Started

### Prerequisites

Make sure you have the following installed:

- Python 3.10 or later.
- Node.js and npm.
- Git.

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd Emotion_detection-austin_commits
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

Backend will be available at:

- API: `http://localhost:8005`
- Swagger Documentation: `http://localhost:8005/docs`

### 3. Frontend Setup

Open another terminal and navigate to the frontend directory:

```bash
cd publicmain
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Frontend:

`http://localhost:8080`

> Make sure the frontend API configuration points to the correct backend URL.

## Results and Observations

The project explores the benefits of combining textual and acoustic information for conversational emotion analysis.

The current system focuses on:

- Improving conversational interpretation beyond text-only analysis.
- Incorporating vocal characteristics to identify tone-driven ambiguity.
- Classifying social intent into categories such as friendly, romantic, and neutral.
- Generating historical conversational trends through day-wise and seven-day analytics.

*Quantitative performance metrics and evaluation results can be added here once benchmark testing is documented.*

## Future Improvements

- Fine-tune BERT using larger and more diverse conversational datasets.
- Improve speaker-aware voice emotion modeling.
- Introduce authentication and user-level conversation ownership.
- Expand long-term relationship and conversational analytics.
- Improve multimodal fusion using more advanced architectures.
- Add comprehensive model evaluation and performance benchmarking.

## Team

| Name | Role |
|---|---|
| Adithyan C P | Research and Documentation |
| Austin Shajan | UI UX |
| Francis Anto | Backend Developer  |
| George Attokaran Jose | Backend Developer |

## References

1. Poria, S. et al. (2017). *Multimodal Sentiment Analysis: Addressing Key Issues and Setting Up the Baselines.*
2. Devlin, J. et al. (2019). *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding.* NAACL-HLT.
3. Busso, C. et al. (2008). *IEMOCAP: Interactive Emotional Dyadic Motion Capture Database.*

---

<p align="center">
  <strong>Multimodal Conversational Intelligence</strong><br/>
  <sub>Understanding conversations beyond words.</sub>
</p>