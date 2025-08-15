from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.files.storage import default_storage
import base64
import requests
from .models import ChatMessageAi
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny
# from rest_framework.authentication import SessionAuthentication, BasicAuthentication


HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_API_KEY = "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"  # Hugging Face token yaha daal

# CHATGPT_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
# CHATGPT_API_URL = "https://api.openai.com/v1/chat/completions"  # Replace with free/proxy API
# ELEVENLABS_API_KEY = "sk_df7d68f7bee4ffe037ee48d885b33f08274ec39a34531abd"
# ELEVENLABS_VOICE_ID = "jqcCZkN6Knx8BJ5TBdYR"

ELEVENLABS_API_KEY = "sk_36b9ab10cd637d6ba2ce3ca1e51e2e5cee65e0a8968eb4ef"
ELEVENLABS_VOICE_ID = "jqcCZkN6Knx8BJ5TBdYR"


@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])  # disables any authentication classes
def transcribe_and_reply_2(request):

    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"
    GEMINI_API_KEY = "AIzaSyDwmmZ4jSBG4h_xh5vY20tYB3YfpYOPnOo"  # from Google AI Studio

    system_prompt = """You are Learn-Z, a software engineer who generates optimised code snippets.
    Your name is formed by combining Gen-Z and learning.
    If asked about your name, explain it in a fun, engaging way. you are supposed to answer freindly like a family member of every question."""

    message = request.data.get("text", "")
    # audio_file = request.FILES['audio']

    # # Save temporarily
    # with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
    #     for chunk in audio_file.chunks():
    #         tmp.write(chunk)
    #     tmp_path = tmp.name

    # # Convert to wav
    # wav_path = tmp_path.replace(".webm", ".wav")
    # subprocess.run(["ffmpeg", "-i", tmp_path, wav_path])

    # # Step 1: Transcribe audio → text
    # result = model.transcribe(wav_path)
    # user_text = result["text"]

    # print(f"User text: {user_text}")

    # Save user message in DB
    ChatMessageAi.objects.create(role="user", content=message)

    # Fetch last 5 messages from DB (oldest first)
    previous_messages = ChatMessageAi.objects.order_by("-created_at")
    previous_messages = list(reversed(previous_messages))

    # Build Gemini history
    gemini_contents = []

    # Inject system prompt as the first user message
    gemini_contents.append({"role": "user", "parts": [{"text": f"{system_prompt}"}]})

    # Add conversation history
    for msg in previous_messages:
        gemini_contents.append(
            {
                "role": "user" if msg.role == "user" else "model",
                "parts": [{"text": msg.content}],
            }
        )
        # print(msg)

    # Add current message
    gemini_contents.append({"role": "user", "parts": [{"text": message}]})

    # Call Gemini
    gemini_payload = {"contents": gemini_contents}

    gemini_res = requests.post(
        f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json=gemini_payload,
    )

    if gemini_res.status_code != 200:
        return Response(
            {"error": "Gemini API failed", "details": gemini_res.text}, status=500
        )

    gemini_data = gemini_res.json()
    if gemini_data:
        print(gemini_data)
    ai_reply = gemini_data["candidates"][0]["content"]["parts"][0]["text"]

    # Save assistant reply
    ChatMessageAi.objects.create(role="assistant", content=ai_reply)

    # ElevenLabs TTS
    tts_payload = {
        "text": f"<speak><prosody rate='85%' pitch='0%' volume='100%'>{ai_reply}</prosody></speak>",
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.8},
    }
    tts_res = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
        headers={"Content-Type": "application/json", "xi-api-key": ELEVENLABS_API_KEY},
        json=tts_payload,
    )

    audio_base64 = (
        base64.b64encode(tts_res.content).decode("utf-8")
        if tts_res.status_code == 200
        else None
    )

    return Response(
        {"ai_text": ai_reply, "ai_audio": audio_base64, "ai_reasoning": None}
    )
