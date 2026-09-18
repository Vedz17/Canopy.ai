import json
import os
import re

from dotenv import load_dotenv
from cohere import ClientV2

from schemas import EnvironmentalProfile, Recommendation
from retrieval_service import retrieve_chunks


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
You are Canopy AI, a personalized environmental intelligence assistant.

Your job is to reason about the user's specific environmental situation
using BOTH:

1. The user's environmental profile.
2. Retrieved scientific evidence from the Canopy knowledge system.

The retrieved evidence is supporting scientific knowledge. It is NOT the
recommendation itself.

Your response must be personalized to the user's actual profile rather
than sounding like a generic summary of the retrieved documents.

IMPORTANT RULES:

1. Start your reasoning from the user's environmental profile.

2. Identify the most relevant conditions, observations, goals, and known
   environmental metrics in the user's profile.

3. The recommendation must be appropriate for THIS specific environmental
   profile. Do not produce a generic recommendation that could apply to
   almost any environmental situation.

4. Explicitly connect the recommendation to the user's known conditions.
   Where possible, the "why" field should connect at least two relevant
   environmental factors from the profile.

5. Consider interactions among environmental metrics when supported by
   the evidence. Examples include:

   - soil health ↔ biodiversity
   - soil moisture ↔ vegetation or species survival
   - land use ↔ habitat diversity
   - crop diversification ↔ soil and biodiversity
   - climate ↔ soil moisture
   - human impact ↔ ecosystem condition

6. Use retrieved scientific evidence to explain WHY the recommendation is
   scientifically relevant to the user's situation.

7. Do NOT simply summarize, copy, or paraphrase the retrieved evidence.
   Transform the evidence into reasoning about the user's specific profile.

8. Do not invent studies, measurements, percentages, mechanisms, or outcomes.

9. Never turn an inference into a measured fact.

10. If the evidence does not support a claim, do not make that claim.

11. Every scientific mechanism or environmental effect mentioned in the
    "why" field must be directly supported by at least one retrieved
    evidence chunk.

12. Do not combine separate retrieved facts into a stronger causal claim
    unless the retrieved evidence itself supports that connection.

13. Do not mention an environmental effect as being improved, reduced,
    enhanced, increased, decreased, or otherwise affected unless the
    retrieved evidence supports that effect.

14. Evidence percentages may be reported ONLY when they are explicitly
    present in the retrieved evidence.

15. Any percentage must be described as a reported study or meta-analysis
    result, NOT as a guaranteed user-specific outcome.

16. If one retrieved chunk supports biodiversity and another retrieved
    chunk supports soil-water infiltration, you may use both supported
    effects to explain why the recommendation is relevant to the user's
    profile.

17. However, do NOT add an unsupported effect such as pollution reduction
    merely because it is generally plausible.

18. The "affected_metrics" array must contain ONLY metrics for which the
    retrieved evidence supports an effect relevant to the recommendation.

19. STRATEGY-SPECIFIC EVIDENCE RULE:

    When recommending a specific intervention such as:

    - agroforestry
    - crop rotation
    - cover crops
    - intercropping
    - variety mixtures

    you MUST distinguish evidence about that specific strategy from
    evidence about crop diversification overall.

20. NEVER attribute an overall crop-diversification effect size to a
    specific strategy unless the retrieved evidence explicitly attributes
    that exact effect size to that strategy.

21. For example:

    If a source says:

    "crop diversification overall → +24% biodiversity"

    and later says:

    "agroforestry is particularly effective..."

    you MUST NOT write:

    "agroforestry increases biodiversity by 24%."

    The +24% result belongs to the overall crop-diversification synthesis,
    not automatically to agroforestry.

22. If a source reports a strategy-specific effect such as:

    "Agroforestry → +45% soil-water infiltration"

    that strategy-specific percentage MAY be reported, provided the wording
    clearly describes it as a reported study/meta-analysis result.

23. If you are uncertain whether a percentage applies to the recommended
    strategy, DO NOT USE THE PERCENTAGE.

24. When strategy-specific evidence exists, prefer it over an overall
    diversification statistic.

25. A qualitative effect is preferable to an incorrectly attributed
    quantitative effect.

26. Never assume that a missing value is poor, low, high, abnormal, or
    otherwise problematic.

27. Unknown measurements must remain unknown.

28. User-provided quantitative values are observations or inputs, not
    predictions.

29. If evidence supports only a direction of effect, describe the direction
    and do not manufacture a percentage.

