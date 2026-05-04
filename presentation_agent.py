import json
from typing import Optional, Dict
from groq_client import GroqClient
from slide_generator import SlideGenerator
from image_fetcher import ImageFetcher


class PresentationAgent:
    def __init__(self):
        self.groq_client = GroqClient()
        self.slide_generator = SlideGenerator()
        self.image_fetcher = ImageFetcher()
        self.title: str = ""
        self.outline: list = []
        self.current_slide_index: int = 0
        self.presentation_created: bool = False

    def set_title(self, title: str):
        self.title = title
        print(f"\n✓ Presentation Title: {title}")

    def generate_outline(self) -> list:
        if not self.title:
            raise ValueError("Please set a title first using set_title()")

        print("\n🔄 Generating outline...")
        outline_json = self.groq_client.generate_outline(self.title)

        try:
            # Clean the JSON response
            outline_json = outline_json.strip()
            if outline_json.startswith("```json"):
                outline_json = outline_json[7:]
            if outline_json.endswith("```"):
                outline_json = outline_json[:-3]

            self.outline = json.loads(outline_json.strip())
            print(f"✓ Outline generated with {len(self.outline)} slides")
            self._display_outline()
            return self.outline
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing outline: {e}")
            print(f"Raw response: {outline_json[:500]}")
            raise

    def _display_outline(self):
        print("\n📋 Presentation Outline:")
        print("-" * 50)
        for slide in self.outline:
            print(f"Slide {slide['slide_number']}: {slide['heading']}")
            if slide.get('content'):
                print(f"  → {slide['content'][:100]}...")
        print("-" * 50)

    def create_next_slide(self) -> Optional[Dict]:
        if not self.outline:
            raise ValueError("Please generate outline first using generate_outline()")

        if self.current_slide_index >= len(self.outline):
            print("✓ All slides have been created!")
            return None

        slide_info = self.outline[self.current_slide_index]
        print(f"\n📊 Creating Slide {self.current_slide_index + 1}/{len(self.outline)}")
        print(f"   Heading: {slide_info['heading']}")

        content_json = self.groq_client.generate_slide_content(self.title, slide_info)

        try:
            content_json = content_json.strip()
            if content_json.startswith("```json"):
                content_json = content_json[7:]
            if content_json.endswith("```"):
                content_json = content_json[:-3]
            slide_content = json.loads(content_json.strip())
        except json.JSONDecodeError as e:
            print(f"⚠ Fallback content used due to parse error: {e}")
            slide_content = {
                "heading": slide_info["heading"],
                "bullet_points": ["Content generation error"],
                "image_search_query": slide_info["heading"]
            }

        # Fetch image (now returns local path)
        image_path = None
        if slide_content.get("image_search_query"):
            print("   🖼️ Fetching/Generating image...")
            image_path = self.image_fetcher.fetch_image(slide_content["image_search_query"])

        if slide_info["type"] == "title":
            self.slide_generator.add_title_slide(
                title=slide_content["heading"],
                subtitle=self.title
            )
        else:
            self.slide_generator.add_content_slide(
                heading=slide_content["heading"],
                bullet_points=slide_content.get("bullet_points", []),
                image_path=image_path
            )

        self.current_slide_index += 1
        self.presentation_created = True
        print(f"✓ Slide {self.current_slide_index} created successfully!")
        return slide_content

    def get_remaining_slides(self) -> int:
        return len(self.outline) - self.current_slide_index

    def save_presentation(self, filename: str = None) -> str:
        if not filename:
            filename = self.title.replace(" ", "_")[:50]
        return self.slide_generator.save_to_file(filename)

    def reset(self):
        self.title = ""
        self.outline = []
        self.current_slide_index = 0
        self.presentation_created = False
        self.slide_generator = SlideGenerator()