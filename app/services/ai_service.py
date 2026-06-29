"""AI service — Gemini integration for conversations and explanations."""

import json
import logging
from uuid import UUID

import google.generativeai as genai
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.ai import AiConversationMessage
from app.models.user import ProficiencyLevel
from app.schemas.ai import (
    AiChatResponse,
    ChatMessage,
    GrammarIssue,
    MessageResponse,
    PronunciationTip,
)

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            self.model = None

    async def get_conversation_response(
        self,
        db: AsyncSession,
        user_id: UUID,
        conversation_id: UUID,
        user_message: str,
        history: list[AiConversationMessage],
        user_level: ProficiencyLevel,
        base_language: str,
    ) -> AiChatResponse:
        """Call Gemini to get a response and feedback."""
        if not self.model:
            # Mock response if no API key
            return self._mock_response(conversation_id, user_message)

        prompt = f"""
        You are Marie, a friendly and patient French language tutor.
        The student's level is {user_level.value} (CEFR). Respond in a way that
        matches this level — simpler vocabulary for A1/A2, richer for B2/C1.
        Always respond in French first, then provide a brief translation in {base_language}
        in parentheses if the level is A1 or A2.

        After your main response, output a JSON block in this exact format:
        <feedback>
        {{
          "grammar_issues": [
            {{"original": "...", "corrected": "...", "explanation": "..."}}
          ],
          "pronunciation_tips": [
            {{"word": "...", "ipa": "...", "tip": "..."}}
          ],
          "fluency_note": "..."
        }}
        </feedback>
        """

        # Prepare chat history for Gemini
        contents = []
        for msg in history[-10:]:  # Last 10 messages for context
            role = "user" if msg.is_user_message else "model"
            contents.append({"role": role, "parts": [msg.content]})

        contents.append({"role": "user", "parts": [user_message]})

        try:
            chat = self.model.start_chat(history=contents[:-1])
            response = await chat.send_message_async(user_message)
            full_text = response.text

            # Parse feedback
            reply_text = full_text
            grammar_issues = []
            pronunciation_tips = []

            if "<feedback>" in full_text and "</feedback>" in full_text:
                parts = full_text.split("<feedback>")
                reply_text = parts[0].strip()
                feedback_str = parts[1].split("</feedback>")[0].strip()
                try:
                    feedback_json = json.loads(feedback_str)
                    grammar_issues = [
                        GrammarIssue(**i) for i in feedback_json.get("grammar_issues", [])
                    ]
                    pronunciation_tips = [
                        PronunciationTip(**i) for i in feedback_json.get("pronunciation_tips", [])
                    ]
                except Exception:
                    logger.error("Failed to parse Gemini feedback JSON")

            # Save messages
            user_msg_obj = AiConversationMessage(
                conversation_id=conversation_id, is_user_message=True, content=user_message
            )
            ai_msg_obj = AiConversationMessage(
                conversation_id=conversation_id, is_user_message=False, content=reply_text
            )
            db.add_all([user_msg_obj, ai_msg_obj])
            await db.commit()
            await db.refresh(user_msg_obj)
            await db.refresh(ai_msg_obj)

            return AiChatResponse(
                user_message=MessageResponse.model_validate(user_msg_obj),
                assistant_message=MessageResponse.model_validate(ai_msg_obj),
                grammar_feedback=grammar_issues,
                pronunciation_tips=pronunciation_tips,
            )
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._mock_response(conversation_id, user_message)

    async def generate_chat_text(
        self,
        messages: list[ChatMessage],
        system_context: str | None = None,
    ) -> str:
        """Generate a simple assistant reply for the mobile AI tutor sheet."""
        if not messages:
            return "Bonjour! What would you like help with today?"

        system_prompt = system_context or (
            "You are a helpful, friendly French language tutor. Keep answers concise, "
            "clear, and appropriate for a language learner."
        )

        if settings.AI_GATEWAY_API_KEY:
            gateway_text = await self._generate_ai_gateway_text(messages, system_prompt)
            if gateway_text:
                return gateway_text

        if not self.model:
            return "Bonjour! I am your French tutor. Ask me about the lesson and I will help."

        transcript = "\n".join(
            f"{message.role}: {message.content}" for message in messages[-12:]
        )
        prompt = f"{system_prompt}\n\nConversation so far:\n{transcript}\n\nassistant:"

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            return "Sorry, I am having trouble answering right now. Please try again in a moment."

    async def _generate_ai_gateway_text(
        self,
        messages: list[ChatMessage],
        system_prompt: str,
    ) -> str | None:
        """Call Vercel AI Gateway through its OpenAI-compatible chat endpoint."""
        payload_messages = [{"role": "system", "content": system_prompt}]
        payload_messages.extend(
            {
                "role": "assistant" if message.role == "assistant" else "user",
                "content": message.content,
            }
            for message in messages[-12:]
        )
        payload = {
            "model": settings.AI_GATEWAY_MODEL,
            "messages": payload_messages,
        }
        headers = {
            "Authorization": f"Bearer {settings.AI_GATEWAY_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://ai-gateway.vercel.sh/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip() if isinstance(content, str) else None
        except Exception as e:
            logger.error(f"Vercel AI Gateway chat error: {e}")
            return None

    def _mock_response(self, conversation_id: UUID, user_message: str) -> AiChatResponse:
        """Fallback mock response."""
        return AiChatResponse(
            user_message=MessageResponse(
                id=UUID(int=0),
                conversation_id=conversation_id,
                is_user_message=True,
                content=user_message,
            ),
            assistant_message=MessageResponse(
                id=UUID(int=1),
                conversation_id=conversation_id,
                is_user_message=False,
                content="Bonjour! Je suis votre tutrice de français. (Hello! I am your French tutor.)",
            ),
            grammar_feedback=[],
            pronunciation_tips=[],
        )

    async def generate_explanation(
        self, concept: str, user_input: str, base_language: str, level: str
    ) -> str:
        """Generate a short explanation for a concept."""
        if not self.model:
            return f"Explication pour {concept} en {base_language}."

        prompt = f"Explain {concept} in {base_language} for a {level} French learner. Use simple language. Give 1-2 examples in French with translation. Keep it under 150 words."
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini explanation error: {e}")
            return f"Désolé, je ne peux pas expliquer {concept} pour le moment."


ai_service = GeminiService()
