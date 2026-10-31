import requests
from django.conf import settings

from common.exceptions import BusinessRuleError


def is_enabled():
    return bool(settings.GEMINI_API_KEY)


def generate_json(prompt):
    """Ask Gemini for a JSON reply over HTTPS, with no SDK dependency."""
    if not is_enabled():
        raise BusinessRuleError("The assistant is not configured.", "assistant_disabled")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
    response = requests.post(
        url,
        headers={"x-goog-api-key": settings.GEMINI_API_KEY},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]
