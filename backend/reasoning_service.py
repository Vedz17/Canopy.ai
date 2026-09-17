import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from schemas import EnvironmentalProfile, Recommendation
from retrieval_service import retrieve_chunks


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Stable Gemini Flash model. Can be overridden with GEMINI_MODEL in .env.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

client = genai.Client(api_key=GEMINI_API_KEY)


SYSTEM_INSTRUCTION = """
You are Canopy AI, an environmental intelligence assistant.

Your job is to reason from the user's environmental profile together with
retrieved scientific evidence and produce a cautious, evidence-backed
recommendation.

Rules:
1. Use the retrieved evidence as the scientific grounding for your claims.
2. Do not invent studies, measurements, percentages, mechanisms, or outcomes.
3. Never turn an inference into a measured fact.
4. If the evidence does not support a claim, do not make that claim.
5. Connect multiple environmental metrics when the evidence supports the
   connection (for example soil, biodiversity, water, land use, or climate).
6. Recommendations must be actionable but appropriately cautious.
7. Do not guarantee outcomes.
8. Quantitative values from the user profile are observations/inputs, not
   predictions.
9. If evidence supports only a direction of effect, describe the direction
   and do not manufacture a percentage.
10. Evidence entries must identify the retrieved source/chunk by document_id
    and chunk id.
11. Keep the answer concise and scientifically defensible.
"""


def build_profile_text(profile: EnvironmentalProfile) -> str:
    return json.dumps(
        profile.model_dump(exclude_none=True),
        indent=2,
    )


def build_evidence_text(chunks: list[dict]) -> str:
    if not chunks:
        return "No scientific evidence was retrieved."

    parts = []

    for chunk in chunks:
        parts.append(
            f"""
[EVIDENCE CHUNK]
chunk_id: {chunk["id"]}
document_id: {chunk["document_id"]}
similarity: {chunk["similarity"]:.4f}
text:
{chunk["text"]}
"""
        )

    return "\n".join(parts)


def generate_recommendation(
    profile: EnvironmentalProfile,
    top_k: int = 5,
) -> tuple[Recommendation, list[dict]]:
    """
    Retrieve scientific evidence and ask Gemini to produce a structured,
    evidence-grounded environmental recommendation.
    """

    profile_text = build_profile_text(profile)

    retrieval_query = f"""
Environmental profile:
{profile_text}

Identify scientifically relevant interventions or management actions for
this environmental context, especially interactions among soil health,
biodiversity, land use, water, climate, and human impacts.
"""

    retrieved_chunks = retrieve_chunks(
        query=retrieval_query,
        top_k=top_k,
    )

    evidence_text = build_evidence_text(retrieved_chunks)

    prompt = f"""
Environmental profile:
{profile_text}

Retrieved scientific evidence:
{evidence_text}

Using ONLY the environmental profile and retrieved evidence above, produce
one primary environmental recommendation.

The "why" field should explain the scientific reasoning and explicitly
connect affected environmental metrics where supported.

The "affected_metrics" field should contain metric names only.

The "time_horizon" field must be one of:
short-term, medium-term, long-term, or uncertain.

The "confidence" field must be one of:
low, medium, or high.

The "evidence" field must contain concise references in this format:
"chunk_id=<id>, document_id=<id>"

If the retrieved evidence is insufficient to justify a specific
recommendation, say that evidence is insufficient rather than guessing.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=Recommendation,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    recommendation = Recommendation.model_validate_json(response.text)

    return recommendation, retrieved_chunks
