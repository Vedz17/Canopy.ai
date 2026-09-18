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

from schemas import (
    Biodiversity,
    Climate,
    EnvironmentalProfile,
    HumanImpact,
    Land,
    ProfileExtraction,
    Soil,
)


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
        "Do you have a soil organic carbon value from a soil test? "
        "If not, we can continue without it."
    ),
    "rainfall": (
        "Would you describe the area's rainfall as low, moderate, or high?"
    ),
    "temperature": (
        "Do you know the typical temperature around the land?"
    ),
    "species_richness": (
        "Would you describe the number of different species around the land "
        "as low, moderate, or high?"
    ),
    "habitat_diversity": (
        "Does the area contain different habitats such as trees, hedgerows, "
        "grass, ponds, or other natural patches?"
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
    Convert the ProfileExtraction result into the flat environmental
    field names used by ConversationState.

    Control fields such as environmental_relevance are deliberately
    excluded because they are not environmental facts.
    """

    data = extraction.model_dump(
        exclude_none=True,
        exclude={
            "environmental_relevance",
            "recommendation_requested",
            "unknown_fields",
            "context_notes",
        },
    )

    return data


def build_environmental_profile(
    state: ConversationState,
) -> EnvironmentalProfile:
    """
    Convert the environmental facts currently known in the
    conversation into the existing EnvironmentalProfile schema.

    Missing values remain None. No values are inferred here.
    """

    known = state.known

    return EnvironmentalProfile(
        soil=Soil(
            ph=known.get("soil_ph"),
            organic_carbon=known.get("organic_carbon"),
            moisture=known.get("soil_moisture"),
        ),
        climate=Climate(
            temperature=known.get("temperature"),
            rainfall=known.get("rainfall"),
        ),
        land=Land(
            land_use=known.get("land_use"),
            crop=known.get("crop"),
            cropping_pattern=known.get("cropping_pattern"),
        ),
        biodiversity=Biodiversity(
            species_richness=known.get("species_richness"),
            habitat_diversity=known.get("habitat_diversity"),
        ),
        human_impact=HumanImpact(
            pollution=known.get("pollution"),
            deforestation=known.get("deforestation"),
        ),
    )


def update_conversation_state(
    state: ConversationState,
    extraction: ProfileExtraction,
) -> None:
    """
    Apply one extraction result to conversation memory.
    """

    facts = extraction_to_facts(
        extraction
    )

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
    Determine whether the conversation contains at least some
    useful environmental information.

    This does NOT require a complete environmental profile.
    """

    return (
        len(state.known) > 0
        or len(state.context_notes) > 0
    )


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

    # ---------------------------------------------------------
    # 1. Farming context
    # ---------------------------------------------------------

    # Crop is useful before asking detailed management questions.

    if (
        (
            "land_use" in known
            and "farm" in str(known["land_use"]).lower()
        )
        and "crop" not in known
        and "crop" not in declined
    ):
        return (
            "crop",
            FIELD_QUESTIONS["crop"],
        )

    # ---------------------------------------------------------
    # 2. Cropping pattern
    # ---------------------------------------------------------

    # Once a crop is known, understand whether the system is
    # monoculture, rotation, or mixed cropping.

    if (
        "crop" in known
        and "cropping_pattern" not in known
        and "cropping_pattern" not in declined
    ):
        return (
            "cropping_pattern",
            FIELD_QUESTIONS["cropping_pattern"],
        )

    # ---------------------------------------------------------
    # 3. Soil moisture
    # ---------------------------------------------------------

    # If soil has been mentioned but moisture is unknown,
    # ask a simple qualitative question first.

    if (
        "soil_moisture" not in known
        and "soil_moisture" not in declined
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

    # ---------------------------------------------------------
    # 4. Soil pH
    # ---------------------------------------------------------

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
        return (
            "soil_ph",
            FIELD_QUESTIONS["soil_ph"],
        )

    return None, None


def has_sufficient_reasoning_context(
    state: ConversationState,
) -> bool:
    """
    Decide whether the conversation contains enough environmental
    information for a recommendation.

    This intentionally does not require a complete profile.
    """

    known = state.known

    # Strong site-specific context:
    # at least two explicit environmental facts.
    if len(known) >= 2:
        return True

    # A qualitative environmental note plus one explicit fact
    # is also useful context.
    if len(known) >= 1 and len(state.context_notes) >= 1:
        return True

    return False


def process_extraction(
    state: ConversationState,
    extraction: ProfileExtraction,
) -> dict[str, Any]:
    """
    Apply extracted information and decide what Canopy should do next.

    Possible outcomes:

    1. Non-environmental message:
       redirect the conversation without reasoning.

    2. Explicitly unknown information:
       acknowledge it without repeating the question.

    3. Environmental information but useful context is still missing:
       ask one targeted clarification.

    4. Environmental information with no further clarification needed:
       mark the conversation ready for reasoning.

    No environmental reasoning is performed in this function.
    """

    # Remember which fields were already marked as unknown
    # before processing this turn.
    previously_declined = set(
        state.user_declined
    )

    update_conversation_state(
        state,
        extraction,
    )

    # Identify fields that became newly unknown during this turn.
    newly_declined = (
        state.user_declined - previously_declined
    )

    # ---------------------------------------------------------
    # CASE 1: Explicit "I don't know" / cannot provide information
    # ---------------------------------------------------------

    # This must happen before the relevance check because a contextual
    # reply such as "I don't know" may itself not be environmental,
    # while still being a valid answer to Canopy's previous question.

    if newly_declined:
        can_reason = has_sufficient_reasoning_context(state)

        if can_reason:
            response = (
                "No problem — we can proceed without that information. "
                "I won't assume a value you don't know. "
                "I have enough environmental context to assess your situation "
                "using the information you've provided."
            )
        else:
            response = (
                "No problem — we can continue without that information. "
                "I won't assume a value you don't know. "
                "Tell me a little more about the environmental conditions "
                "if you'd like a more specific assessment."
            )

        return {
            "needs_clarification": False,
            "can_reason": can_reason,
            "missing_fields": sorted(newly_declined),
            "response": response,
        }

    # ---------------------------------------------------------
    # CASE 2: Message is not environmentally relevant
    # ---------------------------------------------------------

    # This is semantic, not keyword-based. The extraction component
    # decides whether the message is relevant to environmental assessment.

    if not extraction.environmental_relevance:
        return {
            "needs_clarification": False,
            "can_reason": False,
            "missing_fields": [],
            "response": (
                "I can help with the environmental assessment. "
                "Tell me anything you know about the land, soil, crops, "
                "climate, water, biodiversity, or other environmental "
                "conditions you're assessing."
            ),
        }

    # ---------------------------------------------------------
    # CASE 3: Environmental message but no usable context yet
    # ---------------------------------------------------------

    # Example:
    # "What should I do about biodiversity?"
    #
    # This is environmentally relevant, but there is not enough
    # site-specific information to make a responsible recommendation.

    if not has_environmental_context(state):
        return {
            "needs_clarification": True,
            "can_reason": False,
            "missing_fields": [],
            "response": (
                "I can help with that. Tell me whatever you know about "
                "the environment you're assessing — even a simple "
                "description of the land or soil is enough to start."
            ),
        }

    # ---------------------------------------------------------
    # CASE 4: Environmental context exists
    # ---------------------------------------------------------

    # Ask at most ONE useful targeted question.

    field_name, question = choose_next_question(
        state
    )

    if question:
        return {
            "needs_clarification": True,
            "can_reason": False,
            "missing_fields": [field_name],
            "response": question,
        }

    # ---------------------------------------------------------
    # CASE 5: Enough context for environmental reasoning
    # ---------------------------------------------------------

    # This does NOT mean the profile is complete.
    # It only means our clarification policy has no higher-priority
    # question to ask before reasoning.

    if not has_sufficient_reasoning_context(state):
        return {
            "needs_clarification": False,
            "can_reason": False,
            "missing_fields": [],
            "response": (
                "Got it. Tell me a little more about the environmental "
                "conditions you're assessing, or ask me what you should "
                "do to improve them."
            ),
        }

    # ---------------------------------------------------------
    # CASE 6: Ready for RAG + environmental reasoning
    # ---------------------------------------------------------

    return {
        "needs_clarification": False,
        "can_reason": True,
        "missing_fields": [],
        "response": (
            "Got it. I have enough context to reason from "
            "what you've shared."
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
        context-aware Cohere extraction
            ↓
        memory update
            ↓
        relevance check
            ↓
        clarification decision
            ↓
        reasoning readiness decision
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