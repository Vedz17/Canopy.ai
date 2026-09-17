from typing import Any
from conversation_extractor import extract_profile_information

from conversation_service import (
    ConversationState,
    add_assistant_message,
    add_context_note,
    add_user_message,
    mark_user_declined,
    update_known_facts,
)
from schemas import ProfileExtraction


# Fields are intentionally prioritized by context.
# We ask only one question at a time.
FIELD_QUESTIONS = {
    "crop": (
        "What crop are you growing? If you’re not sure, that’s completely okay."
    ),
    "cropping_pattern": (
        "Is it mostly one crop every season, or do you rotate or mix different crops?"
    ),
    "soil_moisture": (
        "How does the soil usually feel — dry, moist, or somewhere in between?"
    ),
    "soil_ph": (
        "Do you know the soil pH from a soil test? If not, we can continue without it."
    ),
    "organic_carbon": (
        "Do you have a soil organic carbon value from a soil test? If not, we can continue without it."
    ),
    "rainfall": (
        "Would you describe the area's rainfall as low, moderate, or high?"
    ),
    "temperature": (
        "Do you know the typical temperature around the land?"
    ),
    "species_richness": (
        "Would you describe the number of different species around the land as low, moderate, or high?"
    ),
    "habitat_diversity": (
        "Does the area contain different habitats such as trees, hedgerows, grass, ponds, or other natural patches?"
    ),
    "pollution": (
        "Is there any noticeable pollution or contamination affecting the area?"
    ),
    "deforestation": (
        "Has there been noticeable tree or natural vegetation loss around the area?"
    ),
}


def extraction_to_facts(
    extraction: ProfileExtraction,
) -> dict[str, Any]:
    """
    Convert Gemini's ProfileExtraction into the flat field names
    used by ConversationState.
    """

    data = extraction.model_dump(
        exclude_none=True,
        exclude={
            "unknown_fields",
            "context_notes",
        },
    )

    return data


def update_conversation_state(
    state: ConversationState,
    extraction: ProfileExtraction,
) -> None:
    """
    Apply one Gemini extraction result to conversation memory.
    """

    facts = extraction_to_facts(extraction)

    update_known_facts(
        state,
        facts,
    )

    mark_user_declined(
        state,
        extraction.unknown_fields,
    )

    for note in extraction.context_notes:
        add_context_note(
            state,
            note,
        )


def has_environmental_context(
    state: ConversationState,
) -> bool:
    """
    Determine whether the conversation contains enough information
    to begin useful environmental reasoning.

    This intentionally does NOT require a complete profile.
    """

    return len(state.known) > 0 or len(state.context_notes) > 0


def choose_next_question(
    state: ConversationState,
) -> tuple[str | None, str | None]:
    """
    Select one useful missing field to ask about.

    Returns:
        (field_name, question)

    Returns (None, None) when no clarification is currently needed.
    """

    known = state.known
    declined = state.user_declined

    # Farming context:
    # Crop is usually useful before asking detailed management questions.
    if (
        ("land_use" in known and "farm" in str(known["land_use"]).lower())
        and "crop" not in known
        and "crop" not in declined
    ):
        return "crop", FIELD_QUESTIONS["crop"]

    if (
        "crop" in known
        and "cropping_pattern" not in known
        and "cropping_pattern" not in declined
    ):
        return (
            "cropping_pattern",
            FIELD_QUESTIONS["cropping_pattern"],
        )

    # If the user has mentioned soil/context but moisture is unknown,
    # moisture is a useful low-friction qualitative question.
    if (
        (
            "soil_moisture" not in known
            and "soil_moisture" not in declined
        )
        and (
            "soil_ph" in known
            or "organic_carbon" in known
            or any(
                "soil" in note.lower()
                for note in state.context_notes
            )
        )
    ):
        return (
            "soil_moisture",
            FIELD_QUESTIONS["soil_moisture"],
        )

    # Quantitative soil information comes later.
    if (
        "soil_ph" not in known
        and "soil_ph" not in declined
        and (
            "soil_moisture" in known
            or any(
                "soil" in note.lower()
                for note in state.context_notes
            )
        )
    ):
        return "soil_ph", FIELD_QUESTIONS["soil_ph"]

    return None, None


def process_extraction(
    state: ConversationState,
    extraction: ProfileExtraction,
) -> dict[str, Any]:
    """
    Apply extracted information and decide whether Canopy should
    ask a clarification question or proceed with the information
    currently available.

    If the user explicitly does not know the answer to the previous
    question, do not immediately ask another question.
    """

    # Remember which fields were already marked as unknown before
    # processing this turn.
    previously_declined = set(state.user_declined)

    update_conversation_state(
        state,
        extraction,
    )

    # Identify fields that became newly unknown during this turn.
    newly_declined = (
        state.user_declined - previously_declined
    )

    # The user explicitly said they do not know something.
    # Do not immediately replace that with another question.
    if newly_declined:
        return {
            "needs_clarification": False,
            "missing_fields": sorted(newly_declined),
            "response": (
                "No problem. We can work with what you've shared so far. "
                "I'll keep the missing information in mind and won't assume "
                "values you don't know."
            ),
        }

    # No explicit unknown response.
    # Ask only one useful clarification question if needed.
    field_name, question = choose_next_question(
        state
    )

    if question:
        return {
            "needs_clarification": True,
            "missing_fields": [field_name],
            "response": question,
        }

    # We have at least some environmental context.
    if has_environmental_context(state):
        return {
            "needs_clarification": False,
            "missing_fields": [],
            "response": (
                "Got it. I have enough context to reason from "
                "what you've shared so far."
            ),
        }

    # No useful environmental information yet.
    return {
        "needs_clarification": True,
        "missing_fields": [],
        "response": (
            "Tell me whatever you know about the environment "
            "you're working with — even a simple description is enough to start."
        ),
    }


def process_user_message(
    state: ConversationState,
    message: str,
    extraction: ProfileExtraction,
) -> dict[str, Any]:
    """
    Record the user message, process its extracted information,
    and generate the assistant response.
    """

    add_user_message(
        state,
        message,
    )

    result = process_extraction(
        state,
        extraction,
    )

    add_assistant_message(
        state,
        result["response"],
    )

    return result


def process_message(
    state: ConversationState,
    message: str,
) -> dict[str, Any]:
    """
    Full conversational turn:

        user message
            ↓
        context-aware Gemini extraction
            ↓
        memory update
            ↓
        clarification decision
            ↓
        assistant response
    """

    extraction = extract_profile_information(
        message=message,
        conversation_history=state.history,
    )

    return process_user_message(
        state=state,
        message=message,
        extraction=extraction,
    )