"""
app/api/voice.py — Voice transcription (Groq Whisper) for low-literacy Indian users
"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File

from app.services.ai_service import ai_service

logger = logging.getLogger("arogyaai.voice")
router = APIRouter(prefix="/api/voice", tags=["Voice"])

ALLOWED_AUDIO_TYPES = {
    "audio/webm", "audio/mp4", "audio/ogg",
    "audio/wav", "audio/mpeg", "audio/x-wav",
    "audio/x-m4a", "audio/m4a",
}

LANGUAGE_OPTIONS = {
    "hi": "Hindi — हिंदी",
    "gu": "Gujarati — ગુજરાતી",
    "en": "English",
    "mr": "Marathi — मराठी",
    "te": "Telugu — తెలుగు",
    "ta": "Tamil — தமிழ்",
    "bn": "Bengali — বাংলা",
    "kn": "Kannada — ಕನ್ನಡ",
}


@router.post("/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    language: str = "hi",
):
    """
    🎤 Voice-to-text for Bharat.
    Supports Hindi, Gujarati, English and 5 other Indian languages.
    Low-literacy users can SPEAK their symptoms — no typing needed.
    """
    if not ai_service.available:
        raise HTTPException(status_code=503, detail="Voice service unavailable. Please configure GROQ_API_KEY.")

    if language not in LANGUAGE_OPTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{language}'. Supported: {list(LANGUAGE_OPTIONS.keys())}"
        )

    content_type = file.content_type or ""
    if content_type not in ALLOWED_AUDIO_TYPES:
        # Try to be lenient with browser-recorded audio
        if not content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {content_type}. Use WebM, MP4, WAV, or MP3."
            )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="Audio too large. Maximum size is 10MB.")
    if len(content) < 100:
        raise HTTPException(status_code=400, detail="Audio too short or empty. Please record a longer message.")

    try:
        transcribed = await ai_service.transcribe_audio(
            content=content,
            filename=file.filename or f"audio.{content_type.split('/')[-1]}",
            language=language,
        )
    except Exception as e:
        logger.error("[Voice] Transcription failed: %s", e)
        raise HTTPException(status_code=503, detail="Transcription failed. Please try again or type your message.")

    if not transcribed or len(transcribed.strip()) < 2:
        raise HTTPException(status_code=422, detail="Could not understand the audio. Please speak clearly or type your message.")

    return {
        "transcription": transcribed,
        "language": language,
        "language_name": LANGUAGE_OPTIONS[language],
        "char_count": len(transcribed),
        "tip": "Tap the send button to get health advice from ArogyaAI.",
    }


@router.get("/languages")
async def get_languages():
    """List supported voice input languages."""
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in LANGUAGE_OPTIONS.items()
        ]
    }