30. Recommendations must be actionable but appropriately cautious.

31. Do not guarantee outcomes.

32. Prefer a practical intervention that addresses the strongest supported
    relationship between the user's conditions and the retrieved evidence.

33. If multiple interventions are possible, choose ONE primary recommendation
    that best fits the available evidence and user context.

34. The recommendation should explain why that intervention fits the user's
    situation, not merely why the intervention is generally useful.

35. If the available profile is incomplete, work with what is known and
    explicitly acknowledge important unknowns when they affect the
    recommendation.

36. Do not recommend actions that depend on measurements the user has not
    provided unless the recommendation is specifically to obtain that
    measurement.

37. Evidence entries must identify the retrieved source/chunk by
    document_id and chunk id.

38. Keep the answer concise, natural, personalized, and scientifically
    defensible.

39. Return ONLY valid JSON matching the Recommendation structure.

40. affected_metrics MUST always be an array of strings.

41. evidence MUST always be an array of strings.

42. Each evidence item must use the format:

    "chunk_id=<id>, document_id=<id>"

43. Only cite evidence chunks that actually support the recommendation.

44. If there is no supporting evidence, return evidence as [].

45. IMPORTANT FINAL SCIENTIFIC CHECK:

    Before returning the JSON, inspect every scientific effect mentioned
    in the "why" field.

    For EACH scientific effect:

    1. Identify the exact retrieved evidence chunk that supports it.

    2. Confirm that the retrieved chunk discusses the SAME intervention
       that is being recommended.

    3. Confirm that the wording does not strengthen, change, or exaggerate
       the mechanism reported by the evidence.

       For example:

       "improves soil-water infiltration"

       must NOT become:

       "improves soil moisture retention"

       unless the evidence explicitly supports soil moisture retention.

    4. Confirm that an effect reported for "crop diversification overall"
       has NOT been attributed to a specific strategy such as agroforestry,
       crop rotation, cover crops, intercropping, or variety mixtures.

    5. If a percentage belongs to crop diversification overall rather than
       the specific recommended strategy, DO NOT use that percentage.

    6. If the evidence supports only a qualitative effect, keep the claim
       qualitative.

    7. If any scientific claim fails these checks, REMOVE the unsupported
       claim instead of guessing or replacing it with a stronger claim.

46. IMPORTANT UNKNOWN-VALUE CHECK:

    Do not describe an unknown metric as though it were deficient.

    For example, if soil pH is unknown, do not say that the soil has poor
    pH or that the recommendation is correcting poor pH.

47. IMPORTANT EVIDENCE-SCOPE CHECK:

    Every quantitative claim must satisfy ALL of these conditions:

    - The exact number appears in the retrieved evidence.
    - The evidence attributes the number to the same intervention being
      recommended.
    - The wording clearly identifies it as a reported study/meta-analysis
      result rather than a prediction for the user's site.

48. If there is any uncertainty about whether an effect or percentage
    applies specifically to the recommended intervention, OMIT the
    quantitative claim and use only the directly supported qualitative
    evidence.

