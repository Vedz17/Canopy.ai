from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationState:
    """
    Stores everything Canopy AI needs to remember during one conversation.
    """

    session_id: str

    # Structured environmental facts discovered so far.
    known: dict[str, Any] = field(default_factory=dict)

    # Fields that are genuinely unknown to the user.
    user_declined: set[str] = field(default_factory=set)

    # Conversation history.
    history: list[dict[str, str]] = field(default_factory=list)

    # Qualitative/contextual information that should not be
    # forced into a numeric environmental field.
    context_notes: list[str] = field(default_factory=list)


# Hackathon-friendly session store.
# This keeps memory alive while the FastAPI process is running.
_sessions: dict[str, ConversationState] = {}


def get_or_create_session(session_id: str) -> ConversationState:
    """
    Return an existing conversation state or create a new one.
    """

    session_id = session_id.strip()

    if not session_id:
        raise ValueError("session_id cannot be empty")

    if session_id not in _sessions:
        _sessions[session_id] = ConversationState(
            session_id=session_id
        )

    return _sessions[session_id]


def add_user_message(
    state: ConversationState,
    message: str,
) -> None:
    """
    Store a user message in conversation history.
    """

    state.history.append(
        {
            "role": "user",
            "content": message,
        }
    )


def add_assistant_message(
    state: ConversationState,
    message: str,
) -> None:
    """
    Store an assistant response in conversation history.
    """

    state.history.append(
        {
            "role": "assistant",
            "content": message,
        }
    )


def update_known_facts(
    state: ConversationState,
    facts: dict[str, Any],
) -> None:
    """
    Merge newly discovered facts into the conversation state.

    Only explicitly provided values are added.
    Missing values are never invented.
    """

    for field_name, value in facts.items():

        if value is None:
            continue

        if isinstance(value, str) and not value.strip():
            continue

        state.known[field_name] = value

        # If the user later provides a value for something
        # previously marked unknown, the new explicit value wins.
        state.user_declined.discard(field_name)


def mark_user_declined(
    state: ConversationState,
    fields: list[str],
) -> None:
    """
    Record fields the user explicitly says they do not know.
    """

    for field_name in fields:
        if field_name:
            state.user_declined.add(field_name)


def add_context_note(
    state: ConversationState,
    note: str,
) -> None:
    """
    Preserve qualitative information without converting it
    into a fabricated numeric measurement.
    """

    note = note.strip()

    if note and note not in state.context_notes:
        state.context_notes.append(note)


def get_conversation_state(
    session_id: str,
) -> dict[str, Any]:
    """
    Return a serializable snapshot of the current conversation state.
    """

    state = get_or_create_session(session_id)

    return {
        "session_id": state.session_id,
        "known": state.known,
        "unknown": sorted(state.user_declined),
        "history": state.history,
        "context_notes": state.context_notes,
    }