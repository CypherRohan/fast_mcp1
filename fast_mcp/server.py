from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
import requests
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MCP_BEARER_TOKEN = os.getenv("MCP_BEARER_TOKEN")

genai.configure(api_key=GEMINI_API_KEY)
TAVILY_API_URL = "https://api.tavily.com/search"

# Create main FastAPI app
app = FastAPI(title="Local Business Finder MCP Server")

# Create FastMCP server
mcp_server = FastMCP("LocalBusinessFinder")

# Health check route
@app.get("/")
def root():
    return {"status": "MCP Server Running"}

# MCP tools
@mcp_server.tool()
def validate(token: str):
    if token != MCP_BEARER_TOKEN:
        raise ValueError("Invalid token")
    return {"phone": "919876543210"}

@mcp_server.tool()
def find_local_business(query: str):
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "max_results": 10
    }
    response = requests.post(TAVILY_API_URL, json=payload)
    data = response.json()

    snippets = []
    for result in data.get("results", []):
        title = result.get("title", "No title")
        url = result.get("url", "")
        snippet = result.get("content", "")
        snippets.append(f"{title} - {snippet} ({url})")

    if not snippets:
        return {"error": "No results found"}

    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    I have search results about '{query}':
    {snippets}

    Provide me the lists and their location link if available, in a structured way.
    """
    result = model.generate_content(prompt)

    return {"results": result.text}

# Mount MCP server under /mcp
app.mount("/mcp", mcp_server)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2015)
