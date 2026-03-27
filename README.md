# MULTIMODAL CONVERSATIONAL EMOTION AND SOCIAL INTENT DETECTION USING NLP AND SPEECH ANALYSIS

## Project Overview
This project presents a multimodal conversational analysis system that combines Natural Language Processing (NLP) and speech analysis to detect emotion and social intent in human communication.

Digital text conversations often lose tone and emotional context, which can lead to misinterpretation. By integrating text understanding with voice signal cues, this system improves conversational interpretation and relationship-aware analysis.

## Authors
- Adithyan C P
- Austin Shajan
- Francis Anto
- George Attokaran Jose

## Guide / Mentor
Ms. Sabira P S  
Assistant Professor, Department of Computer Science and Engineering

## Abstract
Digital communication often lacks emotional clarity when only text is used, as tone significantly affects meaning. This project proposes a multimodal system combining Natural Language Processing (NLP) and speech analysis for improved emotion and intent detection.

Text is processed using models such as BERT or LSTM, while speech features like MFCC, pitch, and energy are extracted and analyzed using CNN or LSTM models. A fusion layer integrates both modalities to produce final classification.

The system improves accuracy, reduces ambiguity, and enhances understanding of conversational context.

## Problem Statement
Text-only communication can hide tone, sarcasm, stress, and emotional intensity. Traditional sentiment analysis pipelines do not fully capture spoken cues and can miss intent-level meaning. This project addresses that gap by combining text and voice understanding in one pipeline.

## Objectives
- Detect emotion and social intent from conversations.
- Combine text and speech analysis in a multimodal framework.
- Classify intent categories such as friendly, romantic, and neutral.
- Improve interpretation quality over text-only approaches.
- Support relationship-aware analysis using day-wise conversation metrics.

## Methodology / Design Approach

### 1. Text Processing
- Input text is normalized and preprocessed.
- NLP pipeline predicts emotion, stress, and social intent.
- Model support includes transformer/recurrent approaches (for example BERT/LSTM), with a working backend implementation for text emotion prediction.

### 2. Speech Processing
- Uploaded audio is validated and processed.
- Acoustic features (for example MFCC, pitch, and energy) are extracted.
- Voice analysis estimates stress level, emotional intensity, and confidence.

### 3. Multimodal Fusion
- Text prediction and voice prediction are combined in a fusion service.
- The fusion output provides final emotion, social intent, and combined confidence.

### 4. Relationship Analytics Layer
- Chat messages are persisted in a database.
- Day-level relationship metrics are computed (positive, negative, affection, message count).
- Relationship stage is updated from accumulated historical metrics.

## Key Functionalities Implemented

### Backend (FastAPI)
- Health endpoint for service readiness.
- Text analysis endpoint.
- Voice analysis endpoint with file type and size validation.
- Fusion endpoint for multimodal inference.
- Chat ingestion endpoint for conversation-level persistence.
- OCR-based chat image analysis endpoint.
- Historical relationship summary endpoint (last 7 days).

### Frontend (React + Vite + Tailwind)
- Modern landing page and user interaction flow.
- Add-person workflow for conversation analysis profiles.
- Modal-based chat input parsing (`Sender: message` format).
- Live relationship analysis view:
	- Conversation ID
	- Relationship stage
	- Emotion counts
	- Last 7-day timeline metrics
- API fallback handling for multiple local backend ports.

### Persistence and History
- SQLAlchemy ORM with SQLite storage (`app.db`).
- Entities include:
	- users
	- conversations
	- messages
	- daily_relationship_metrics
	- relationship_stages
- Historical metrics can be retrieved and displayed across days for the same conversation.

## System Architecture (High Level)
1. User submits chat text, audio, or chat screenshot.
2. Backend preprocesses input and runs text/voice analysis.
3. Fusion layer combines modality outputs.
4. Message-level and day-level metrics are stored in the database.
5. Relationship stage is updated from metric history.
6. Frontend renders current analysis and timeline summary.

## API Endpoints

### Core
- `GET /health` - service health status.
- `GET /` - API root metadata.

### Text / Voice / Fusion
- `POST /api/v1/text/analyze`
- `POST /api/v1/voice/analyze`
- `POST /api/v1/fusion/analyze`

### Conversation and History
- `POST /test-chat` - analyze and persist structured chat messages.
- `POST /analyze-chat` - alias flow for chat analysis.
- `POST /analyze-chat-image` - OCR + chat analysis pipeline.
- `GET /conversations/{conversation_id}/relationship-summary` - last 7 days metrics and current stage.

## Tech Stack

### Frontend
- React 18
- TypeScript
- Vite
- Tailwind CSS
- Radix UI components

### Backend
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn

### ML / Signal Processing
- scikit-learn
- transformers
- PyTorch
- librosa
- OpenCV
- pytesseract

### Database
- SQLite (development default)

## Project Structure
```
Emotion_detection-austin_commits/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── requirements.txt
│   └── scripts/
├── publicmain/
│   ├── src/
│   │   ├── components/frontend/
│   │   ├── lib/
│   │   └── pages/
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Local Setup and Run Instructions

### 1. Clone and open project
```bash
git clone <your-repo-url>
cd Emotion_detection-austin_commits
```

### 2. Run backend
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

Backend URL: `http://localhost:8005`  
API docs: `http://localhost:8005/docs`

### 3. Run frontend
```bash
cd publicmain
npm install
npm run dev
```

Frontend URL (default): `http://localhost:8080`

## Usage Workflow
1. Open the frontend.
2. Add a person profile in the avatar grid.
3. Enter conversation lines using `Sender: message` format.
4. Run analysis from the modal.
5. View:
	 - detected emotion counts
	 - relationship stage
	 - current day relationship metrics
	 - timeline of last 7 days
6. Optionally analyze chat screenshots or upload voice clips through backend endpoints.

## Results and Discussion
- Improved accuracy compared to text-only sentiment approaches by introducing speech cues.
- Better handling of tone variations and conversational ambiguity.
- Effective social intent categorization in practical conversation scenarios.
- Day-wise metrics provide interpretable, longitudinal relationship insights.

## Achievements
- Built a working multimodal emotion and intent detection prototype.
- Integrated NLP and voice pipelines with fusion logic.
- Implemented persistence for conversation analytics and timeline history.
- Added OCR-based chat screenshot analysis support.
- Developed an interactive web interface for end-to-end testing and usage.

## Conclusion
This project demonstrates that multimodal analysis improves emotion and social intent detection over text-only systems. By combining NLP and speech features, the system reduces misinterpretation and improves understanding of conversational context.

The implementation also introduces practical history-aware analytics through daily relationship metrics and stage tracking.

## Future Scope
- Improve model performance with larger curated datasets.
- Add speaker diarization and stronger voice-emotion modeling.
- Introduce authentication and per-user conversation ownership.
- Extend timeline analytics beyond 7-day summaries.
- Deploy as a production-ready cloud service with monitoring.

## References
1. Poria S et al., "Multimodal Sentiment Analysis," IEEE, 2017.
2. Devlin J et al., "BERT: Pre-training of Transformers," NAACL, 2019.
3. Busso C et al., "IEMOCAP Dataset," 2008.
