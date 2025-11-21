from typing import Protocol, Union, Awaitable, TypedDict, Optional, runtime_checkable, Literal

class ScrapeResult(TypedDict, total=False):
    scraper: Literal[
        # Apify
        "apify_api",

        # Crawl4AIs
        "crawl4ai_scraper",

        # Firecrawl
        "firecrawl_api",

        # Exa
        "exa_api",

        # Playwright
        "playwright_scraper",

        # Puppeteer
        "puppeteer_scraper",

        # Rest
        "rest_scraper",

        # ScraperAPI
        "scraperapi_api",

        # ScrapingBee
        "scrapingbee_api",

        # Scrapy
        "scrapy_scraper",

        # Selenium
        "selenium_scraper",

        # Tavily
        "tavily_api",

        # Oxylabs AI Scraper
        "oxylabs_ai_scraper",

        # Zyte
        "zyte_api",
    ]
    run_id: str
    url: str
    status_code: int
    error: Optional[str]
    created_at: str
    format: Literal["markdown", "text", "html"]
    content_size: int
    content: Optional[str]

@runtime_checkable
class Scraper(Protocol):
    def scrape(self, url: str, run_id: str) -> Union[ScrapeResult, Awaitable[ScrapeResult]]:
        ...
    def check_environment(self) -> bool:
        """Return True if environment is ready, False or raise Exception if not. Default: always ready."""
        return True