49. SITE-SUITABILITY / EFFECTIVENESS-MODIFICATION RULE:
    Do NOT claim that the user's specific conditions make the recommended
    strategy "particularly effective," "especially effective," "ideal,"
    "well suited," or otherwise amplify, strengthen, or optimize its
    effectiveness — UNLESS the retrieved evidence explicitly studies or
    reports an interaction between that specific condition and the
    strategy's effectiveness.

    You MAY connect the recommendation to the user's profile by describing
    RELEVANCE or APPLICABILITY (for example, "because you grow crop X under
    continuous monoculture, diversification is applicable to your land
    use"). This is a statement about fit, not about amplified effect.

    Do NOT convert a general study finding into a claim that the user's
    reported conditions strengthen or improve that finding's magnitude,
    unless the evidence itself makes that comparison.

    Example: do NOT write:
    "Given your moist soil and moderate rainfall, agroforestry can be
    particularly effective."
    Instead state the general evidence finding as a study/meta-analysis
    result, and separately state that the intervention is relevant given
    the user's reported land use/crop, without implying that its magnitude
    is amplified by those conditions.

50. Every mechanism or effect statement in the "why" field must use
    explicit attribution language (for example, "Retrieved evidence
    indicates..." or "A meta-analysis of [topic] reports...") rather than
    being stated as a plain, unsourced fact about the user's site.
"""


def build_profile_text(
    profile: EnvironmentalProfile,
) -> str:
    """
    Convert the environmental profile into readable JSON for the
    retrieval and reasoning prompts.
    """

    return json.dumps(
        profile.model_dump(exclude_none=True),
        indent=2,
    )


def build_evidence_text(
    chunks: list[dict],
) -> str:
    """
    Convert retrieved chunks into clearly separated evidence blocks.
    """

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


def _extract_percentages(
    text_value: str,
) -> list[str]:
    """
    Extract percentage expressions from generated reasoning.

    Handles examples such as:
        45%
        +45%
        24 percent
        +24 percent
    """

    return re.findall(
        r"[+-]?\d+(?:\.\d+)?\s*(?:%|percent)",
        text_value,
        flags=re.IGNORECASE,
    )


def _percentage_has_strategy_specific_support(
    percentage: str,
    recommendation_text: str,
    evidence_chunks: list[dict],
) -> bool:
    """
    Check whether a quantitative claim can reasonably be attributed
    to the recommended intervention.

    The important distinction is between:

        crop diversification overall → +24%

    and:

        agroforestry → +45%

    A percentage must occur near explicit strategy language in the
    same evidence chunk before it is accepted as strategy-specific.
    """

    recommendation_lower = recommendation_text.lower()

    strategies = (
        "agroforestry",
        "crop rotation",
        "cover crops",
        "intercropping",
        "variety mixtures",
    )

    strategy = None

    for candidate in strategies:
        if candidate in recommendation_lower:
            strategy = candidate
            break

    if strategy is None:
        return True

    percentage_number_match = re.search(
        r"[+-]?\d+(?:\.\d+)?",
        percentage,
    )

    if not percentage_number_match:
        return False

    percentage_number = percentage_number_match.group(0)

    for chunk in evidence_chunks:
        chunk_text = chunk.get("text", "")

        if not chunk_text:
            continue

        matches = list(
            re.finditer(
                re.escape(percentage_number),
                chunk_text,
            )
        )

        if not matches:
            continue

        chunk_lower = chunk_text.lower()

        for match in matches:
            start = max(
                0,
                match.start() - 250,
            )

            end = min(
                len(chunk_lower),
                match.end() + 250,
            )

            local_context = chunk_lower[start:end]

            if strategy in local_context:
                return True

    return False


def _find_invalid_quantitative_claims(
    recommendation: Recommendation,
    evidence_chunks: list[dict],
) -> list[str]:
    """
    Identify generated percentages that cannot be verified as
    strategy-specific evidence.
    """

    generated_text = (
        f"{recommendation.recommendation} "
        f"{recommendation.why}"
    )

    percentages = _extract_percentages(
        generated_text
    )

    invalid = []

    for percentage in percentages:
        if not _percentage_has_strategy_specific_support(
            percentage=percentage,
            recommendation_text=recommendation.recommendation,
            evidence_chunks=evidence_chunks,
        ):
            invalid.append(percentage)

    return invalid


def _build_reasoning_prompt(
    profile_text: str,
    evidence_text: str,
) -> str:
    """
    Build the primary reasoning prompt.
    """

    return f"""
USER'S ENVIRONMENTAL PROFILE:

{profile_text}


RETRIEVED SCIENTIFIC EVIDENCE:

{evidence_text}


TASK:

Reason about the user's specific environmental situation and produce ONE
primary personalized environmental recommendation.

Do NOT simply summarize the retrieved evidence.

First determine what is actually happening in the user's profile based only
on the provided information.

Then determine which intervention is most directly relevant to those known
conditions.

Then use the retrieved scientific evidence to support the reasoning behind
that intervention.


PERSONALIZATION REQUIREMENTS:

- Refer directly to the user's relevant environmental conditions.
- Use the known crop, land-use pattern, soil condition, climate condition,
  biodiversity condition, or human-impact condition when relevant.
- Connect multiple known metrics when scientifically supported.
- Explain why the recommendation fits THIS profile.
- Do not treat unknown measurements as problems.
- Do not invent missing pH, organic carbon, temperature, rainfall, or
  biodiversity measurements.
- Do not give a generic textbook explanation.


EVIDENCE-GROUNDING REQUIREMENTS:

- Every scientific mechanism or environmental effect in "why" must be
  supported by at least one retrieved evidence chunk.
- Do not infer an unsupported environmental benefit from general knowledge.
- Do not claim pollution reduction, carbon improvement, biodiversity
  improvement, water retention, yield improvement, or any other effect
  unless the retrieved evidence supports that specific effect.
- If multiple evidence chunks support different effects, keep those effects
  distinct unless the evidence explicitly establishes their relationship.
- If reporting a percentage, reproduce it only as a reported study/meta-analysis
  result and do not present it as a prediction for the user's site.
- The affected_metrics list must contain ONLY metrics with evidence-backed
  effects.
- Only cite evidence chunks that actually support the recommendation or the
  specific effects stated in "why".
- When citing a quantitative effect, prefer the most specific retrieved
  evidence that matches the recommended intervention.
- Distinguish overall crop-diversification effects from strategy-specific
  effects such as agroforestry, crop rotation, cover crops, intercropping,
  or variety mixtures.

- Use only effects that are explicitly stated in the retrieved evidence.

- Do not replace an evidence term with a stronger or different mechanism.

  For example:

  "improves soil-water infiltration"

  must NOT become:

  "improves soil moisture retention"

  unless the evidence explicitly says that.

- Do not infer climatic classifications such as arid, semi-arid, humid,
  tropical, or temperate from a qualitative value such as "low rainfall"
  unless that classification is explicitly supported by the profile or
  retrieved evidence.

- When evidence discusses "crop diversification overall", do not attribute
  its effect to agroforestry, crop rotation, cover crops, intercropping,
  or another individual strategy unless the evidence explicitly does so.

- When a qualitative effect is supported for agroforestry, it may be stated
  qualitatively. Do not attach a quantitative value from a broader
  diversification category to that qualitative statement.

- Do not describe an environmental metric as "unknown" and then imply that
  the intervention will improve it. An unknown metric is simply unknown.


CRITICAL QUANTITATIVE RULE:

If the recommendation is agroforestry, do NOT use an overall
crop-diversification percentage as an agroforestry percentage.

For example:

    WRONG:
    "Agroforestry increases biodiversity by 24%."

when the evidence actually says:

    "crop diversification overall → +24% biodiversity."

Instead write a qualitative statement unless the evidence contains a
strategy-specific agroforestry statistic.

If the evidence explicitly states:

    "Agroforestry → +45% soil-water infiltration"

you may report that result, but phrase it as a reported meta-analysis/study
result and not as a guaranteed result for the user's site.


FINAL SCIENTIFIC VALIDATION:

Before returning the JSON, inspect every scientific effect mentioned
in "why".

For each effect:

1. Identify the exact retrieved chunk supporting it.
2. Confirm that the chunk discusses the same intervention.
3. Confirm that the wording does not strengthen or change the mechanism.
4. Confirm that an overall crop-diversification result has not been
   attributed to a specific strategy.
5. Confirm that any percentage is explicitly attributable to the same
   intervention.
6. Confirm that no sentence claims the user's specific conditions make
   the strategy "particularly effective," "ideal," "well suited," or
   otherwise more effective than the evidence reports, unless the
   evidence explicitly studies that interaction. Rewrite such claims
   as relevance/applicability or remove them.
7. If any check fails, REMOVE the claim instead of guessing.


OUTPUT REQUIREMENTS:

The "recommendation" field should contain ONE clear, practical action or
management strategy tailored to the user's situation.

The "why" field should explain:

1. What in the user's profile makes this recommendation relevant.
2. Which specific retrieved evidence supports the recommendation.
3. The scientific effect or relationship actually reported by that evidence.
4. Which environmental conditions may be affected, using ONLY
   evidence-supported effects.

Do not add an environmental effect merely because it is generally plausible.

The "affected_metrics" field should contain metric names only, and every
listed metric must have a directly supported effect in the retrieved evidence.

The "time_horizon" field must be one of:

- short-term
- medium-term
- long-term
- uncertain

The "confidence" field must be one of:

- low
- medium
- high

The "evidence" field MUST be an array of strings.

Each evidence item must use exactly this format:

"chunk_id=<id>, document_id=<id>"

Only reference evidence chunks that actually support the recommendation.

If the retrieved evidence is insufficient to justify a specific
recommendation, say that evidence is insufficient rather than guessing.

Return ONLY valid JSON.
"""


def _generate_recommendation_once(
    prompt: str,
) -> Recommendation:
    """
    Ask Cohere to generate one recommendation.
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
                "content": prompt,
            },
        ],
        temperature=0.2,
        response_format={
            "type": "json_object",
        },
    )

    response_text = response.message.content[0].text

    if not response_text:
        raise RuntimeError(
            "Cohere returned an empty response."
        )

    try:
        return Recommendation.model_validate_json(
            response_text
        )
    except Exception as exc:
        raise RuntimeError(
            "Cohere returned invalid Recommendation JSON: "
            f"{response_text}"
        ) from exc


