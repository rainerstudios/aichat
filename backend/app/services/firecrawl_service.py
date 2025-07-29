import httpx
import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

class FirecrawlService:
    """
    Service for crawling documentation with Firecrawl API
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.base_url = "https://api.firecrawl.dev/v1"
        
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable is required")
        
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=30.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    async def crawl_website(self, 
                          url: str, 
                          limit: int = 100, 
                          only_main_content: bool = True,
                          include_subdomains: bool = False) -> List[Dict[str, Any]]:
        """
        Crawl a website and return documents in markdown format
        """
        try:
            # Start crawl job
            crawl_data = {
                "url": url,
                "limit": limit,
                "crawlerOptions": {
                    "onlyMainContent": only_main_content,
                    "includeSubdomains": include_subdomains,
                    "excludes": [
                        "*/search*",
                        "*/login*", 
                        "*/register*",
                        "*/admin*",
                        "*/*.pdf",
                        "*/*.zip"
                    ]
                },
                "scrapeOptions": {
                    "formats": ["markdown"],
                    "onlyMainContent": only_main_content
                }
            }
            
            response = await self.session.post(f"{self.base_url}/crawl", json=crawl_data)
            response.raise_for_status()
            
            job_data = response.json()
            job_id = job_data.get("jobId")
            
            if not job_id:
                raise Exception("No job ID returned from Firecrawl")
            
            print(f"Started Firecrawl job {job_id} for {url}")
            
            # Poll for completion
            return await self._wait_for_crawl_completion(job_id)
            
        except httpx.HTTPError as e:
            raise Exception(f"Firecrawl API error: {e}")
    
    async def _wait_for_crawl_completion(self, job_id: str, max_wait_time: int = 600) -> List[Dict[str, Any]]:
        """
        Wait for crawl job to complete and return results
        """
        start_time = datetime.now()
        
        while True:
            try:
                response = await self.session.get(f"{self.base_url}/crawl/{job_id}")
                response.raise_for_status()
                
                job_data = response.json()
                status = job_data.get("status")
                
                print(f"Crawl job {job_id} status: {status}")
                
                if status == "completed":
                    documents = job_data.get("data", [])
                    print(f"Crawl completed with {len(documents)} documents")
                    return documents
                    
                elif status == "failed":
                    error_msg = job_data.get("error", "Unknown error")
                    raise Exception(f"Crawl job failed: {error_msg}")
                
                # Check timeout
                elapsed = (datetime.now() - start_time).seconds
                if elapsed > max_wait_time:
                    raise Exception(f"Crawl job timed out after {max_wait_time} seconds")
                
                # Wait before next check
                await asyncio.sleep(10)
                
            except httpx.HTTPError as e:
                raise Exception(f"Error checking crawl status: {e}")
    
    async def scrape_single_page(self, url: str, only_main_content: bool = True) -> Dict[str, Any]:
        """
        Scrape a single page and return markdown content
        """
        try:
            scrape_data = {
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": only_main_content
            }
            
            response = await self.session.post(f"{self.base_url}/scrape", json=scrape_data)
            response.raise_for_status()
            
            return response.json().get("data", {})
            
        except httpx.HTTPError as e:
            raise Exception(f"Firecrawl scrape error: {e}")

# Factory function
def create_firecrawl_service() -> FirecrawlService:
    """Create Firecrawl service instance"""
    return FirecrawlService()

# Predefined documentation sources - using single page scraping for reliability
DOCUMENTATION_SOURCES = [
    # Pterodactyl Documentation
    {
        "name": "Pterodactyl Panel Main",
        "url": "https://pterodactyl.io/panel/",
        "scrape_only": True
    },
    {
        "name": "Pterodactyl Panel Installation",
        "url": "https://pterodactyl.io/panel/1.0/getting_started.html",
        "scrape_only": True
    },
    {
        "name": "Pterodactyl Wings",
        "url": "https://pterodactyl.io/wings/",
        "scrape_only": True
    },
    
    # Game Server Documentation
    {
        "name": "Minecraft Server Setup Guide",
        "url": "https://minecraft.wiki/w/Tutorials/Setting_up_a_server",
        "scrape_only": True
    },
    {
        "name": "Paper MC Documentation",
        "url": "https://docs.papermc.io/",
        "scrape_only": True
    },
    {
        "name": "Paper Server Setup",
        "url": "https://docs.papermc.io/paper/getting-started",
        "scrape_only": True
    },
    {
        "name": "Spigot Installation Guide",
        "url": "https://www.spigotmc.org/wiki/spigot-installation/",
        "scrape_only": True
    },
    
    # Arma Reforger
    {
        "name": "Arma Reforger Server Setup",
        "url": "https://community.bistudio.com/wiki/Arma_Reforger:Server_Hosting",
        "scrape_only": True
    },
    
    # Rust Server Documentation
    {
        "name": "Rust Server Setup",
        "url": "https://rust.facepunch.com/blog/server-setup/",
        "scrape_only": True
    },
    
    # Counter-Strike 2
    {
        "name": "CS2 Dedicated Servers",
        "url": "https://developer.valvesoftware.com/wiki/Counter-Strike_2/Dedicated_Servers",
        "scrape_only": True
    },
    
    # Valheim
    {
        "name": "Valheim Dedicated Server",
        "url": "https://valheim.fandom.com/wiki/Valheim_Dedicated_Server",
        "scrape_only": True
    },
    
    # Hosting Provider Knowledge Bases
    {
        "name": "Shockbyte Knowledge Base",
        "url": "https://shockbyte.com/help/knowledgebase",
        "scrape_only": True
    },
    {
        "name": "BisectHosting Knowledge Base", 
        "url": "https://www.bisecthosting.com/clients/index.php?rp=/knowledgebase",
        "scrape_only": True
    },
]

async def crawl_all_documentation_sources() -> List[Dict[str, Any]]:
    """
    Crawl all predefined documentation sources
    """
    all_documents = []
    
    async with create_firecrawl_service() as firecrawl:
        for source in DOCUMENTATION_SOURCES:
            try:
                print(f"Processing {source['name']}: {source['url']}")
                
                # Check if this source should use single page scraping
                if source.get("scrape_only", False):
                    print(f"  Using single page scraping for {source['name']}")
                    doc = await firecrawl.scrape_single_page(source["url"])
                    if doc and doc.get("markdown"):
                        doc["source_name"] = source["name"]
                        doc["crawled_at"] = datetime.now().isoformat()
                        all_documents.append(doc)
                else:
                    print(f"  Using full crawl for {source['name']}")
                    documents = await firecrawl.crawl_website(
                        url=source["url"],
                        limit=source.get("limit", 50)
                    )
                    
                    # Add source metadata
                    for doc in documents:
                        doc["source_name"] = source["name"]
                        doc["crawled_at"] = datetime.now().isoformat()
                    
                    all_documents.extend(documents)
                
                print(f"  ✅ Successfully processed {source['name']}")
                
            except Exception as e:
                print(f"  ❌ Failed to process {source['name']}: {e}")
                continue
    
    return all_documents