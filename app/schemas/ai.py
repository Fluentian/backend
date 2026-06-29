"""AI domain schemas: conversations, messages, explanations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ── Conversation ────────────────────────────────────────


class CreateConversationRequest(BaseModel):
    title: str | None = None
    mode: str = "general"


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str | None = None
    started_at: datetime
    ended_at: datetime | None = None


class ConversationDetailResponse(ConversationResponse):
    messages: list["MessageResponse"] = []


# ── Message ─────────────────────────────────────────────


class SendMessageRequest(BaseModel):
    content: str
    audio_asset_id: UUID | None = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    is_user_message: bool
    content: str
    pronunciation_score: float | None = None
    created_at: datetime


class GrammarIssue(BaseModel):
    original: str
    corrected: str
    explanation: str


class PronunciationTip(BaseModel):
    word: str
    ipa: str
    tip: str


class AiChatResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    grammar_feedback: list[GrammarIssue] = []
    pronunciation_tips: list[PronunciationTip] = []


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    systemContext: str | None = None


class ChatTextResponse(BaseModel):
    text: str


# ── Explanation ─────────────────────────────────────────


class ExplainRequest(BaseModel):
    source_type: str
    source_id: UUID
    user_input: str
    base_language_id: UUID


class ExplanationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    explanation_text: str
    created_at: datetime


# ── Conversation End ────────────────────────────────────


class ConversationSummary(BaseModel):
    total_messages: int
    duration_minutes: float
