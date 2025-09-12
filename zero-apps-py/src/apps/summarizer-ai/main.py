# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
import os

app = FastAPI(title="NoteSpark API")

# --- Enable CORS ---
origins = [
    "http://localhost:5173",  # Vite/React frontend
    "http://127.0.0.1:5173",  # Alternative access
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # only allow these origins
    allow_credentials=True,
    allow_methods=["*"],            # allow all HTTP methods
    allow_headers=["*"],            # allow all headers
)


class YTReq(BaseModel):
    url: str

@app.post('/api/ingest/youtube')
async def ingest_youtube(body: YTReq):
    video_id = extract_video_id(body.url)
    transcript = fetch_transcript(video_id)
    # TODO: if no captions, download audio with yt_dlp and run WhisperX/Whisper
    summary = await llm_summarize(transcript)
    return {"summary": summary, "timestamps": make_timestamps(transcript)}

# --- helpers ---

def extract_video_id(url: str) -> str:
    import re
    m = re.search(r"v=([\w-]{11})", url) or re.search(r"youtu\.be/([\w-]{11})", url)
    if not m:
        raise HTTPException(400, 'Invalid YouTube URL')
    return m.group(1)

def fetch_transcript(video_id: str) -> str:
    try:
        s = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([x['text'] for x in s])
    except Exception:
        return "" # caller decides to fall back to ASR

async def llm_summarize(text: str) -> str:
    if not text:
        return "(No transcript available — add ASR fallback)"
    import openai
    async def llm_summarize(text: str) -> str:
        if not text:
            return "(No transcript available — add ASR fallback)"
    
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    prompt = (
        "Summarize as bullet points with clear headers and timestamps if present. "
        "Be concise and faithful; avoid hallucinations.\n\nTEXT:\n" + text[:12000]
    )

    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    # New SDK response format
    return r.choices[0].message.content


def make_timestamps(transcript: str):
    # stub: in production, use original segments with start times
    return []