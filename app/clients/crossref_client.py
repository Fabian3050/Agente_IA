import httpx
import re
from typing import List, Optional
from app.models.metadata_model import MetadataResponse

async def search_crossref(query: str, limit: int = 5) -> List[MetadataResponse]:
    url = "https://api.crossref.org/works"
    params = {"query": query, "rows": limit}
    results = []
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            items = data.get("message", {}).get("items", [])
            
            for item in items:
                title = item.get("title", [""])[0] if item.get("title") else "No title"
                authors = []
                for author in item.get("author", []):
                    name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                    if name:
                        authors.append(name)
                
                doi = item.get("DOI")
                
                # Try to extract published year
                year = None
                published = item.get("published-print") or item.get("published-online")
                if published and published.get("date-parts"):
                    year = published["date-parts"][0][0]
                
                item_url = item.get("URL")
                
                raw_abstract = item.get("abstract")
                abstract = re.sub(r'<[^>]+>', '', str(raw_abstract)) if raw_abstract else None
                
                results.append(MetadataResponse(
                    title=title,
                    authors=authors,
                    doi=doi,
                    year=year,
                    source="crossref",
                    url=item_url,
                    abstract=abstract
                ))
        except Exception as e:
            print(f"Error fetching from CrossRef: {e}")
            
    return results

async def get_by_doi_crossref(doi: str) -> Optional[MetadataResponse]:
    url = f"https://api.crossref.org/works/{doi}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            item = data.get("message", {})
            
            title = item.get("title", [""])[0] if item.get("title") else "No title"
            authors = []
            for author in item.get("author", []):
                name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                if name:
                    authors.append(name)
            
            retrieved_doi = item.get("DOI", doi)
            
            year = None
            published = item.get("published-print") or item.get("published-online")
            if published and published.get("date-parts"):
                year = published["date-parts"][0][0]
            
            item_url = item.get("URL")
            
            raw_abstract = item.get("abstract")
            abstract = re.sub(r'<[^>]+>', '', str(raw_abstract)) if raw_abstract else None
            
            return MetadataResponse(
                title=title,
                authors=authors,
                doi=retrieved_doi,
                year=year,
                source="crossref",
                url=item_url,
                abstract=abstract
            )
        except Exception as e:
            print(f"Error fetching from CrossRef by DOI: {e}")
            
    return None
