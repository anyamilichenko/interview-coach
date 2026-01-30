from typing import Dict, List, Any
from utils.llm_client import MistralClient
from utils.state_manager import StateManager
import json


class ObserverAgent:
    def __init__(self, llm_client: MistralClient, state_manager: StateManager):
        self.llm_client = llm_client
        self.state_manager = state_manager

    def analyze_response(self, user_message: str, current_topic: str) -> Dict[str, Any]:
        system_prompt = """Ты - наблюдатель на техническом интервью. Анализируй ответы кандидата.

Твои задачи:
1. Оценить качество ответа (0-100)
2. Определить, есть ли в ответе ошибки или галлюцинации
3. Определить уровень уверенности кандидата
4. Дать рекомендации интервьюеру для следующего вопроса
5. Выявить пробелы в знаниях
6. Отметить подтвержденные навыки

Обрати особое внимание на:
- Технические ошибки
- Противоречия с ранее сказанным
- Попытки уйти от ответа
- Несуществующие технологии/факты

Формат ответа:
{
    "confidence_score": 0-100,
    "has_errors": boolean,
    "has_hallucinations": boolean,
    "is_off_topic": boolean,
    "recommendation": "string",
    "next_action": "harder_question|easier_question|clarify|change_topic|continue",
    "knowledge_gaps": ["gap1", "gap2"],
    "confirmed_skills": ["skill1", "skill2"],
    "analysis": "Подробный анализ ответа"
}"""

        context = ""
        if self.state_manager.state and self.state_manager.state.conversation_history:
            recent = self.state_manager.state.conversation_history[-2:]  # Last 2 turns
            for turn in recent:
                context += f"Интервьюер: {turn.get('agent', '')}\n"
                context += f"Кандидат: {turn.get('user', '')}\n\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""
Текущая тема: {current_topic}
Позиция кандидата: {self.state_manager.state.position if self.state_manager.state else ''}
Грейд: {self.state_manager.state.grade if self.state_manager.state else ''}

Контекст диалога:
{context}

Ответ кандидата: {user_message}

Проанализируй ответ."""}
        ]

        response = self.llm_client.generate_structured_response(
            "observer",
            messages,
            response_format={
                "confidence_score": "integer 0-100",
                "has_errors": "boolean",
                "has_hallucinations": "boolean",
                "is_off_topic": "boolean",
                "recommendation": "string",
                "next_action": "string",
                "knowledge_gaps": "list of strings",
                "confirmed_skills": "list of strings",
                "analysis": "string"
            }
        )

        if self.state_manager.state:
            confidence = response.get("confidence_score", 50)
            self.state_manager.update_difficulty(confidence)

            for gap in response.get("knowledge_gaps", []):
                self.state_manager.add_knowledge_gap(gap)

            for skill in response.get("confirmed_skills", []):
                self.state_manager.add_confirmed_skill(skill)

        return response