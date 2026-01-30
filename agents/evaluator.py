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

На основе всей истории диалога и анализа наблюдателя, сформируй финальный отчет, даже если данных было мало.

Структура отчета:
1. Вердикт (Decision)
2. Анализ Hard Skills (Technical Review)
3. Анализ Soft Skills & Communication
4. Персональный Roadmap (Next Steps)

Даже если данных мало, постарайся дать максимально подробный анализ на основе того, что есть все равно сформируй все необходимые элементы отчета.

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

        if not self.state_manager or not self.state_manager.state:
            return self._create_default_feedback()

        full_history = ""
        if self.state_manager.state.conversation_history:
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
Имя: {self.state_manager.state.participant_name}
Позиция: {self.state_manager.state.position}
Грейд: {self.state_manager.state.grade}
Опыт: {self.state_manager.state.experience}

Статистика интервью:
{json.dumps(state_summary, ensure_ascii=False, indent=2)}

Полная история диалога:
{full_history}

Сформируй финальный отчет."""}
        ]

        try:
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


            if not response:
                return self._create_default_feedback()

            return response

        except Exception as e:
            print(f"Ошибка генерации фидбэка: {e}")
            return self._create_default_feedback()

    def _create_default_feedback(self) -> Dict[str, Any]:
        return {
            "verdict": {
                "grade": "Junior",
                "hiring_recommendation": "No Hire",
                "confidence_score": 50,
                "summary": "Недостаточно данных для полноценной оценки. Кандидат рано завершил интервью."
            },
            "hard_skills": {
                "topics_covered": ["Базовые вопросы"],
                "confirmed_skills": ["Базовые знания"],
                "knowledge_gaps": [
                    {
                        "topic": "Завершение интервью",
                        "gap": "Кандидат рано завершил интервью",
                        "correct_answer": "Рекомендуется пройти полное интервью для оценки навыков"
                    }
                ]
            },
            "soft_skills": {
                "clarity": "5/10 - ответы были краткими",
                "honesty": "6/10 - признал незнание некоторых тем",
                "engagement": "4/10 - низкая вовлеченность в диалог",
                "summary": "Требуется больше данных для оценки"
            },
            "roadmap": {
                "next_steps": ["Пройти полное техническое интервью", "Изучить базовые концепции"],
                "recommended_topics": ["Основы программирования", "Технологии из резюме"],
                "timeline": "1-2 месяца подготовки"
            },
            "detailed_feedback": "Кандидат рано завершил интервью, что не позволило провести полноценную оценку. Рекомендуется подготовиться и пройти полное интервью."
        }