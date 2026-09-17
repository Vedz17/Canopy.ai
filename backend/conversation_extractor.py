import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from schemas import ProfileExtraction


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")


client = genai.Client(api_key=GEMINI_API_KEY)


SYSTEM_INSTRUCTION = """
You are the profile extraction component of Canopy AI.

Your job is to extract environmental information explicitly provided
by the user.

IMPORTANT RULES:

1. Extract ONLY information supported by the user's message.
2. Never invent, estimate, infer, or assume a measurement.
3. Missing information must remain missing.
4. If the user explicitly says they do not know something, put the
   corresponding field in unknown_fields.
5. Qualitative observations should remain qualitative.
6. Do not convert qualitative descriptions into fabricated numeric values.
7. If the user says the soil is dry, you may record soil_moisture as "low".
8. If the user says the soil is poor, preserve that as a context note.
   Do NOT convert "poor soil" into a fabricated pH, organic carbon,
   nutrient value, or other measurement.
9. If the user provides a value that updates an earlier value, extract
   the new value.
10. Do not fill unrelated environmental fields.
11. Keep context_notes concise and faithful to what the user said.
12. unknown_fields must contain field names from the environmental
    profile, such as "soil_ph", "organic_carbon", "temperature",
    "rainfall", "crop", or "cropping_pattern".
13. Use recent conversation history to understand contextual replies.
    For example, if the assistant asks about "cropping_pattern" and the
    user replies "I don't know", record "cropping_pattern" in
    unknown_fields.

14. Do not mark a field unknown merely because it is absent from the
    latest user message. Only mark it unknown when the user explicitly
    indicates that they do not know, cannot provide, or have not checked
    that information in the context of the conversation.
"""


def extract_profile_information(
    message: str,
    conversation_history: list[dict[str, str]] | None = None,
) -> ProfileExtraction:
    """
    Extract only explicit environmental information from the user's
    latest message, using recent conversation history when needed
    to understand contextual replies such as "I don't know".
    """

    message = message.strip()

    if not message:
        return ProfileExtraction()

    history_text = ""

    if conversation_history:
        recent_history = conversation_history[-6:]

        history_lines = []

        for turn in recent_history:
            role = turn.get("role", "unknown")
            content = turn.get("content", "").strip()

            if content:
                history_lines.append(
                    f"{role}: {content}"
                )

        history_text = "\n".join(history_lines)

    if history_text:
        contents = f"""
Recent conversation:
{history_text}

Latest user message:
{message}
"""
    else:
        contents = f"""
Latest user message:
{message}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=ProfileExtraction,
        ),
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty profile extraction response."
        )

    return ProfileExtraction.model_validate_json(
        response.text
    )