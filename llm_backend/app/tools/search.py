from typing import Dict, List

import requests

from app.core.config import settings


class SearchTool:
    def __init__(self):
        self.tavily_api_key = settings.TAVILY_API_KEY
        self.serpapi_key = settings.SERPAPI_KEY
        if not self.tavily_api_key and not self.serpapi_key:
            raise ValueError("未配置 TAVILY_API_KEY 或 SERPAPI_KEY")

    def search(self, query: str, num_results: int = 3) -> List[Dict]:
        num_results = settings.SEARCH_RESULT_COUNT or num_results
        if self.tavily_api_key:
            return self._tavily_search(query, num_results)
        return self._serpapi_search(query, num_results)

    def _tavily_search(self, query: str, num_results: int) -> List[Dict]:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": self.tavily_api_key,
                "query": query,
                "max_results": num_results,
                "search_depth": "advanced",
                "topic": "general",
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            }
            for item in data.get("results", [])
        ][:num_results]

    def _serpapi_search(self, query: str, num_results: int) -> List[Dict]:
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "google",
                "q": query,
                "api_key": self.serpapi_key,
                "num": num_results,
                "hl": "zh-CN",
                "gl": "cn",
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            }
            for item in data.get("organic_results", [])
        ][:num_results]
