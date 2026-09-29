import os
import json
import ast

class LLMFusionLayer:
    def __init__(self, enabled=False, api_key=None, vignettes_path=None):
        self.enabled = enabled
        self.api_key = api_key
        
        if vignettes_path is None:
            vignettes_path = os.path.join(os.path.dirname(__file__), "calibration_vignettes.json")
            
        self.few_shot_examples = []
        if os.path.exists(vignettes_path):
            with open(vignettes_path, "r", encoding="utf-8") as f:
                self.few_shot_examples = json.load(f)

    def _build_prompt(self, transcript: str, scores: dict, matched_evidence: dict) -> str:
        prompt = "You are a crisis helpline AI acting as an independent assessor.\n\n"
        prompt += "Current extracted evidence (lexical and semantic):\n"
        prompt += json.dumps(scores, indent=2) + "\n\n"
        prompt += "Detailed evidence:\n"
        prompt += json.dumps(matched_evidence, indent=2) + "\n\n"
        prompt += "Based on this evidence and the transcript, provide an independent assessment of scores (0.0 to 1.0) and a brief justification.\n"
        prompt += "Output MUST be a JSON object strictly in this format:\n"
        prompt += "{\n  \"adjusted_scores\": {\"self_harm_risk\": 0.9, ...},\n  \"justification\": \"string explaining the assessment\"\n}\n\n"
        prompt += f"Transcript to review:\n{transcript}\n"
        return prompt

    def fuse(self, transcript: str, rules_scores: dict, matched_evidence: dict) -> tuple[dict, str]:
        if not self.enabled:
            return rules_scores, ""
            
        if not self.api_key:
            return rules_scores, ""
            
        prompt = self._build_prompt(transcript, rules_scores, matched_evidence)
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a crisis helpline AI Escalation Reviewer. Output ONLY valid JSON with 'adjusted_scores' and 'justification' fields. No markdown formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            llm_result = ast.literal_eval(content)
            
            adjusted_scores = llm_result.get("adjusted_scores", rules_scores)
            justification = llm_result.get("justification", "LLM escalation applied.")
            
            # Ensure all dims exist
            for dim in rules_scores:
                if dim not in adjusted_scores:
                    adjusted_scores[dim] = rules_scores[dim]
                    
            return adjusted_scores, justification
            
        except Exception as e:
            print(f"LLM Fusion failed: {e}")
            return rules_scores, f"Failed to escalate: {e}"
