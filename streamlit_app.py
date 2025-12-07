"""Streamlit demo app for AI_Domain_Agnostic_Crawler."""
import streamlit as st
import requests
import json
from typing import Dict, Any
import time

# Page configuration
st.set_page_config(
    page_title="AI_Domain_Agnostic_Crawler Demo",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API URL - can be configured via environment variable or defaults to localhost
import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def crawl_url(url: str, force_refresh: bool = False):
    """Crawl a URL."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/crawl",
            json={"url": url, "force_refresh": force_refresh},
            timeout=180
        )
        if response.status_code == 200:
            return response.json()
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", response.text)
            except:
                error_msg = response.text
            return {"error": error_msg, "status_code": response.status_code}
    except requests.exceptions.Timeout:
        return {"error": "Request timeout - URL took too long to crawl. Try again or use a different URL."}
    except requests.exceptions.ConnectionError:
        return {"error": f"Connection error - Cannot connect to API server at {API_BASE_URL}. Make sure the server is running."}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

def search_similar(query: str, limit: int = 10):
    """Search for similar content."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/search",
            json={"query": query, "limit": limit},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", response.text)
            except:
                error_msg = response.text
            return {"error": error_msg, "status_code": response.status_code}
    except requests.exceptions.Timeout:
        return {"error": "Request timeout - Search took too long. Try again."}
    except requests.exceptions.ConnectionError:
        return {"error": f"Connection error - Cannot connect to API server at {API_BASE_URL}. Make sure the server is running."}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

def rag_query(query: str, industry: str = None, include_sources: bool = True):
    """RAG query."""
    try:
        data = {"query": query, "include_sources": include_sources}
        if industry:
            data["industry"] = industry
        response = requests.post(
            f"{API_BASE_URL}/rag/query",
            json=data,
            timeout=60
        )
        return response.json() if response.status_code == 200 else {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def rag_compare(query: str, industry: str = None):
    """RAG compare products."""
    try:
        data = {"query": query}
        if industry:
            data["industry"] = industry
        response = requests.post(
            f"{API_BASE_URL}/rag/compare",
            json=data,
            timeout=60
        )
        return response.json() if response.status_code == 200 else {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

def get_by_industry(industry: str, limit: int = 100):
    """Get pages by industry."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/industry/{industry}",
            params={"limit": limit},
            timeout=30
        )
        return response.json() if response.status_code == 200 else {"error": response.text}
    except Exception as e:
        return {"error": str(e)}

# Main App
st.markdown('<h1 class="main-header">🕷️ AI_Domain_Agnostic_Crawler</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Info")
    
    st.header("📚 Quick Links")
    st.markdown(f"""
    - [API Documentation]({API_BASE_URL}/docs)
    - [Health Check]({API_BASE_URL}/health)
    - [API Root]({API_BASE_URL}/)
    """)
    
    st.divider()
    
    st.header("ℹ️ Features")
    st.markdown("""
    - 🕷️ **Web Crawling**: Extract data from any URL
    - 🔍 **Semantic Search**: Meaning-based search
    - 🤖 **RAG Q&A**: AI-powered questions & answers
    - 📊 **Product Comparison**: Compare multiple items
    - 🏷️ **Industry Classification**: Auto-detect domain
    """)
    
    st.divider()
    
    st.header("🔧 Tech Stack")
    st.markdown("""
    - FastAPI
    - Crawl4AI
    - OpenAI/Groq
    - PostgreSQL
    - Qdrant
    - Schema.org
    """)

# Main Content
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🕷️ Crawl URL", 
    "🔍 Search", 
    "🤖 RAG Query", 
    "📊 Compare", 
    "📁 Browse Data"
])

# Tab 1: Crawl URL
with tab1:
    st.header("Crawl & Extract Data from URL")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        url = st.text_input(
            "Enter URL to crawl:",
            placeholder="https://www.example.com",
            value="",
            key="crawl_url_input"
        )
    
    with col2:
        force_refresh = st.checkbox("Force Refresh", value=False, key="force_refresh_checkbox")
    
    if st.button("🚀 Crawl URL", type="primary", use_container_width=True):
        if url:
            with st.spinner("Crawling URL... This may take 30-60 seconds"):
                result = crawl_url(url, force_refresh)
                
                # Check for actual errors (not just the presence of error key)
                if "error" in result and result.get("error") is not None:
                    error_msg = result.get("error", "Unknown error")
                    st.error(f"❌ Error: {error_msg}")
                    if result.get("status_code"):
                        st.info(f"Status Code: {result.get('status_code')}")
                elif result.get("success"):
                    st.success("✅ URL crawled successfully!")
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Industry", result.get("industry", "N/A"))
                    with col2:
                        st.metric("Schema Type", result.get("schema_type", "N/A"))
                    with col3:
                        st.metric("Page ID", result.get("page_id", "N/A")[:8] + "...")
                    
                    # Extracted Data
                    st.subheader("📋 Extracted Data")
                    extracted_data = result.get("extracted_data", {})
                    st.json(extracted_data)
                    
                    # JSON-LD
                    with st.expander("📄 View JSON-LD"):
                        st.json(result.get("jsonld", {}))
                else:
                    st.error("Failed to crawl URL")
        else:
            st.warning("Please enter a URL")

# Tab 2: Search
with tab2:
    st.header("🔍 Semantic Search")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Search query:",
            placeholder="e.g., credit card with cashback",
            value="",
            key="search_query_input"
        )
    
    with col2:
        search_limit = st.number_input("Limit", min_value=1, max_value=50, value=10, key="search_limit_input")
    
    if st.button("🔍 Search", type="primary", use_container_width=True, key="search_button"):
        if search_query:
            with st.spinner("Searching..."):
                results = search_similar(search_query, search_limit)
                
                # Check for errors first
                if "error" in results and results.get("error") is not None:
                    error_msg = results.get("error", "Unknown error")
                    st.error(f"❌ Error: {error_msg}")
                    if results.get("status_code"):
                        st.info(f"Status Code: {results.get('status_code')}")
                # Check if we have valid results
                elif "results" in results or "count" in results:
                    count = results.get("count", len(results.get("results", [])))
                    st.success(f"✅ Found {count} results")
                    
                    search_results = results.get("results", [])
                    if count > 0 and len(search_results) > 0:
                        for i, item in enumerate(search_results, 1):
                            with st.container():
                                st.markdown(f"### Result {i}")
                                
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(f"**Title:** {item.get('title', 'N/A')}")
                                    st.write(f"**URL:** {item.get('url', 'N/A')}")
                                    st.write(f"**Industry:** {item.get('industry', 'N/A')}")
                                    st.write(f"**Schema Type:** {item.get('schema_type', 'N/A')}")
                                
                                with col2:
                                    similarity = item.get('similarity_score', 0)
                                    if isinstance(similarity, (int, float)):
                                        st.metric("Similarity", f"{similarity:.2%}")
                                    else:
                                        st.metric("Similarity", "N/A")
                                
                                with st.expander("View Details"):
                                    st.json(item.get('extracted_data', {}))
                                
                                st.divider()
                    else:
                        st.info("No results found. Try crawling some URLs first.")
                else:
                    # Debug: show what we received
                    st.warning("Unexpected response format.")
                    with st.expander("Debug: View Response"):
                        st.json(results)
        else:
            st.warning("Please enter a search query")

# Tab 3: RAG Query
with tab3:
    st.header("🤖 RAG Query - Ask Questions")
    
    rag_query_text = st.text_area(
        "Enter your question:",
        placeholder="e.g., What insurance policies are available?",
        height=100,
        key="rag_query_textarea"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        rag_industry = st.selectbox(
            "Industry (Optional):",
            ["", "banking", "ecommerce", "insurance", "general"],
            index=0,
            key="rag_industry_select"
        )
    
    with col2:
        include_sources = st.checkbox("Include Sources", value=True, key="include_sources_checkbox")
    
    if st.button("🤖 Ask Question", type="primary", use_container_width=True):
        if rag_query_text:
            with st.spinner("Generating answer... This may take 10-30 seconds"):
                industry_filter = rag_industry if rag_industry else None
                result = rag_query(rag_query_text, industry_filter, include_sources)
                
                if "error" in result:
                    st.error(f"❌ Error: {result['error']}")
                else:
                    st.success("✅ Answer generated!")
                    
                    # Answer
                    st.subheader("💬 Answer")
                    st.markdown(result.get("answer", "No answer generated"))
                    
                    # Sources
                    if include_sources and result.get("sources"):
                        st.subheader("📚 Sources")
                        sources_count = result.get("sources_count", 0)
                        st.info(f"Found {sources_count} source(s)")
                        
                        for i, source in enumerate(result.get("sources", []), 1):
                            with st.container():
                                st.markdown(f"**Source {i}:**")
                                st.write(f"- **Title:** {source.get('title', 'N/A')}")
                                st.write(f"- **URL:** {source.get('url', 'N/A')}")
                                st.write(f"- **Industry:** {source.get('industry', 'N/A')}")
                                if 'similarity_score' in source:
                                    st.write(f"- **Relevance:** {source['similarity_score']:.2%}")
                    
                    # Model info
                    if result.get("model"):
                        st.caption(f"Generated using: {result.get('model')}")
        else:
            st.warning("Please enter a question")

# Tab 4: Compare
with tab4:
    st.header("📊 Compare Products/Services")
    
    compare_query = st.text_area(
        "Enter comparison query:",
        placeholder="e.g., Compare insurance policies",
        height=100,
        key="compare_query_textarea"
    )
    
    compare_industry = st.selectbox(
        "Industry (Optional):",
        ["", "banking", "ecommerce", "insurance", "general"],
        index=0,
        key="compare_industry_select"
    )
    
    if st.button("📊 Compare", type="primary", use_container_width=True):
        if compare_query:
            with st.spinner("Comparing... This may take 15-30 seconds"):
                industry_filter = compare_industry if compare_industry else None
                result = rag_compare(compare_query, industry_filter)
                
                if "error" in result:
                    st.error(f"❌ Error: {result['error']}")
                elif "items_found" in result:
                    st.warning(f"⚠️ {result.get('answer', 'Need at least 2 items to compare')}")
                else:
                    st.success("✅ Comparison generated!")
                    
                    # Comparison
                    st.subheader("📊 Comparison")
                    st.markdown(result.get("answer", "No comparison generated"))
                    
                    # Items compared
                    items_count = result.get("items_compared", 0)
                    st.info(f"Compared {items_count} item(s)")
                    
                    # Sources
                    if result.get("sources"):
                        st.subheader("📚 Sources")
                        for i, source in enumerate(result.get("sources", []), 1):
                            st.write(f"{i}. **{source.get('title', 'N/A')}**")
                            st.write(f"   {source.get('url', 'N/A')}")
        else:
            st.warning("Please enter a comparison query")

# Tab 5: Browse Data
with tab5:
    st.header("📁 Browse Crawled Data")
    
    industry_filter = st.selectbox(
        "Filter by Industry:",
        ["all", "banking", "ecommerce", "insurance", "general"],
        index=0,
        key="browse_industry_select"
    )
    
    limit = st.slider("Number of results:", min_value=5, max_value=100, value=20, key="browse_limit_slider")
    
    if st.button("🔍 Load Data", type="primary", use_container_width=True):
        if industry_filter == "all":
            st.info("Select a specific industry to view data")
        else:
            with st.spinner("Loading data..."):
                result = get_by_industry(industry_filter, limit)
                
                if "error" in result:
                    st.error(f"❌ Error: {result['error']}")
                else:
                    count = result.get("count", 0)
                    st.success(f"✅ Found {count} page(s) in {industry_filter} industry")
                    
                    if count > 0:
                        for i, page in enumerate(result.get("results", []), 1):
                            with st.container():
                                st.markdown(f"### Page {i}: {page.get('title', 'N/A')}")
                                
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(f"**URL:** {page.get('url', 'N/A')}")
                                    st.write(f"**Schema Type:** {page.get('schema_type', 'N/A')}")
                                    st.write(f"**Description:** {page.get('description', 'N/A')[:200]}...")
                                
                                with col2:
                                    st.write(f"**ID:** {page.get('id', 'N/A')[:8]}...")
                                    if page.get('created_at'):
                                        st.write(f"**Crawled:** {page.get('created_at')[:10]}")
                                
                                with st.expander("View Full Data"):
                                    st.json(page.get('extracted_data', {}))
                                
                                st.divider()
                    else:
                        st.info(f"No pages found in {industry_filter} industry. Try crawling some URLs first.")
    else:
        st.info("Click 'Load Data' to view crawled pages")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>AI_Domain_Agnostic_Crawler - Schema.org Normalization</p>
    <p>Built with FastAPI, Crawl4AI, OpenAI/Groq, PostgreSQL, and Qdrant</p>
</div>
""", unsafe_allow_html=True)

