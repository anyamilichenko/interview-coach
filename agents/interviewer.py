from typing import Dict, List, Any, Tuple
from utils.llm_client import MistralClient
from utils.state_manager import StateManager
import json


class InterviewerAgent:
    def __init__(self, llm_client: MistralClient, state_manager: StateManager):
        self.llm_client = llm_client
        self.state_manager = state_manager

    def generate_initial_question(self) -> Tuple[str, str]:
        state = self.state_manager.state
        if not state:
            return "Привет! Расскажи о своем опыте.", "Ошибка: состояние не инициализировано"

        system_prompt = """Ты - опытный технический интервьюер. Твоя задача - задавать технические вопросы кандидату.

Ты должен:
1. Начать с приветствия и представиться
2. Задать первый технический вопрос, соответствующий позиции и грейду кандидата
3. Вопрос должен быть достаточно простым для разминки
4. Не задавай сразу сложных вопросов

Формат ответа:
{
    "visible_message": "Твое сообщение кандидату",
    "internal_thought": "Твои мысли о том, почему задал этот вопрос"
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""
Кандидат:
Имя: {state.participant_name}
Позиция: {state.position}
Грейд: {state.grade}
Опыт: {state.experience}

Сгенерируй приветственное сообщение и первый вопрос."""}
        ]

        response = self.llm_client.generate_structured_response(
            "interviewer",
            messages,
            response_format={
                "visible_message": "string",
                "internal_thought": "string"
            }
        )

        return response.get("visible_message", "Привет! Расскажи о своем опыте."), \
            response.get("internal_thought", "Начинаю с базового вопроса.")

    def generate_next_question(self, observer_analysis: Dict[str, Any]) -> Tuple[str, str]:
        state = self.state_manager.state
        if not state:
            return "Расскажи подробнее о своем опыте.", "Ошибка: состояние не инициализировано"

        system_prompt = """Ты - технический интервьюер. На основе анализа наблюдателя и истории диалога, определи следующий вопрос.

Ты должен:
1. Учитывать рекомендации наблюдателя
2. Адаптировать сложность вопроса (если кандидат отвечал хорошо - усложни, если плохо - упрости)
3. Не повторять вопросы
4. Естественно вести диалог
5. Если кандидат пытается сменить тему - вежливо вернуть к интервью
6. Если кандидат спрашивает о компании/задачах - кратко ответить и вернуться к интервью

Формат ответа:
{
    "visible_message": "Твое сообщение кандидату",
    "internal_thought": "Твои мысли о выборе вопроса",
    "topic": "Тема вопроса"
}"""

        recent_convo = ""
        if state.conversation_history:
            recent = state.conversation_history[-3:] if len(
                state.conversation_history) >= 3 else state.conversation_history
            for turn in recent:
                recent_convo += f"Интервьюер: {turn.get('agent', '')}\n"
                recent_convo += f"Кандидат: {turn.get('user', '')}\n"
                recent_convo += f"Мысли: {turn.get('internal_thoughts', '')}\n\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""
Информация о кандидате:
Позиция: {state.position}
Грейд: {state.grade}
Опыт: {state.experience}

Текущий уровень сложности: {state.difficulty_level}
Пройденные темы: {', '.join(state.topics_covered)}

Анализ наблюдателя:
{json.dumps(observer_analysis, ensure_ascii=False, indent=2)}

Недавний диалог:
{recent_convo}

Сгенерируй следующий вопрос."""}
        ]

        response = self.llm_client.generate_structured_response(
            "interviewer",
            messages,
            response_format={
                "visible_message": "string",
                "internal_thought": "string",
                "topic": "string"
            }
        )

        topic = response.get("topic", "Общая тема")
        if topic:
            self.state_manager.add_topic(topic)

        return response.get("visible_message", "Расскажи подробнее о своем опыте."), \
            response.get("internal_thought", "Перехожу к следующей теме.")

    def handle_off_topic(self, user_message: str) -> Tuple[str, str]:
        state = self.state_manager.state
        if not state:
            return "Давайте вернемся к техническим вопросам.", "Ошибка: состояние не инициализировано"

        system_prompt = """Кандидат пытается уйти от темы или говорит о чем-то не связанном с интервью.
Вежливо верни его к интервью и задай технический вопрос."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""
Кандидат сказал: {user_message}

Верни кандидата к техническому интервью и задай вопрос по теме {state.position}.

Формат ответа:
{{
    "visible_message": "Твое сообщение кандидату",
    "internal_thought": "Твои мысли"
}}"""}
        ]

        response = self.llm_client.generate_structured_response(
            "interviewer",
            messages,
            response_format={
                "visible_message": "string",
                "internal_thought": "string"
            }
        )

        return response.get("visible_message", "Давайте вернемся к техническим вопросам."), \
            response.get("internal_thought", "Кандидат пытается уйти от темы.")