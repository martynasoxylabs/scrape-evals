import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from oxylabs_ai_studio.apps.ai_scraper import AiScraper

from .base import Scraper, ScrapeResult

load_dotenv()

class OxylabsAiScraper(Scraper):
    """Scrapes web pages using the Oxylabs AI Scraper asynchronously."""

    def __init__(self):
        self.api_key = os.getenv("OXYLABS_AI_STUDIO_API_KEY")
        if not self.api_key:
            raise ValueError("OXYLABS_AI_STUDIO_API_KEY not set in environment.")
        self.scraper = AiScraper(api_key=self.api_key)

    async def scrape(self, url: str, run_id: str) -> ScrapeResult:
        try:
            result = await self.scraper.scrape_async(
                url=url,
                output_format="markdown",
                render_javascript=False,
            )

            # Extract content from result.data
            content: Optional[str] = None
            
            if isinstance(result.data, str):
                content = result.data
            elif isinstance(result.data, dict):
                # Fallback if it returns a dict
                content = result.data.get("content") or result.data.get("markdown") or str(result.data)
            
            content_size = len(content.encode("utf-8")) if content else 0
            
            return ScrapeResult(
                run_id=run_id,
                scraper="oxylabs_ai_scraper",
                url=url,
                status_code=200,  # Assumed success if no exception raised
                error=result.message if result.message and not content else None,
                content_size=content_size,
                format="markdown",
                created_at=datetime.now().isoformat(),
                content=content,
            )

        except Exception as e:
            return ScrapeResult(
                run_id=run_id,
                scraper="oxylabs_ai_scraper",
                url=url,
                status_code=500,
                error=str(e),
                content_size=0,
                format="markdown",
                created_at=datetime.now().isoformat(),
                content=None,
            )
