from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup


@dataclass
class PageContext:
    requested_url: str
    final_url: str
    html: str
    status_code: int
    response_time_ms: float
    has_ssl: bool
    soup: BeautifulSoup

    @property
    def host(self) -> str:
        return urlparse(self.final_url).netloc.lower()

    @property
    def title_text(self) -> str:
        if self.soup.title and self.soup.title.string:
            return self.soup.title.string.strip()
        return ""

    def meta_content(self, name: str) -> str:
        tag = self.soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
        return ""

    def meta_property(self, prop: str) -> str:
        tag = self.soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
        return ""
