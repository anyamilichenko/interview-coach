from typing import Dict, List, Any
from utils.llm_client import MistralClient
from utils.state_manager import StateManager
import json


class EvaluatorAgent:
    def __init__(self, llm_client: MistralClient, state_manager: StateManager):
        self.llm_client = llm_client
        self.state_manager = state_manager

    def generate_final_feedback(self) -> Dict[str, Any]:
        system_prompt = """Ты - старший технический специалист, который анализирует результаты интервью.

На основе всей истории диалога и анализа наблюдателя, сформируй финальный отчет.

Структура отчета:
1. Вердикт (Decision)
2. Анализ Hard Skills (Technical Review)
3. Анализ Soft Skills & Communication
4. Персональный Roadmap (Next Steps)

Формат ответа:
{
    "verdict": {
        "grade": "Junior/Middle/Senior",
        "hiring_recommendation": "Hire/No Hire/Strong Hire",
        "confidence_score": 0-100,
        "summary": "Краткое резюме"
    },
    "hard_skills": {
        "topics_covered": ["topic1", "topic2"],
        "confirmed_skills": ["skill1", "skill2"],
        "knowledge_gaps": [
            {
                "topic": "Название темы",
                "gap": "Описание пробела",
                "correct_answer": "Правильный ответ"
            }
        ]
    },
    "soft_skills": {
        "clarity": "Оценка 1-10 с объяснением",
        "honesty": "Оценка 1-10 с объяснением",
        "engagement": "Оценка 1-10 с объяснением",
        "summary": "Общая оценка soft skills"
    },
    "roadmap": {
        "next_steps": ["step1", "step2"],
        "recommended_topics": ["topic1", "topic2"],
        "timeline": "Рекомендации по срокам"
    },
    "detailed_feedback": "Подробный текст фидбэка для кандидата"
}"""

        full_history = ""
        if self.state_manager.state:
            for i, turn in enumerate(self.state_manager.state.conversation_history, 1):
                full_history += f"Ход {i}:\n"
                full_history += f"Вопрос: {turn.get('agent', '')}\n"
                full_history += f"Ответ: {turn.get('user', '')}\n"
                full_history += f"Мысли: {turn.get('internal_thoughts', '')}\n\n"

        state_summary = self.state_manager.get_state_summary()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""
Информация о кандидате:
Имя: {self.state_manager.state.participant_name if self.state_manager.state else ''}
Позиция: {self.state_manager.state.position if self.state_manager.state else ''}
Грейд: {self.state_manager.state.grade if self.state_manager.state else ''}
Опыт: {self.state_manager.state.experience if self.state_manager.state else ''}

Статистика интервью:
{json.dumps(state_summary, ensure_ascii=False, indent=2)}

Полная история диалога:
{full_history}

Сформируй финальный отчет."""}
        ]

        response = self.llm_client.generate_structured_response(
            "evaluator",
            messages,
            response_format={
                "verdict": {
                    "grade": "string",
                    "hiring_recommendation": "string",
                    "confidence_score": "integer",
                    "summary": "string"
                },
                "hard_skills": {
                    "topics_covered": "list of strings",
                    "confirmed_skills": "list of strings",
                    "knowledge_gaps": "list of objects"
                },
                "soft_skills": {
                    "clarity": "string",
                    "honesty": "string",
                    "engagement": "string",
                    "summary": "string"
                },
                "roadmap": {
                    "next_steps": "list of strings",
                    "recommended_topics": "list of strings",
                    "timeline": "string"
                },
                "detailed_feedback": "string"
            }
        )

        return response