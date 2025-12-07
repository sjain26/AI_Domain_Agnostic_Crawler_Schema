"""RAG (Retrieval-Augmented Generation) module for intelligent query answering."""
from typing import List, Dict, Any, Optional
from storage import StorageManager
from llm_client import LLMClient
import json


class RAGPipeline:
    
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        groq_model: str = "meta-llama/llama-4-maverick-17b-128e-instruct",
        storage_manager: Optional[StorageManager] = None,
        llm_provider: str = "auto",
        max_context_items: int = 5
    ):
        """Initialize RAG pipeline."""
        self.llm_client = LLMClient(
            openai_api_key=openai_api_key,
            groq_api_key=groq_api_key,
            groq_model=groq_model,
            provider=llm_provider
        )
        self.storage = storage_manager
        self.max_context_items = max_context_items
    
    def retrieve_context(self, query: str, industry: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant context from vector database."""
        # Use vector search to find similar content
        results = self.storage.search_similar(query, limit=self.max_context_items)
        
        # Filter by industry if specified
        if industry:
            results = [r for r in results if r.get("industry") == industry]
        
        return results
    
    def format_context(self, retrieved_items: List[Dict[str, Any]]) -> str:
        """Format retrieved items into context string for LLM."""
        context_parts = []
        
        for i, item in enumerate(retrieved_items, 1):
            extracted_data = item.get("extracted_data", {})
            metadata = item.get("metadata", {})
            
            context_item = f"\n[Document {i}]\n"
            context_item += f"URL: {item.get('url', 'N/A')}\n"
            context_item += f"Title: {metadata.get('title', 'N/A')}\n"
            context_item += f"Industry: {item.get('industry', 'N/A')}\n"
            context_item += f"Schema Type: {item.get('schema_type', 'N/A')}\n"
            
            # Add extracted structured data
            if extracted_data:
                context_item += "Data:\n"
                for key, value in extracted_data.items():
                    if key not in ["@type", "@context", "@id"] and value:
                        context_item += f"  - {key}: {value}\n"
            
            context_parts.append(context_item)
        
        return "\n".join(context_parts)
    
    def generate_answer(
        self,
        query: str,
        context: str,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """Generate answer using LLM with retrieved context."""
        
        system_prompt = """You are an intelligent assistant that answers questions based on the provided context from crawled web pages.
The context contains structured data extracted from various websites using Schema.org schemas.
Answer the user's question accurately using only the information provided in the context.
If the context doesn't contain enough information, say so clearly.
Always cite sources when providing specific information."""
        
        user_prompt = f"""Context from crawled web pages:
{context}

Question: {query}

Please provide a comprehensive answer based on the context above. If you reference specific information, mention which document it came from."""
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            answer = self.llm_client.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=1500
            )
            
            result = {
                "answer": answer,
                "query": query,
                "model": self.llm_client.get_provider()
            }
            
            if include_sources:
                result["sources_count"] = len(context.split("[Document"))
                result["context_length"] = len(context)
            
            return result
            
        except Exception as e:
            return {
                "answer": f"Error generating answer: {str(e)}",
                "query": query,
                "error": str(e)
            }
    
    def query(
        self,
        query: str,
        industry: Optional[str] = None,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """Complete RAG pipeline: retrieve + generate."""
        # Step 1: Retrieve relevant context
        retrieved_items = self.retrieve_context(query, industry)
        
        if not retrieved_items:
            return {
                "answer": "No relevant information found in the crawled data.",
                "query": query,
                "sources": [],
                "sources_count": 0
            }
        
        # Step 2: Format context
        context = self.format_context(retrieved_items)
        
        # Step 3: Generate answer
        result = self.generate_answer(query, context, include_sources)
        
        # Step 4: Add source information
        if include_sources:
            result["sources"] = [
                {
                    "url": item.get("url"),
                    "title": item.get("metadata", {}).get("title"),
                    "industry": item.get("industry"),
                    "schema_type": item.get("schema_type"),
                    "similarity_score": item.get("similarity_score")
                }
                for item in retrieved_items
            ]
            result["sources_count"] = len(retrieved_items)
        
        return result
    
    def compare_products(
        self,
        query: str,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare multiple products/services based on query."""
        retrieved_items = self.retrieve_context(query, industry)
        
        if len(retrieved_items) < 2:
            return {
                "answer": "Need at least 2 items to compare. Found fewer items in database.",
                "query": query,
                "items_found": len(retrieved_items)
            }
        
        # Format comparison context
        comparison_context = "Compare the following items:\n\n"
        for i, item in enumerate(retrieved_items[:5], 1):  # Limit to 5 for comparison
            extracted_data = item.get("extracted_data", {})
            metadata = item.get("metadata", {})
            
            comparison_context += f"Item {i}: {metadata.get('title', 'N/A')}\n"
            comparison_context += f"URL: {item.get('url')}\n"
            comparison_context += f"Data: {json.dumps(extracted_data, indent=2)}\n\n"
        
        system_prompt = """You are a comparison expert. Compare the provided items based on the user's query.
Highlight similarities, differences, advantages, and disadvantages.
Present the comparison in a clear, structured format."""
        
        user_prompt = f"""{comparison_context}

User Query: {query}

Provide a detailed comparison of the items above."""
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            answer = self.llm_client.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )
            
            return {
                "answer": answer,
                "query": query,
                "items_compared": len(retrieved_items[:5]),
                "sources": [
                    {
                        "url": item.get("url"),
                        "title": item.get("metadata", {}).get("title")
                    }
                    for item in retrieved_items[:5]
                ]
            }
            
        except Exception as e:
            return {
                "answer": f"Error generating comparison: {str(e)}",
                "query": query,
                "error": str(e)
            }

