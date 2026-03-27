<h1 align="center">Multimodal Conversational Emotion and Social Intent Detection</h1>

<p align="center">
	AI-powered conversation understanding using <strong>BERT + Speech Features + Multimodal Fusion</strong>
</p>

<p align="center">
	<img src="https://img.shields.io/badge/BERT-111827?logo=huggingface&logoColor=FFBF00" alt="BERT" />
	<img src="https://img.shields.io/badge/Voice-MFCC%20%7C%20Pitch%20%7C%20Energy-6D28D9" alt="Voice Features" />
	<img src="https://img.shields.io/badge/Fusion-Multimodal-0EA5E9" alt="Fusion" />
	<img src="https://img.shields.io/badge/Database-SQLite-003B57" alt="SQLite" />
</p>

<p align="center">
	Detect emotion, stress, and social intent from chat text, voice clips, and chat screenshots with history-aware relationship analytics.
</p>

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white)
![Transformers](https://img.shields.io/badge/HuggingFace_Transformers-FFBF00?logo=huggingface&logoColor=black)
![BERT](https://img.shields.io/badge/BERT-111827?logo=huggingface&logoColor=FFBF00)

## Team
- Adithyan C P
- Austin Shajan
- Francis Anto
- George Attokaran Jose

**Guide / Mentor:** Ms. Sabira P S, Assistant Professor, Department of Computer Science and Engineering

## Abstract
Digital communication often loses emotional clarity when only text is used. This project combines Natural Language Processing and speech analysis to improve emotion and intent detection.

The text pipeline uses **BERT** as the core NLP model, while speech is analyzed using acoustic features such as MFCC, pitch, and energy. A multimodal fusion layer combines both outputs to generate final emotion and social intent predictions with improved robustness and reduced ambiguity.

## Why This Project
- Text-only sentiment analysis misses tone and vocal context.
- Speech-only analysis misses semantic context.
- Multimodal fusion improves interpretability for conversational intelligence.

## Core Features
- Text emotion and intent analysis
- Voice stress and emotional intensity analysis
- Multimodal text+voice fusion endpoint
- OCR-based chat screenshot analysis
- Persistent conversation storage
- Day-wise relationship metrics
- Relationship stage tracking
- Last 7-day analytics timeline

## Model and AI Stack
### Text Modality
- **Primary model: BERT**
- Tokenization and text preprocessing
- Emotion and social intent prediction

### Speech Modality
- Feature extraction: MFCC, pitch, energy
- Voice-level stress and emotional intensity inference

### Fusion
- Weighted multimodal combination of text and voice outputs
- Final emotion, social intent, stress, and confidence estimation

## Tech Stack (with icons)
| Layer | Tools |
|---|---|
| Frontend | ![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black) ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white) ![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white) ![Tailwind CSS](https://img.shields.io/badge/Tailwind-06B6D4?logo=tailwindcss&logoColor=white) |
| Backend | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white) ![Pydantic](https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=white) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?logo=sqlalchemy&logoColor=white) ![BERT](https://img.shields.io/badge/BERT-111827?logo=huggingface&logoColor=FFBF00) |
| ML / Signal | ![Transformers](https://img.shields.io/badge/Transformers-FFBF00?logo=huggingface&logoColor=black) ![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white) ![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikitlearn&logoColor=white) ![Librosa](https://img.shields.io/badge/Librosa-A400FF?logo=python&logoColor=white) |
| OCR / Imaging | ![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?logo=opencv&logoColor=white) ![Tesseract](https://img.shields.io/badge/Tesseract-OCR-2F7DB8) ![Pillow](https://img.shields.io/badge/Pillow-3776AB?logo=python&logoColor=white) |
| Database | ![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white) |

## Functional Workflow
1. User enters chat text, uploads audio, or uploads chat screenshot.
2. Backend runs text analysis and/or voice analysis.
3. Fusion module combines modality outputs.
4. Messages and per-day metrics are stored in the database.
5. Relationship stage is updated from historical behavior.
6. Frontend displays current analysis and timeline trends.

## API Overview
### Health and Service
- `GET /`
- `GET /health`

### Text / Voice / Fusion
- `POST /api/v1/text/analyze`
- `POST /api/v1/voice/analyze`
- `POST /api/v1/fusion/analyze`

### Conversation Analytics
- `POST /test-chat`
- `POST /analyze-chat`
- `POST /analyze-chat-image`
- `GET /conversations/{conversation_id}/relationship-summary`

## Project Structure
```text
Emotion_detection-austin_commits/
|-- backend/
|   |-- app/
|   |   |-- api/routes/
|   |   |-- core/
|   |   |-- db/
|   |   |-- schemas/
|   |   |-- services/
|   |   `-- utils/
|   |-- requirements.txt
|   `-- scripts/
|-- publicmain/
|   |-- src/
|   |   |-- components/frontend/
|   |   |-- lib/
|   |   `-- pages/
|   `-- package.json
`-- README.md
```

## Quick Start
### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

### Frontend
```bash
cd publicmain
npm install
npm run dev
```

### Local URLs
- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8005`
- API Docs: `http://localhost:8005/docs`

## Results Summary
- Better performance than text-only analysis for conversational interpretation.
- Improved handling of tone-driven ambiguity.
- Effective social intent classification (friendly, romantic, neutral).
- Useful trend analysis through 7-day relationship metrics.

## Future Improvements
- Fine-tune BERT on larger conversation datasets.
- Better speaker-aware voice modeling.
- Add authentication and per-user ownership mapping.
- Expand long-range timeline analytics and dashboarding.

## References
1. Poria S et al., "Multimodal Sentiment Analysis," IEEE, 2017.
2. Devlin J et al., "BERT: Pre-training of Deep Bidirectional Transformers," NAACL, 2019.
3. Busso C et al., "IEMOCAP Dataset," 2008.
