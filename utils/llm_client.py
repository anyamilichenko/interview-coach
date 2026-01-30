from mistralai import Mistral
from typing import List, Dict, Any
import json
from config import Config


class MistralClient:
    def __init__(self):
        self.client = Mistral(api_key=Config.MISTRAL_API_KEY)
        self.models = {
            "interviewer": Config.INTERVIEWER_MODEL,
            "observer": Config.OBSERVER_MODEL,
            "evaluator": Config.EVALUATOR_MODEL
        }

    def generate_response(self, agent_type: str, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.client.chat.complete(
                model=self.models[agent_type],
                messages=messages,
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling Mistral API: {e}")
            return ""

    def generate_structured_response(self, agent_type: str, messages: List[Dict[str, str]],
                                     response_format: Dict[str, Any] = None) -> Dict[str, Any]:
        if response_format:
            messages.append({
                "role": "system",
                "content": f"Respond in JSON format: {json.dumps(response_format)}"
            })

        response = self.generate_response(agent_type, messages)

        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except:
            pass

        return {"response": response}