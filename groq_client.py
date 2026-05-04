import os
from groq import Groq
from dotenv import load_dotenv
import json

load_dotenv()


class GroqClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables!")

        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def generate_outline(self, title: str) -> str:
        """Generate presentation outline from title"""
        prompt = f"""
        Create a professional presentation outline for the topic: "{title}"

        Provide:
        1. A title slide heading
        2. 5-7 slide titles with brief descriptions
        3. Each slide should have a clear purpose

        Format as JSON array like this:
        [
            {{"slide_number": 1, "type": "title", "heading": "Main Title", "content": ""}},
            {{"slide_number": 2, "type": "content", "heading": "Slide Title", "content": "Brief description of what this slide covers"}}
        ]

        Only return the JSON array, nothing else. No markdown formatting.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000,
                timeout=30
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Groq API error in generate_outline: {str(e)}")

    def generate_slide_content(self, title: str, slide_info: dict) -> str:
        """Generate detailed content for a specific slide"""
        prompt = f"""
        For presentation topic: "{title}"
        Slide: {slide_info.get('heading', '')}
        Description: {slide_info.get('content', '')}

        Generate detailed slide content including:
        1. Main heading (short, impactful)
        2. 3-5 bullet points with key information
        3. A search query for finding a relevant image

        Format as JSON:
        {{
            "heading": "Slide heading",
            "bullet_points": ["point 1", "point 2", "point 3"],
            "image_search_query": "search term for image"
        }}

        Only return the JSON object, nothing else. No markdown formatting.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
                timeout=30
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Groq API error in generate_slide_content: {str(e)}")