def _build_correction_prompt(
    original_prompt: str,
    recommendation: Recommendation,
    invalid_percentages: list[str],
) -> str:
    """
    Build a focused correction prompt when the first generation
    contains a quantitative claim that cannot be verified as
    strategy-specific.
    """

    invalid_text = ", ".join(
        invalid_percentages
    )

    return f"""
{original_prompt}


IMPORTANT CORRECTION REQUIRED:

The previous generated answer contained these quantitative claims:

{invalid_text}

Those quantitative claims could not be verified as being specific to the
recommended intervention from the retrieved evidence.

Previous answer:

{recommendation.model_dump_json(indent=2)}

Regenerate the answer.

STRICT CORRECTION RULE:

- Remove any quantitative claim whose evidence scope is ambiguous.
- Do NOT convert an overall crop-diversification statistic into a
  strategy-specific statistic.
- If a percentage is not explicitly attributable to the recommended
  intervention, replace it with a qualitative evidence-backed statement.
- Do not replace an evidence term with a stronger or different mechanism.
- Do not turn "improves soil-water infiltration" into
  "improves soil moisture retention" unless the evidence explicitly
  supports soil moisture retention.
- Do not infer climatic classifications from qualitative rainfall values.
- Do not describe unknown metrics as deficient.
- Keep only effects directly supported by the retrieved evidence.
- Keep the recommendation personalized to the user's actual profile.
- Keep the evidence array limited to chunks that genuinely support the
  recommendation.

Return ONLY valid JSON matching the Recommendation structure.
"""


