# AI_Domain_Agnostic_Crawler

A sophisticated web crawler that uses AI to extract, normalize, and segment structured data from any public website using Schema.org ontologies. The system adapts dynamically across industries using semantic similarity and LLM reasoning.

## Features

- **Domain-Agnostic**: Automatically adapts to any industry (Banking, E-Commerce, Insurance, etc.)
- **AI-Powered**: Uses LLM + Sentence Transformers for intelligent schema mapping
- **Schema.org Compliance**: Normalizes data according to Schema.org standards
- **Vector Search**: Semantic similarity search using Qdrant
- **Structured Storage**: PostgreSQL for relational data, Qdrant for vector embeddings
- **REST API**: FastAPI-based API with JSON-LD output
- **Industry Classification**: Automatic industry detection using semantic similarity
- **RAG Pipeline**: Retrieval-Augmented Generation for intelligent Q&A based on crawled data

## Tech Stack

- **Crawler**: Crawl4AI, BeautifulSoup
- **AI Layer**: OpenAI GPT-4o-mini / Groq (Llama 4), Sentence Transformers
- **LLM Support**: Automatic fallback from OpenAI to Groq if OpenAI fails
- **Schema**: Schema.org ontologies
- **Storage**: PostgreSQL, Qdrant (Vector DB)
- **API**: FastAPI, Uvicorn
- **Output**: JSON-LD format

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL (cloud or local)
- Qdrant (cloud or local via Docker)

### Setup

1. **Clone the repository** (if applicable) or navigate to the project directory:
```bash
cd AI_Domain_Agnostic_Crawler
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Set up environment variables**:
```bash
cp env_template.txt .env
# Edit .env with your configuration
# For local PostgreSQL, use individual parameters:
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=your_password
# POSTGRES_DATABASE=crawler_db
```

5. **Verify setup**:
```bash
# Test the API server
curl http://localhost:8000/health
```

## Configuration

Edit `.env` file with your settings:

```env
# OpenAI API Key (primary)
OPENAI_API_KEY=your_openai_api_key_here

# Groq API Key (fallback if OpenAI fails)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=meta-llama/llama-4-maverick-17b-128e-instruct
LLM_PROVIDER=auto  # auto, openai, or groq

# PostgreSQL Configuration
# Use full connection URL (recommended):
POSTGRES_URL=postgresql://user:password@host:port/database

# Or use individual parameters:
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=your_password
# POSTGRES_DATABASE=crawler_db

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=crawler_vectors

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## Usage

### Start the API Server

**Option 1: Using the run script** (recommended):
```bash
./run.sh
```

**Option 2: Direct Python execution**:
```bash
python main.py
```

**Option 3: Using uvicorn directly**:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Crawl a URL

```bash
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.hdfcbank.com/personal/pay/cards/millennia-cards/millennia-cc-new",
    "force_refresh": false
  }'
```

**Response:**
```json
{
  "success": true,
  "url": "https://www.hdfcbank.com/...",
  "page_id": "uuid-here",
  "industry": "banking",
  "schema_type": "FinancialProduct",
  "extracted_data": {
    "@type": "FinancialProduct",
    "@context": "https://schema.org",
    "name": "Millennia Credit Card",
    "brand": "HDFC Bank",
    "annualFee": 1000,
    "rewards": "5% Cashback on Online Shopping",
    "audience": "Retail"
  },
  "jsonld": { ... }
}
```

#### 2. Get Crawled Data

```bash
curl "http://localhost:8000/crawl/https://www.hdfcbank.com/..."
```

#### 3. Semantic Search

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "credit card with cashback rewards",
    "limit": 10
  }'
```

#### 4. Get by Industry

```bash
curl "http://localhost:8000/industry/banking?limit=50"
```

#### 5. RAG Query (Ask Questions)

```bash
curl -X POST "http://localhost:8000/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the best credit cards with cashback rewards?",
    "industry": "banking",
    "include_sources": true
  }'
```

**Response:**
```json
{
  "answer": "Based on the crawled data, here are the best credit cards...",
  "query": "What are the best credit cards with cashback rewards?",
  "sources": [
    {
      "url": "https://www.hdfcbank.com/...",
      "title": "Millennia Credit Card",
      "industry": "banking",
      "similarity_score": 0.85
    }
  ],
  "sources_count": 3,
  "model": "gpt-4o-mini"
}
```

#### 6. RAG Compare Products

```bash
curl -X POST "http://localhost:8000/rag/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare credit cards by annual fee and rewards",
    "industry": "banking"
  }'
