import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")

    INTERVIEWER_MODEL = "mistral-large-latest"
    OBSERVER_MODEL = "mistral-large-latest"
    EVALUATOR_MODEL = "mistral-large-latest"

    MAX_TOKENS = 2000
    TEMPERATURE = 0.7

    MAX_QUESTIONS = 10
    MIN_QUESTIONS = 5

    LOG_FORMAT = "json"

    @classmethod
    def validate(cls):
        if not cls.MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY is not set. Please set it in .env file")