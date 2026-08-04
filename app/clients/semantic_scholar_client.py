import httpx
from typing import List, Optional
from app.models.metadata_model import MetadataResponse

async def search_semantic_scholar(query: str, limit: int = 5) -> List[MetadataResponse]:
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query, 
        "limit": limit,
        "fields": "title,authors,year,externalIds,url,abstract"
    }
    results = []
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            items = data.get("data", [])
            
            for item in items:
                title = item.get("title") or "No title"
                authors = [auth.get("name", "") for auth in item.get("authors", [])]
                authors = [a for a in authors if a]
                
                external_ids = item.get("externalIds", {})
                doi = external_ids.get("DOI")
                
                year = item.get("year")
                item_url = item.get("url")
                abstract = item.get("abstract")
                
                results.append(MetadataResponse(
                    title=title,
                    authors=authors,
                    doi=doi,
                    year=year,
                    source="semanticscholar",
                    url=item_url,
                    abstract=abstract
                ))
        except Exception as e:
            print(f"Error fetching from Semantic Scholar: {e}")
            
    return results

async def get_by_doi_semantic_scholar(doi: str) -> Optional[MetadataResponse]:
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
    params = {
        "fields": "title,authors,year,externalIds,url,abstract"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            item = response.json()
            
            title = item.get("title") or "No title"
            authors = [auth.get("name", "") for auth in item.get("authors", [])]
            authors = [a for a in authors if a]
            
            external_ids = item.get("externalIds", {})
            retrieved_doi = external_ids.get("DOI", doi)
            
            year = item.get("year")
            item_url = item.get("url")
            abstract = item.get("abstract")
            
            return MetadataResponse(
                title=title,
                authors=authors,
                doi=retrieved_doi,
                year=year,
                source="semanticscholar",
                url=item_url,
                abstract=abstract
            )
        except Exception as e:
            print(f"Error fetching from Semantic Scholar by DOI: {e}")
            
    return None
