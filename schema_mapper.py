"""AI-driven schema mapping and normalization using Schema.org."""
import json
import re
from typing import Dict, List, Optional, Any
from sentence_transformers import SentenceTransformer
import numpy as np
from llm_client import LLMClient


class SchemaMapper:
    """Maps extracted content to Schema.org schemas using AI."""
    
    # Common Schema.org types by industry
    SCHEMA_TYPES = {
        "banking": ["Product", "FinancialProduct", "Service", "Offer"],
        "ecommerce": ["Product", "Offer", "Review", "AggregateRating"],
        "insurance": ["Service", "Product", "Offer", "InsuranceAgency"],
        "general": ["Product", "Service", "Organization", "WebPage"]
    }
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        groq_model: str = "meta-llama/llama-4-maverick-17b-128e-instruct",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_provider: str = "auto"
    ):
        """Initialize the schema mapper."""
        self.llm_client = LLMClient(
            openai_api_key=openai_api_key,
            groq_api_key=groq_api_key,
            groq_model=groq_model,
            provider=llm_provider
        )
        self.embedding_model = SentenceTransformer(embedding_model)
        self.schema_embeddings = self._precompute_schema_embeddings()
    
    def _precompute_schema_embeddings(self) -> Dict[str, np.ndarray]:
        """Precompute embeddings for schema types."""
        schema_descriptions = {
            "Product": "A product available for purchase with name, price, brand, description",
            "FinancialProduct": "Financial products like credit cards, loans, accounts with fees, interest rates",
            "Service": "Services offered by organizations with pricing and terms",
            "Offer": "Offers, deals, promotions with prices and conditions",
            "Review": "Customer reviews and ratings",
            "AggregateRating": "Aggregated ratings and review counts",
            "Organization": "Company or organization information",
            "WebPage": "Web page content and metadata",
            "InsuranceAgency": "Insurance products and policies"
        }
        return {
            schema_type: self.embedding_model.encode(description)
            for schema_type, description in schema_descriptions.items()
        }
    
    def classify_industry(self, content: str) -> str:
        """Classify the industry/domain of the content using semantic similarity."""
        content_embedding = self.embedding_model.encode(content[:1000])  # First 1000 chars
        
        industry_keywords = {
            "banking": ["credit card", "loan", "account", "interest rate", "bank", "deposit", "withdrawal"],
            "ecommerce": ["product", "price", "buy", "cart", "shipping", "delivery", "review", "rating"],
            "insurance": ["insurance", "policy", "premium", "coverage", "claim", "motor", "health"]
        }
        
        best_match = "general"
        max_similarity = 0
        
        for industry, keywords in industry_keywords.items():
            keyword_text = " ".join(keywords)
            keyword_embedding = self.embedding_model.encode(keyword_text)
            similarity = np.dot(content_embedding, keyword_embedding) / (
                np.linalg.norm(content_embedding) * np.linalg.norm(keyword_embedding)
            )
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = industry
        
        return best_match
    
    def detect_schema_type(self, content: str, industry: str) -> str:
        """Detect the most appropriate Schema.org type using embeddings."""
        content_embedding = self.embedding_model.encode(content[:1000])
        
        candidate_types = self.SCHEMA_TYPES.get(industry, self.SCHEMA_TYPES["general"])
        best_type = "Product"
        max_similarity = 0
        
        for schema_type in candidate_types:
            if schema_type in self.schema_embeddings:
                similarity = np.dot(content_embedding, self.schema_embeddings[schema_type]) / (
                    np.linalg.norm(content_embedding) * np.linalg.norm(self.schema_embeddings[schema_type])
                )
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_type = schema_type
        
        return best_type
    
    def extract_with_llm(self, html_content: str, text_content: str, schema_type: str) -> Dict[str, Any]:
        """Use LLM to extract structured data according to Schema.org schema."""
        
        prompt = f"""Extract structured data from the following web content and normalize it according to Schema.org {schema_type} schema.

Content:
{text_content[:3000]}

Extract and return a JSON object with the following structure based on Schema.org {schema_type}:
- Include all relevant properties for {schema_type}
- Normalize field names to match Schema.org conventions
- Extract prices, ratings, dates, and other structured data
- Return only valid JSON, no markdown formatting

Schema.org {schema_type} properties to consider:
- name, description, brand, price, priceCurrency
- For FinancialProduct: annualFee, interestRate, rewards, benefits
- For Product: aggregateRating, reviewCount, availability, offers
- For Service: serviceType, areaServed, provider
- For Offer: price, priceCurrency, availability, validFrom, validThrough

Return JSON only:"""

        try:
            messages = [
                {"role": "system", "content": "You are a data extraction expert that extracts structured data according to Schema.org schemas. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ]
            
            result_text = self.llm_client.chat_completion(
                messages=messages,
                temperature=0.1,
                max_tokens=2000
            )
            # Remove markdown code blocks if present
            result_text = re.sub(r'```json\s*', '', result_text)
            result_text = re.sub(r'```\s*', '', result_text)
            result_text = result_text.strip()
            
            extracted_data = json.loads(result_text)
            
            # Add schema context
            extracted_data["@type"] = schema_type
            extracted_data["@context"] = "https://schema.org"
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return {"@type": schema_type, "@context": "https://schema.org", "error": "Failed to parse LLM response"}
        except Exception as e:
            print(f"LLM extraction error: {e}")
            return {"@type": schema_type, "@context": "https://schema.org", "error": str(e)}
    
    def normalize_to_jsonld(self, data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Convert extracted data to JSON-LD format."""
        jsonld = {
            "@context": "https://schema.org",
            "@type": data.get("@type", "Product"),
            "@id": url
        }
        
        # Map common fields
        field_mapping = {
            "name": "name",
            "description": "description",
            "price": "price",
            "priceCurrency": "priceCurrency",
            "brand": "brand",
            "image": "image",
            "url": "url",
            "aggregateRating": "aggregateRating",
            "reviewCount": "reviewCount",
            "availability": "availability",
            "annualFee": "annualFee",
            "interestRate": "interestRate",
            "rewards": "rewards",
            "benefits": "benefits",
            "coverage": "coverage",
            "policyTerm": "policyTerm",
            "serviceType": "serviceType"
        }
        
        for key, value in data.items():
            if key not in ["@type", "@context", "@id"] and value is not None:
                schema_key = field_mapping.get(key, key)
                jsonld[schema_key] = value
        
        return jsonld

