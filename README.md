# EchoFrame: AI-Powered Video Learning Assistant

> Initially developed during Meta's [LlamaCon Hackathon 2025](https://www.linkedin.com/posts/meta-for-developers_llamaconhackathon25-activity-7325260127798788096-TqPZ?utm_source=share&utm_medium=member_desktop&rcm=ACoAABdIhZwBKgBEN52VAp7xTSJE6_nIFC-OCWU) as an innovative solution for video-based learning and content analysis. The project has since evolved with additional features and improvements to enhance user experience and functionality.

EchoFrame is an innovative application that revolutionizes how we learn from video content. By leveraging Meta's Llama 4 models and advanced AI technologies, EchoFrame helps users efficiently extract knowledge from multiple videos without the need to watch them entirely.

## Features

### 1. Smart Video Analysis
- Multi-video processing and summarization
- Visual action recognition using Llama 4's multimodal capabilities
- Extraction of key steps, visual cues and timestamps from instructional videos

### 2. Interactive Avatar Assistant
- Real-time conversations about video content using Tavus integration
- Ability to ask specific questions about any part of the video
- Quick navigation to relevant video timestamps

### 3. Multilingual Support
- Support for multiple languages:
  - English (en)
  - Spanish (es)
  - German (de)
  - Hindi (hi)
- Translation of both conversations and podcasts

### 4. Podcast Generation
- Creation of concise audio summaries
- Multi-video content synthesis
- Language customization options

## Architecture

![EchoFrame Architecture](images/EchoFrame%20Flow%20Diagram.jpg)

The application leverages several cutting-edge technologies:
- **Llama 4 Maverick**: Core model for summarization and conversation
- **Groq**: Fast inference engine
- **Tavus**: Avatar-based interaction
- **Meta's Synthetic Data Toolkit**: Transcriptions and Visual cue extraction from videos
- **FastAPI**: Backend API framework
- **React**: Frontend framework

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/LlamaConHackathon-EchoFrame.git
cd LlamaConHackathon-EchoFrame
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

4. Configure environment variables:
Create a `.env` file in the backend directory with:
```
GROQ_API_KEY=your_groq_api_key
TAVUS_API_KEY=your_tavus_api_key
GROQ_MODEL=model_name
LLAMA_API_KEY=your_llama_api_key
TAVUS_PERSONA_ID=created_persona_id
TAVUS_REPLICA_ID=replica_id
```

## Running the Application

1. Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
```

3. Access the application:
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs

## Use Cases

1. **DIY Home Repairs**: Quickly find specific repair steps without watching multiple lengthy videos
2. **Technical Learning**: Extract key concepts from multiple educational videos
3. **Cooking Instructions**: Synthesize cooking methods from various recipe videos
4. **Assembly Instructions**: Get clear, step-by-step guidance from product assembly videos

## Technical Implementation

EchoFrame leverages Llama 4's advanced capabilities:
- **Long Context Window**: Processes multiple videos simultaneously (up to 1M tokens with Maverick)
- **Multimodality**: Extracts information from both video frames and audio
- **Multilingual Support**: Handles content in 200+ languages

## License

EchoFrame is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

### Attribution Requirements
When using EchoFrame in your project, please provide attribution as specified in the [NOTICE](NOTICE) file.