def generate_recommendation(
    profile: EnvironmentalProfile,
    top_k: int = 5,
) -> tuple[Recommendation, list[dict]]:
    """
    Retrieve scientific evidence and ask Cohere to produce a personalized,
    evidence-grounded environmental recommendation.

    A deterministic quantitative-evidence validation layer is applied after
    generation. If Cohere attributes a percentage to a specific intervention
    without sufficiently specific evidence, the answer is regenerated with
    explicit correction instructions.
    """

    profile_text = build_profile_text(
        profile
    )

    retrieval_query = f"""
Environmental assessment for a specific user:

{profile_text}

Retrieve scientific evidence that directly supports management decisions
for THIS environmental profile.

Prioritize evidence that connects the user's actual conditions, especially:

- crop type and cropping pattern
- monoculture versus crop diversification or rotation
- soil moisture and soil health
- soil organic carbon and soil structure
- agricultural biodiversity and habitat diversity
- interactions between crop diversification, soil health, and biodiversity
- climate or rainfall conditions ONLY when they are explicitly present
  in the user profile

The retrieved evidence should help answer:

1. What environmental problem or interaction is most relevant here?
2. Which management intervention is scientifically supported for these
   specific conditions?
3. What environmental metrics could be affected?

Do not prioritize unrelated environmental topics simply because they appear
in the general environmental profile.

The evidence will be used to support a personalized recommendation, not
to generate a generic summary of environmental science.
"""

    retrieved_chunks = retrieve_chunks(
        query=retrieval_query,
        top_k=top_k,
    )

    evidence_text = build_evidence_text(
        retrieved_chunks
    )

    prompt = _build_reasoning_prompt(
        profile_text=profile_text,
        evidence_text=evidence_text,
    )

    recommendation = _generate_recommendation_once(
        prompt
    )

    # ---------------------------------------------------------
    # Deterministic quantitative-evidence guard
    # ---------------------------------------------------------

    invalid_percentages = _find_invalid_quantitative_claims(
        recommendation=recommendation,
        evidence_chunks=retrieved_chunks,
    )

    if invalid_percentages:
        correction_prompt = _build_correction_prompt(
            original_prompt=prompt,
            recommendation=recommendation,
            invalid_percentages=invalid_percentages,
        )

        corrected_recommendation = (
            _generate_recommendation_once(
                correction_prompt
            )
        )

        # Validate the corrected response one more time.
        corrected_invalid_percentages = (
            _find_invalid_quantitative_claims(
                recommendation=corrected_recommendation,
                evidence_chunks=retrieved_chunks,
            )
        )

        if not corrected_invalid_percentages:
            recommendation = corrected_recommendation

    return recommendation, retrieved_chunks