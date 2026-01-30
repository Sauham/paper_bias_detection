import os
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class OpenAIBiasAnalyzer:
    def __init__(self):
        self.enabled = bool(OPENAI_API_KEY)
        self.client = OpenAI(api_key=OPENAI_API_KEY) if self.enabled else None

    def analyze_sections(self, sections: dict) -> dict:
        if not self.enabled:
            return {
                "enabled": False,
                "result": {
                    "bias_types": [],
                    "severity": "low",
                    "explanation": "Bias analysis disabled (API key not configured)."
                }
            }

        text = (sections.get("Abstract", "") + "\n" +
                sections.get("Conclusions", ""))[:3000]

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": f"""
    Analyze the following research text for possible academic bias.
    Return JSON with:
    bias_types, severity, explanation.

    Text:
    {text}
    """
                }],
                temperature=0.1,
                max_tokens=200
            )

            return {
                "enabled": True,
                "result": response.choices[0].message.content
            }

        except Exception as e:
            return {
                "enabled": False,
                "result": {
                    "bias_types": [],
                    "severity": "low",
                    "explanation": f"Bias analysis failed: {e}"
                }
            }

