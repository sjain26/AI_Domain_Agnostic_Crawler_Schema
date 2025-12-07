"""Storage layer for PostgreSQL and Qdrant."""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import uuid


class StorageManager:
    
    
    def __init__(
        self,
        postgres_config: Dict[str, Any],
        qdrant_config: Dict[str, Any],
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """Initialize storage manager."""
        self.postgres_config = postgres_config
        self.qdrant_config = qdrant_config
        self.embedding_model = SentenceTransformer(embedding_model)
        self.qdrant_client = None
        self._init_qdrant()
        self._init_postgres()
    
    def _get_connection(self):
        """Get PostgreSQL connection."""
        if self.postgres_config.get("url"):
            # Use connection URL
            return psycopg2.connect(self.postgres_config["url"])
        else:
            # Use individual parameters
            return psycopg2.connect(
                host=self.postgres_config.get("host", "localhost"),
                port=self.postgres_config.get("port", 5432),
                user=self.postgres_config.get("user", "postgres"),
                password=self.postgres_config.get("password", ""),
                database=self.postgres_config.get("database", "crawler_db")
            )
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection and create tables."""
        try:
            conn = self._get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crawled_pages (
                    id VARCHAR(36) PRIMARY KEY,
                    url VARCHAR(2048) UNIQUE NOT NULL,
                    title TEXT,
                    description TEXT,
                    industry VARCHAR(100),
                    schema_type VARCHAR(100),
                    extracted_data JSONB,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_url ON crawled_pages(url)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_industry ON crawled_pages(industry)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_schema_type ON crawled_pages(schema_type)
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crawl_history (
                    id SERIAL PRIMARY KEY,
                    page_id VARCHAR(36),
                    url VARCHAR(2048),
                    status VARCHAR(50),
                    error_message TEXT,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (page_id) REFERENCES crawled_pages(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_crawled_at ON crawl_history(crawled_at)
            """)
            
            cursor.close()
            conn.close()
            
            print("✅ PostgreSQL tables initialized")
            
        except Exception as e:
            print(f"❌ PostgreSQL initialization error: {e}")
            raise
    
    def _init_qdrant(self):
        """Initialize Qdrant client and collection."""
        try:
            # Use cloud Qdrant if URL and API key are provided
            if self.qdrant_config.get("url") and self.qdrant_config.get("api_key"):
                print("🌐 Using Cloud Qdrant")
                self.qdrant_client = QdrantClient(
                    url=self.qdrant_config["url"],
                    api_key=self.qdrant_config["api_key"]
                )
            else:
                # Use local Qdrant
                print("🏠 Using Local Qdrant")
                self.qdrant_client = QdrantClient(
                    host=self.qdrant_config.get("host", "localhost"),
                    port=self.qdrant_config.get("port", 6333)
                )
            
            # Test connection
            collections = self.qdrant_client.get_collections()
            print(f"✅ Qdrant connected. Collections: {[c.name for c in collections.collections]}")
            
            # Create collection if not exists
            collection_names = [c.name for c in collections.collections]
            
            if self.qdrant_config["collection_name"] not in collection_names:
                print(f"📦 Creating collection: {self.qdrant_config['collection_name']}")
                self.qdrant_client.create_collection(
                    collection_name=self.qdrant_config["collection_name"],
                    vectors_config=VectorParams(
                        size=384,  # all-MiniLM-L6-v2 dimension
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Collection created: {self.qdrant_config['collection_name']}")
            else:
                print(f"✅ Collection exists: {self.qdrant_config['collection_name']}")
                
        except Exception as e:
            print(f"❌ Qdrant initialization error: {e}")
            raise
    
    def save_crawled_data(
        self,
        url: str,
        title: str,
        description: str,
        industry: str,
        schema_type: str,
        extracted_data: Dict[str, Any],
        metadata: Dict[str, Any],
        text_content: str
    ) -> str:
        """Save crawled data to PostgreSQL and Qdrant."""
        page_id = str(uuid.uuid4())
        
        # Save to PostgreSQL
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO crawled_pages 
                (id, url, title, description, industry, schema_type, extracted_data, metadata, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (url) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    industry = EXCLUDED.industry,
                    schema_type = EXCLUDED.schema_type,
                    extracted_data = EXCLUDED.extracted_data,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                page_id,
                url,
                title,
                description,
                industry,
                schema_type,
                json.dumps(extracted_data),
                json.dumps(metadata)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ PostgreSQL save error: {e}")
            return None
        
        # Save to Qdrant for vector search
        try:
            # Create embedding from text content
            embedding = self.embedding_model.encode(text_content[:1000]).tolist()
            
            payload = {
                "url": url,
                "title": title,
                "industry": industry,
                "schema_type": schema_type,
                "page_id": page_id
            }
            
            self.qdrant_client.upsert(
                collection_name=self.qdrant_config["collection_name"],
                points=[
                    PointStruct(
                        id=hash(url) % (2**63),  # Use hash of URL as ID
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
        except Exception as e:
            print(f"❌ Qdrant save error: {e}")
        
        return page_id
    
    def get_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve data by URL."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM crawled_pages WHERE url = %s
            """, (url,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                result = dict(result)
                result["extracted_data"] = json.loads(result["extracted_data"]) if isinstance(result["extracted_data"], str) else result["extracted_data"]
                result["metadata"] = json.loads(result["metadata"]) if isinstance(result["metadata"], str) else result["metadata"]
            
            return result
            
        except Exception as e:
            print(f"❌ PostgreSQL get error: {e}")
            return None
    
    def search_similar(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar content using vector similarity."""
        try:
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Use query_points method (correct Qdrant API)
            query_response = self.qdrant_client.query_points(
                collection_name=self.qdrant_config["collection_name"],
                query=query_embedding,
                limit=limit
            )
            
            # Fetch full data from PostgreSQL
            similar_pages = []
            for point in query_response.points:
                url = point.payload.get("url")
                if url:
                    page_data = self.get_by_url(url)
                    if page_data:
                        page_data["similarity_score"] = point.score
                        similar_pages.append(page_data)
            
            return similar_pages
            
        except Exception as e:
            print(f"❌ Vector search error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_by_industry(self, industry: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all pages by industry."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM crawled_pages 
                WHERE industry = %s 
                ORDER BY updated_at DESC 
                LIMIT %s
            """, (industry, limit))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            formatted_results = []
            for result in results:
                result_dict = dict(result)
                result_dict["extracted_data"] = json.loads(result_dict["extracted_data"]) if isinstance(result_dict["extracted_data"], str) else result_dict["extracted_data"]
                result_dict["metadata"] = json.loads(result_dict["metadata"]) if isinstance(result_dict["metadata"], str) else result_dict["metadata"]
                formatted_results.append(result_dict)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ PostgreSQL get by industry error: {e}")
            return []
