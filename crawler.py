"""Web crawler using Crawl4AI for content extraction."""
import asyncio
from typing import Dict, Optional, Any
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from bs4 import BeautifulSoup
import re


class WebCrawler:
    
    
    def __init__(self, user_agent: str, timeout: int = 30):
        """Initialize the crawler."""
        self.user_agent = user_agent
        self.timeout = timeout
    
    async def crawl(self, url: str) -> Dict[str, Any]:
        """Crawl a URL and extract content."""
        try:
            async with AsyncWebCrawler() as crawler:
                config = CrawlerRunConfig(
                    user_agent=self.user_agent,
                    wait_for="css:body"
                )
                
                result = await crawler.arun(url=url, config=config)
                
                if result.success:
                    # Parse HTML
                    soup = BeautifulSoup(result.html, 'html.parser')
                    
                    # Extract text content
                    text_content = self._extract_text(soup)
                    
                    # Extract metadata
                    metadata = self._extract_metadata(soup, url)
                    
                    # Extract structured data (JSON-LD, microdata, etc.)
                    structured_data = self._extract_structured_data(soup)
                    
                    return {
                        "success": True,
                        "url": url,
                        "html": result.html,
                        "text": text_content,
                        "metadata": metadata,
                        "structured_data": structured_data,
                        "soup": soup
                    }
                else:
                    return {
                        "success": False,
                        "url": url,
                        "error": result.error_message or "Unknown error"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML."""
        # Remove script and style elements
        for script in soup(["script", "style", "meta", "link"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from the page."""
        metadata = {
            "url": url,
            "title": "",
            "description": "",
            "keywords": [],
            "og_title": "",
            "og_description": "",
            "og_image": ""
        }
        
        # Title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()
        
        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            metadata["description"] = meta_desc.get("content", "").strip()
        
        # Keywords
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords:
            keywords = meta_keywords.get("content", "")
            metadata["keywords"] = [k.strip() for k in keywords.split(",")]
        
        # Open Graph
        og_title = soup.find("meta", property="og:title")
        if og_title:
            metadata["og_title"] = og_title.get("content", "").strip()
        
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            metadata["og_description"] = og_desc.get("content", "").strip()
        
        og_image = soup.find("meta", property="og:image")
        if og_image:
            metadata["og_image"] = og_image.get("content", "").strip()
        
        return metadata
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> list:
        """Extract existing structured data (JSON-LD, microdata)."""
        structured_data = []
        
        # Extract JSON-LD
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                structured_data.append(data)
            except:
                pass
        
        # Extract microdata (basic)
        items = soup.find_all(attrs={"itemscope": True})
        for item in items:
            item_data = {}
            item_type = item.get("itemtype", "")
            if item_type:
                item_data["@type"] = item_type.replace("http://schema.org/", "").replace("https://schema.org/", "")
            
            props = item.find_all(attrs={"itemprop": True})
            for prop in props:
                prop_name = prop.get("itemprop")
                prop_value = prop.get("content") or prop.get_text().strip()
                if prop_name and prop_value:
                    item_data[prop_name] = prop_value
            
            if item_data:
                structured_data.append(item_data)
        
        return structured_data

