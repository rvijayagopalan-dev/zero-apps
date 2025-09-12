import logging
import os
from dotenv import load_dotenv

import re
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
import openai
import yt_dlp

# ----------------------------
# Setup logging
# ----------------------------
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG level logs everything
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Please check your .env file or environment variables.")

# ----------------------------
# FastAPI app initialization
# ----------------------------
app = FastAPI(title="NoteSpark API")

# ----------------------------
# CORS middleware
# ----------------------------
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # allowed origins
    allow_credentials=True,
    allow_methods=["*"],         # include OPTIONS automatically
    allow_headers=["*"],         # allow all headers
)

# ----------------------------
# Pydantic model
# ----------------------------
class YTReq(BaseModel):
    url: str

# ----------------------------
# Middleware to log all requests
# ----------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logs every incoming request for debugging."""
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")

    # If there's a body, log it
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()
        if body:
            logger.debug(f"Request Body: {body.decode('utf-8')}")

    response = await call_next(request)
    logger.info(f"Response Status: {response.status_code}")
    return response

# ----------------------------
# Routes
# ----------------------------
@app.post("/api/ingest/youtube")
async def ingest_youtube(body: YTReq):
    logger.info(f"Processing YouTube URL: {body.url}")

    video_id = extract_video_id(body.url)
    transcript = fetch_transcript(video_id)

    if not transcript:
        logger.warning("No transcript available, falling back to ASR via Whisper")
        audio_path = download_audio(body.url)
        transcript = transcribe_audio(audio_path)

    summary = await llm_summarize(transcript)
    timestamps = make_timestamps(transcript)

    logger.info("Successfully processed YouTube video")
    return {"summary": summary, "timestamps": timestamps}


# ----------------------------
# Helper functions
# ----------------------------
def extract_video_id(url: str) -> str:
    """Extracts the video ID from a YouTube URL."""
    logger.debug(f"Extracting video ID from URL: {url}")
    m = re.search(r"v=([\w-]{11})", url) or re.search(r"youtu\.be/([\w-]{11})", url)
    if not m:
        logger.error("Invalid YouTube URL provided")
        raise HTTPException(400, "Invalid YouTube URL")
    video_id = m.group(1)
    logger.debug(f"Extracted video ID: {video_id}")
    return video_id


def fetch_transcript(video_id: str) -> str:
    logger.info(f"Fetching transcript for video ID: {video_id}")
    try:
        # List available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        logger.info("Available transcripts:")
        for transcript in transcript_list:
            logger.info(f"  - {transcript.language} ({'auto-generated' if transcript.is_generated else 'manual'})")

        # Try English first
        try:
            transcript = transcript_list.find_transcript(['en'])
            segments = transcript.fetch()
        except:
            logger.warning("English transcript not found, trying auto-generated or other languages")
            transcript = transcript_list.find_generated_transcript(['en', 'es', 'fr'])
            segments = transcript.fetch()

        text = " ".join([x['text'] for x in segments])
        logger.info(f"Transcript fetched successfully. Length: {len(text)} characters")
        return text

    except Exception as e:
        logger.error(f"Failed to fetch transcript: {str(e)}")
        return ""
    
def download_audio(video_url: str, output_path: str = "audio.mp3"):
    logger.info(f"Downloading audio from {video_url}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    return output_path

def transcribe_audio(file_path: str):
    logger.info("Sending audio to Whisper for transcription")
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text


async def llm_summarize(text: str) -> str:
    """Summarizes text using LLM (OpenAI)."""
    if not text:
        logger.warning("Empty transcript provided to llm_summarize()")
        return "(No transcript available — add ASR fallback)"
    
    logger.info("Sending transcript to LLM for summarization")

    import openai
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = (
        "Summarize as bullet points with clear headers and timestamps if present. "
        "Be concise and faithful; avoid hallucinations.\n\nTEXT:\n" + text[:12000]
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response.choices[0].message.content
        logger.info("LLM summarization successful")
        return summary
    except Exception as e:
        logger.error(f"LLM summarization failed: {str(e)}")
        return "(Error summarizing text)"


def make_timestamps(transcript: str):
    """Stub for generating timestamps."""
    logger.debug("Generating timestamps (stub)")
    return []
