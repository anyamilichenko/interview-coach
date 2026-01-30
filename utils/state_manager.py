from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class InterviewState(BaseModel):
    participant_name: str
    position: str
    grade: str
    experience: str

    conversation_history: List[Dict[str, str]] = []

    topics_covered: List[str] = []

    candidate_answers: List[Dict[str, Any]] = []

    current_topic: str = ""
    difficulty_level: str = "medium"  # easy, medium, hard
    question_count: int = 0

    confidence_scores: List[int] = []
    knowledge_gaps: List[str] = []
    confirmed_skills: List[str] = []

    class Config:
        arbitrary_types_allowed = True


class StateManager:
    def __init__(self):
        self.state: Optional[InterviewState] = None

    def initialize_state(self, participant_name: str, position: str,
                         grade: str, experience: str) -> InterviewState:
        self.state = InterviewState(
            participant_name=participant_name,
            position=position,
            grade=grade,
            experience=experience
        )
        return self.state

    def add_conversation_turn(self, agent_message: str, user_message: str,
                              internal_thoughts: str) -> None:
        if self.state:
            self.state.conversation_history.append({
                "agent": agent_message,
                "user": user_message,
                "internal_thoughts": internal_thoughts
            })
            self.state.question_count += 1

    def update_difficulty(self, confidence: int) -> None:
        if not self.state:
            return

        self.state.confidence_scores.append(confidence)

        if len(self.state.confidence_scores) > 0:
            avg_confidence = sum(self.state.confidence_scores) / len(self.state.confidence_scores)

            if avg_confidence > 80:
                self.state.difficulty_level = "hard"
            elif avg_confidence < 40:
                self.state.difficulty_level = "easy"
            else:
                self.state.difficulty_level = "medium"

    def add_topic(self, topic: str) -> None:
        if self.state and topic not in self.state.topics_covered:
            self.state.topics_covered.append(topic)

    def add_knowledge_gap(self, gap: str) -> None:
        if self.state and gap not in self.state.knowledge_gaps:
            self.state.knowledge_gaps.append(gap)

    def add_confirmed_skill(self, skill: str) -> None:
        if self.state and skill not in self.state.confirmed_skills:
            self.state.confirmed_skills.append(skill)

    def get_state_summary(self) -> Dict[str, Any]:
        if not self.state:
            return {}

        return {
            "question_count": self.state.question_count,
            "topics_covered": self.state.topics_covered,
            "difficulty_level": self.state.difficulty_level,
            "avg_confidence": sum(self.state.confidence_scores) / len(self.state.confidence_scores)
            if self.state.confidence_scores else 0,
            "knowledge_gaps": self.state.knowledge_gaps,
            "confirmed_skills": self.state.confirmed_skills
        }