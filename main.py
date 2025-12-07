"""Main FastAPI application for the web crawler."""
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import uvicorn

from crawler import WebCrawler
from schema_mapper import SchemaMapper
from storage import StorageManager
from rag import RAGPipeline
from config import settings


app = FastAPI(
    title="AI_Domain_Agnostic_Crawler",
    description="Extract, normalize, and segment structured data from any website using Schema.org",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
crawler = WebCrawler(
    user_agent=settings.crawler_user_agent,
    timeout=settings.crawler_timeout
)

schema_mapper = SchemaMapper(
    openai_api_key=settings.openai_api_key,
    groq_api_key=settings.groq_api_key,
    groq_model=settings.groq_model,
    embedding_model=settings.embedding_model,
    llm_provider=settings.llm_provider
)

storage = StorageManager(
    postgres_config={
        "host": settings.postgres_host,
        "port": settings.postgres_port,
        "user": settings.postgres_user,
        "password": settings.postgres_password,
        "database": settings.postgres_database,
        "url": settings.postgres_url
    },
    qdrant_config={
        "host": settings.qdrant_host,
        "port": settings.qdrant_port,
        "url": settings.qdrant_url,
        "api_key": settings.qdrant_api_key,
        "collection_name": settings.qdrant_collection_name
    },
    embedding_model=settings.embedding_model
)

# Initialize RAG pipeline
rag_pipeline = RAGPipeline(
    openai_api_key=settings.openai_api_key,
    groq_api_key=settings.groq_api_key,
    groq_model=settings.groq_model,
    storage_manager=storage,
    llm_provider=settings.llm_provider
)


# Request/Response Models
class CrawlRequest(BaseModel):
    url: HttpUrl
    force_refresh: Optional[bool] = False


class CrawlResponse(BaseModel):
    success: bool
    url: str
    page_id: Optional[str] = None
    industry: Optional[str] = None
    schema_type: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    jsonld: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    count: int


class RAGRequest(BaseModel):
    query: str
    industry: Optional[str] = None
    include_sources: Optional[bool] = True


class RAGResponse(BaseModel):
    answer: str
    query: str
    sources: Optional[List[Dict[str, Any]]] = None
    sources_count: Optional[int] = None
    model: Optional[str] = None


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI_Domain_Agnostic_Crawler API",
        "version": "1.0.0",
        "endpoints": {
            "POST /crawl": "Crawl and extract data from a URL",
            "GET /crawl/{url}": "Get crawled data by URL",
            "POST /search": "Search for similar content",
            "GET /industry/{industry}": "Get all pages by industry",
            "POST /rag/query": "RAG: Ask questions based on crawled data",
            "POST /rag/compare": "RAG: Compare products/services",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/crawl", response_model=CrawlResponse)
async def crawl_url(request: CrawlRequest, background_tasks: BackgroundTasks):
    """Crawl a URL and extract structured data."""
    url = str(request.url)
    
    # Check if already crawled (unless force refresh)
    if not request.force_refresh:
        existing = storage.get_by_url(url)
        if existing:
            return CrawlResponse(
                success=True,
                url=url,
                page_id=existing["id"],
                industry=existing["industry"],
                schema_type=existing["schema_type"],
                extracted_data=existing["extracted_data"],
                jsonld=existing["extracted_data"]
            )
    
    # Crawl the URL
    crawl_result = await crawler.crawl(url)
    
    if not crawl_result["success"]:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to crawl URL: {crawl_result.get('error', 'Unknown error')}"
        )
    
    # Classify industry
    text_content = crawl_result.get("text", "")
    industry = schema_mapper.classify_industry(text_content)
    
    # Detect schema type
    schema_type = schema_mapper.detect_schema_type(text_content, industry)
    
    # Extract structured data using LLM
    extracted_data = schema_mapper.extract_with_llm(
        crawl_result.get("html", ""),
        text_content,
        schema_type
    )
    
    # Normalize to JSON-LD
    jsonld = schema_mapper.normalize_to_jsonld(extracted_data, url)
    
    # Save to storage
    metadata = crawl_result.get("metadata", {})
    page_id = storage.save_crawled_data(
        url=url,
        title=metadata.get("title", ""),
        description=metadata.get("description", ""),
        industry=industry,
        schema_type=schema_type,
        extracted_data=extracted_data,
        metadata=metadata,
        text_content=text_content
    )
    
    return CrawlResponse(
        success=True,
        url=url,
        page_id=page_id,
        industry=industry,
        schema_type=schema_type,
        extracted_data=extracted_data,
        jsonld=jsonld
    )


@app.get("/crawl/{url:path}", response_model=CrawlResponse)
async def get_crawled_data(url: str):
    """Get previously crawled data by URL."""
    # Decode URL if needed
    import urllib.parse
    url = urllib.parse.unquote(url)
    
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    data = storage.get_by_url(url)
    
    if not data:
        raise HTTPException(status_code=404, detail="URL not found in database")
    
    return CrawlResponse(
        success=True,
        url=url,
        page_id=data["id"],
        industry=data["industry"],
        schema_type=data["schema_type"],
        extracted_data=data["extracted_data"],
        jsonld=data["extracted_data"]
    )


@app.post("/search", response_model=SearchResponse)
async def search_similar(request: SearchRequest):
    """Search for similar content using semantic similarity."""
    results = storage.search_similar(request.query, request.limit)
    
    return SearchResponse(
        results=results,
        count=len(results)
    )


@app.get("/industry/{industry}")
async def get_by_industry(industry: str, limit: int = 100):
    """Get all crawled pages by industry."""
    results = storage.get_by_industry(industry, limit)
    
    return {
        "industry": industry,
        "count": len(results),
        "results": results
    }


@app.get("/stats")
async def get_stats():
    """Get crawling statistics."""
    # This would require additional MySQL queries
    return {
        "message": "Statistics endpoint - implement as needed"
    }


@app.post("/rag/query", response_model=RAGResponse)
async def rag_query(request: RAGRequest):
    """RAG endpoint: Ask questions and get answers based on crawled data.
    
    - query: Required - Your question
    - industry: Optional - Filter by industry (banking, ecommerce, insurance, etc.)
    - include_sources: Optional - Include source URLs in response (default: true)
    
    If industry is not provided, searches across all industries.
    """
    result = rag_pipeline.query(
        query=request.query,
        industry=request.industry,
        include_sources=request.include_sources
    )
    
    return RAGResponse(
        answer=result.get("answer", ""),
        query=result.get("query", request.query),
        sources=result.get("sources", []),
        sources_count=result.get("sources_count", 0),
        model=result.get("model")
    )


@app.post("/rag/compare")
async def rag_compare(request: RAGRequest):
    """RAG endpoint: Compare multiple products/services.
    
    - query: Required - Your comparison query
    - industry: Optional - Filter by industry (banking, ecommerce, insurance, etc.)
    
    If industry is not provided, searches across all industries.
    Needs at least 2 items to compare.
    """
    result = rag_pipeline.compare_products(
        query=request.query,
        industry=request.industry
    )
    
    return result


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