```

#### 7. Health Check

```bash
curl "http://localhost:8000/health"
```

## Example Use Cases

### Banking (HDFC Credit Card)
```bash
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.hdfcbank.com/personal/pay/cards/millennia-cards/millennia-cc-new"}'
```

**Expected Output:**
- Industry: `banking`
- Schema Type: `FinancialProduct`
- Fields: `name`, `brand`, `annualFee`, `rewards`, `interestRate`, etc.

### E-Commerce (Reliance Digital)
```bash
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.reliancedigital.in/product/samsung-s24-ultra-5g-256-gb-12-gb-ram-titanium-black-mobile-phone-lrud04-7536178"}'
```

**Expected Output:**
- Industry: `ecommerce`
- Schema Type: `Product`
- Fields: `name`, `brand`, `price`, `aggregateRating`, `reviewCount`, etc.

### Insurance (Tata AIG)
```bash
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.tataaig.com/motor-insurance"}'
```

**Expected Output:**
- Industry: `insurance`
- Schema Type: `Service` or `InsuranceAgency`
- Fields: `name`, `coverage`, `priceCurrency`, `policyTerm`, etc.

## Architecture

```
┌─────────────┐
│   FastAPI   │
│   (main.py) │
└──────┬──────┘
       │
       ├───► WebCrawler (crawler.py)
       │     └───► Crawl4AI + BeautifulSoup
       │
       ├───► SchemaMapper (schema_mapper.py)
       │     ├───► LLMClient (llm_client.py)
       │     │     ├───► OpenAI (primary)
       │     │     └───► Groq (fallback)
       │     └───► Sentence Transformers (classification)
       │
       ├───► StorageManager (storage.py)
       │     ├───► PostgreSQL (structured data)
       │     └───► Qdrant (vector embeddings)
       │
       └───► RAGPipeline (rag.py)
             ├───► Vector Retrieval (Qdrant)
             └───► LLMClient (OpenAI/Groq with fallback)
```

## How It Works

1. **Crawling**: Uses Crawl4AI to fetch and parse web pages
2. **Industry Classification**: Sentence Transformers analyze content to classify industry
3. **Schema Detection**: Semantic similarity matches content to appropriate Schema.org type
4. **Data Extraction**: LLM extracts structured data according to detected schema
5. **Normalization**: Data is normalized to JSON-LD format
6. **Storage**: 
   - PostgreSQL stores structured data and metadata
   - Qdrant stores vector embeddings for semantic search
7. **RAG Pipeline**:
   - User query is embedded using Sentence Transformers
   - Vector search retrieves relevant crawled pages from Qdrant
   - Retrieved context is formatted and sent to LLM
   - LLM generates answer based on retrieved context

## Schema.org Types Supported

- **Product**: General products
- **FinancialProduct**: Banking products (cards, loans)
- **Service**: Services offered
- **Offer**: Offers and promotions
- **Review**: Customer reviews
- **AggregateRating**: Ratings and reviews
- **Organization**: Company information
- **InsuranceAgency**: Insurance products

## Development

### Project Structure

```
AI_Domain_Agnostic_Crawler/
├── main.py              # FastAPI application
├── crawler.py           # Web crawler module
├── schema_mapper.py     # AI schema mapping
├── rag.py               # RAG pipeline for Q&A
├── llm_client.py        # Unified LLM client (OpenAI + Groq)
├── storage.py           # PostgreSQL + Qdrant storage
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── env_template.txt     # Environment template
└── README.md            # This file
```

### Running Tests

```bash
# Test individual components
python -c "from crawler import WebCrawler; import asyncio; asyncio.run(WebCrawler('test').crawl('https://example.com'))"
```

## Limitations & Future Enhancements

- **Rate Limiting**: Add rate limiting for API endpoints
- **Caching**: Implement Redis caching for frequently accessed URLs
- **Batch Processing**: Support batch URL crawling
- **Webhook Support**: Notify on crawl completion
- **Advanced Schema Detection**: Support more Schema.org types
- **Multi-language**: Support non-English content
- **Robots.txt**: Respect robots.txt rules

## License

This project is provided as-is for educational and development purposes.

## Support

For issues or questions, please refer to the project documentation or create an issue in the repository.

