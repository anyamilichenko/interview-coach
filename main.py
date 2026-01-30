from agents.interviewer import InterviewerAgent
from agents.observer import ObserverAgent
from agents.evaluator import EvaluatorAgent
from utils.llm_client import MistralClient
from utils.state_manager import StateManager
from utils.logger import InterviewLogger
from typing import Optional, Dict, Any
from config import Config
import json


class MultiAgentInterviewCoach:
    def __init__(self):
        Config.validate()

        self.llm_client = MistralClient()
        self.state_manager = StateManager()
        self.logger = InterviewLogger()

        self.interviewer = None
        self.observer = None
        self.evaluator = None

        self.log_data: Optional[Dict[str, Any]] = None
        self.is_interview_active = False
        self.turn_count = 0

    def start_interview(self, participant_name: str, position: str,
                        grade: str, experience: str) -> str:

        self.state_manager.initialize_state(participant_name, position, grade, experience)

        self.interviewer = InterviewerAgent(self.llm_client, self.state_manager)
        self.observer = ObserverAgent(self.llm_client, self.state_manager)
        self.evaluator = EvaluatorAgent(self.llm_client, self.state_manager)

        self.log_data = self.logger.create_log_structure(participant_name)

        visible_message, internal_thought = self.interviewer.generate_initial_question()

        self.is_interview_active = True
        self.turn_count = 0

        return visible_message

    def process_response(self, user_message: str) -> tuple:
        if not self.is_interview_active:
            return "Интервью не активно. Начните новое интервью.", "", False

        self.turn_count += 1

        end_phrases = ["стоп интервью", "завершить интервью", "давай фидбэк",
                       "конец интервью", "стоп игра", "фидбэк", "стоп", "закончить", "завершить"]
        if any(phrase in user_message.lower() for phrase in end_phrases):
            return self._end_interview(), "", True

        current_topic = ""
        if self.state_manager.state:
            current_topic = self.state_manager.state.current_topic

        observer_analysis = self.observer.analyze_response(user_message, current_topic)

        if observer_analysis.get("is_off_topic", False):
            visible_message, internal_thought = self.interviewer.handle_off_topic(user_message)
        else:
            visible_message, internal_thought = self.interviewer.generate_next_question(observer_analysis)

        observer_thought = observer_analysis.get("analysis", "Анализ ответа")
        formatted_thoughts = f"[Observer]: {observer_thought}\n[Interviewer]: {internal_thought}"

        if self.log_data:
            prev_agent_message = ""
            if self.log_data["turns"]:
                prev_agent_message = self.log_data["turns"][-1]["agent_visible_message"]

            self.logger.add_turn(
                self.log_data,
                self.turn_count,
                visible_message,
                user_message,
                formatted_thoughts
            )

        if (self.state_manager.state and
                self.state_manager.state.question_count >= Config.MAX_QUESTIONS):
            return self._end_interview(), "", True

        return visible_message, formatted_thoughts, False

    def _end_interview(self) -> str:
        self.is_interview_active = False

        feedback_report = self.evaluator.generate_final_feedback()

        feedback_text = self._format_feedback(feedback_report)

        if self.log_data:
            self.logger.add_final_feedback(self.log_data, feedback_text)

            filename = f"interview_log_{self.turn_count}.json"
            filepath = self.logger.save_log(self.log_data, filename)
            print(f"\nЛог сохранен в: {filepath}")

        return feedback_text

    def _format_feedback(self, feedback_report: Dict[str, Any]) -> str:
        if not feedback_report:
            return "Не удалось сгенерировать фидбэк."

        lines = []
        lines.append("ФИНАЛЬНЫЙ ФИДБЭК")


        verdict = feedback_report.get("verdict", {})
        lines.append("\nВЕРДИКТ:")
        lines.append(f"Уровень: {verdict.get('grade', 'N/A')}")
        lines.append(f"Рекомендация: {verdict.get('hiring_recommendation', 'N/A')}")
        lines.append(f"Уверенность: {verdict.get('confidence_score', 0)}%")
        lines.append(f"Резюме: {verdict.get('summary', '')}")

        hard_skills = feedback_report.get("hard_skills", {})
        lines.append("\nАНАЛИЗ HARD SKILLS:")

        topics = hard_skills.get("topics_covered", [])
        if topics:
            lines.append(f"Пройденные темы: {', '.join(topics)}")

        confirmed = hard_skills.get("confirmed_skills", [])
        if confirmed:
            lines.append("\nПодтвержденные навыки:")
            for skill in confirmed:
                lines.append(f"  • {skill}")

        gaps = hard_skills.get("knowledge_gaps", [])
        if gaps:
            lines.append("\nПробелы в знаниях:")
            for gap in gaps:
                if isinstance(gap, dict):
                    lines.append(f"  • Тема: {gap.get('topic', '')}")
                    lines.append(f"    Пробел: {gap.get('gap', '')}")
                    lines.append(f"    Правильный ответ: {gap.get('correct_answer', '')}")
                else:
                    lines.append(f"  • {gap}")

        soft_skills = feedback_report.get("soft_skills", {})
        lines.append("\nАНАЛИЗ SOFT SKILLS:")
        lines.append(f"Ясность изложения: {soft_skills.get('clarity', 'N/A')}")
        lines.append(f"Честность: {soft_skills.get('honesty', 'N/A')}")
        lines.append(f"Вовлеченность: {soft_skills.get('engagement', 'N/A')}")
        lines.append(f"Общая оценка: {soft_skills.get('summary', '')}")

        roadmap = feedback_report.get("roadmap", {})
        lines.append("\nПЕРСОНАЛЬНЫЙ ROADMAP:")

        next_steps = roadmap.get("next_steps", [])
        if next_steps:
            lines.append("Следующие шаги:")
            for step in next_steps:
                lines.append(f"  • {step}")

        recommended = roadmap.get("recommended_topics", [])
        if recommended:
            lines.append("\nРекомендуемые темы для изучения:")
            for topic in recommended:
                lines.append(f"  • {topic}")

        timeline = roadmap.get("timeline", "")
        if timeline:
            lines.append(f"\nРекомендуемые сроки: {timeline}")

        detailed = feedback_report.get("detailed_feedback", "")
        if detailed:
            lines.append("\n" + "=" * 60)
            lines.append("ДЕТАЛЬНЫЙ ФИДБЭК:")
            lines.append("=" * 60)
            lines.append(detailed)

        return "\n".join(lines)

    def save_current_log(self, filename: str = None) -> str:
        if not self.log_data:
            return "Нет данных для сохранения"

        filepath = self.logger.save_log(self.log_data, filename)
        return f"Лог сохранен в: {filepath}"


interview_coach = MultiAgentInterviewCoach()