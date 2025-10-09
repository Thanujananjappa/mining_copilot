from mistralai import Mistral
from config import Config

class MistralService:
    def __init__(self):
        self.client = Mistral(api_key=Config.MISTRAL_API_KEY)
        self.model = "mistral-small-latest"
    
    def generate_response(self, context, query, max_tokens=150):
        """
        Generate concise 3-4 sentence response
        """
        prompt = f"""You are an expert mining and infrastructure management assistant.
Using the following context, provide a concise answer in 3-4 sentences maximum.
Be specific, actionable, and focus on key insights for managers.

Context:
{context}

Question: {query}

Concise Answer (3-4 sentences):"""

        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
        except Exception as e:
            return f"Error generating response: {str(e)}"