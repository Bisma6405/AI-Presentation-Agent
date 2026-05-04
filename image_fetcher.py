import os
import requests
from typing import Optional
from pathlib import Path


class ImageFetcher:
    def __init__(self):
        self.temp_dir = Path("temp_images")
        self.temp_dir.mkdir(exist_ok=True)
        self.unsplash_api_key = os.getenv("UNSPLASH_ACCESS_KEY")

    def fetch_image(self, query: str) -> Optional[str]:
        """
        Fetch image from Unsplash API or return None if not available.
        Returns local file path if successful.
        """
        if not query:
            return None

        # Try Unsplash API first if key exists
        if self.unsplash_api_key:
            try:
                return self._fetch_from_unsplash(query)
            except Exception as e:
                print(f"⚠️ Unsplash API failed: {e}, using fallback...")

        # Fallback: Create a placeholder
        return self._create_placeholder(query)

    def _fetch_from_unsplash(self, query: str) -> Optional[str]:
        """Fetch image from Unsplash API"""
        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": query,
            "per_page": 1,
            "orientation": "landscape"
        }
        headers = {
            "Authorization": f"Client-ID {self.unsplash_api_key}"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data["results"]:
            image_url = data["results"][0]["urls"]["regular"]
            return self._download_image(image_url, query)

        return None

    def _download_image(self, url: str, query: str) -> Optional[str]:
        """Download image from URL to local temp directory"""
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            # Clean query for filename
            filename = "".join(c for c in query if c.isalnum() or c in (" ", "-", "_")).strip()
            filename = filename.replace(" ", "_")[:50]
            filepath = self.temp_dir / f"{filename}.jpg"

            with open(filepath, "wb") as f:
                f.write(response.content)

            return str(filepath)
        except Exception as e:
            print(f"⚠️ Error downloading image: {e}")
            return None

    def _create_placeholder(self, query: str) -> Optional[str]:
        """Create a simple placeholder image (fallback)"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create image
            img = Image.new('RGB', (800, 600), color='#3b82f6')
            d = ImageDraw.Draw(img)

            # Add text
            text = query[:40]
            d.text((400, 300), text, fill='white', anchor="mm",
                   font=ImageFont.load_default())

            filepath = self.temp_dir / f"placeholder_{len(list(self.temp_dir.glob('*')))}.jpg"
            img.save(filepath)
            return str(filepath)
        except Exception as e:
            print(f"⚠️ Could not create placeholder: {e}")
            return None