import os
import re

from dotenv import load_dotenv
from cohere import ClientV2

from schemas import ProfileExtraction


load_dotenv()


COHERE_API_KEY = os.getenv("COHERE_API_KEY")

COHERE_GENERATION_MODEL = os.getenv(
    "COHERE_GENERATION_MODEL",
    "command-a-03-2025",
)

if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY is not set")


client = ClientV2(api_key=COHERE_API_KEY)


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
15. Set environmental_relevance to true only when the user's message
    contains information, a question, or an observation that is meaningfully
    related to the environmental assessment. This includes soil, climate,
    rainfall, water, land, crops, biodiversity, habitat, pollution,
    deforestation, or environmental management. Greetings, names,
    casual conversation, unrelated topics, and gibberish should normally
    have environmental_relevance set to false.
16. Do not determine environmental_relevance from specific keywords alone.
    Judge the meaning and context of the user's message.
17. A message can be environmentally relevant even when it does not provide
    a structured field. For example, an environmental question or qualitative
    observation may be relevant.
18. Set recommendation_requested to true only when the user is actually
    asking for environmental advice, an intervention, a recommendation,
    what they should do, how to improve the environmental condition, or
    an equivalent request. Judge this from meaning and conversation
    context, not from specific keywords alone.
19. Set recommendation_requested to false when the user is only providing
    environmental information, answering a clarification question, saying
    they do not know something, greeting, or discussing an unrelated topic.
20. A message may be environmentally relevant while recommendation_requested
    is false.

21. Return ONLY valid JSON matching the ProfileExtraction structure.
22. unknown_fields MUST always be an array of strings.
23. context_notes MUST always be an array of strings.
24. If there are no unknown fields, return "unknown_fields": [].
25. If there are no context notes, return "context_notes": [].
"""


def apply_explicit_fact_overrides(
    message: str,
    extraction: ProfileExtraction,
) -> ProfileExtraction:
    """
    Safely recover explicit facts that the LLM may miss.

    These overrides only extract information literally stated by the user.
    They do not infer environmental measurements.
    """

    text = message.strip()
    lower = text.lower()

    # ---------------------------------------------------------
    # Soil organic carbon
    # ---------------------------------------------------------
    soc_match = re.search(
        r"(?:soil\s+organic\s+carbon|organic\s+carbon|soc)"
        r"\s*(?:is|=|:)?\s*(\d+(?:\.\d+)?)\s*%",
        lower,
    )

    if soc_match:
        extraction.organic_carbon = float(soc_match.group(1))

    # ---------------------------------------------------------
    # Soil moisture
    # ---------------------------------------------------------
    if re.search(
        r"\bsoil\b.{0,40}\b(?:dry|very dry)\b",
        lower,
    ):
        extraction.soil_moisture = "low"

    elif re.search(
        r"\bsoil\b.{0,40}\bmoist\b",
        lower,
    ):
        extraction.soil_moisture = "medium"

    # ---------------------------------------------------------
    # Rainfall
    # ---------------------------------------------------------
    if re.search(
        r"\b(?:low|limited|scarce)\s+(?:and\s+irregular\s+)?rainfall\b",
        lower,
    ):
        extraction.rainfall = "low"

    # ---------------------------------------------------------
    # Crop
    # ---------------------------------------------------------
    if re.search(r"\bwheat\b", lower):
        extraction.crop = "wheat"

    # ---------------------------------------------------------
    # Continuous monoculture
    # ---------------------------------------------------------
    if (
        re.search(
            r"\bcontinuous(?:ly)?\s+(?:wheat\s+)?cultivation\b",
            lower,
        )
        or re.search(r"\bcontinuous\s+monoculture\b", lower)
        or re.search(r"\bmonoculture\b", lower)
        or re.search(r"\bgrow\s+wheat\s+continuously\b", lower)
    ):
        extraction.cropping_pattern = "monoculture"

    # ---------------------------------------------------------
    # Explicit biodiversity observation
    # ---------------------------------------------------------
    if re.search(
        r"\bbiodiversity\b.{0,30}\b(?:low|declining|poor)\b",
        lower,
    ):
        note = "Biodiversity is low."

        if note not in extraction.context_notes:
            extraction.context_notes.append(note)

    return extraction


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

    response = client.chat(
        model=COHERE_GENERATION_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTION,
            },
            {
                "role": "user",
                "content": contents,
            },
        ],
        temperature=0.2,
        response_format={
            "type": "json_object",
        },
    )

    response_text = response.message.content[0].text

    if not response_text:
        raise RuntimeError("Cohere returned an empty response.")

    try:
        extraction = ProfileExtraction.model_validate_json(
            response_text
        )
    except Exception as exc:
        raise RuntimeError(
            "Cohere returned invalid ProfileExtraction JSON: "
            f"{response_text}"
        ) from exc

    extraction = apply_explicit_fact_overrides(
        message,
        extraction,
    )

    return extraction