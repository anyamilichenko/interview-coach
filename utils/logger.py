import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path


class InterviewLogger:
    def __init__(self, output_dir: str = "logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def create_log_structure(self, participant_name: str) -> Dict[str, Any]:
        return {
            "participant_name": participant_name,
            "timestamp": datetime.now().isoformat(),
            "turns": [],
            "final_feedback": ""
        }

    def add_turn(self, log_data: Dict[str, Any], turn_id: int,
                 agent_visible_message: str, user_message: str,
                 internal_thoughts: str) -> None:
        turn = {
            "turn_id": turn_id,
            "agent_visible_message": agent_visible_message,
            "user_message": user_message,
            "internal_thoughts": internal_thoughts
        }
        log_data["turns"].append(turn)

    def add_final_feedback(self, log_data: Dict[str, Any], feedback: str) -> None:
        log_data["final_feedback"] = feedback

    def save_log(self, log_data: Dict[str, Any], filename: str = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = log_data["participant_name"].replace(" ", "_")
            filename = f"interview_log_{name}_{timestamp}.json"

        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2, default=str)

        return str(filepath)

    def format_internal_thoughts(self, observer_thought: str, interviewer_thought: str) -> str:
        return f"[Observer]: {observer_thought}\n[Interviewer]: {interviewer_thought}"