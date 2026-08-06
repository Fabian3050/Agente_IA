import httpx
from typing import List, Optional
from app.models.metadata_model import MetadataResponse

def _reconstruct_openalex_abstract(inv_index: Optional[dict]) -> Optional[str]:
    if not inv_index:
        return None
    try:
        max_idx = max(max(positions) for positions in inv_index.values()) if inv_index else -1
        if max_idx >= 0:
            words = [""] * (max_idx + 1)
            for word, positions in inv_index.items():
                for pos in positions:
                    words[pos] = word
            return " ".join(words).strip()
    except Exception:
        pass
    return None

async def search_openalex(query: str, limit: int = 5) -> List[MetadataResponse]:
    url = "https://api.openalex.org/works"
    params = {"search": query, "per-page": limit}
    results = []
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            items = data.get("results", [])
            
            for item in items:
                title = item.get("title") or "No title"
                authors = [
                    auth.get("author", {}).get("display_name", "") 
                    for auth in item.get("authorships", [])
                ]
                authors = [a for a in authors if a]
                
                doi = item.get("doi")
                if doi and doi.startswith("https://doi.org/"):
                    doi = doi.replace("https://doi.org/", "")
                    
                year = item.get("publication_year")
                item_url = item.get("id")
                abstract = _reconstruct_openalex_abstract(item.get("abstract_inverted_index"))
                
                keywords = []
                if item.get("keywords"):
                    keywords = [kw.get("display_name") for kw in item.get("keywords", []) if kw.get("display_name")]
                elif item.get("concepts"):
                    keywords = [concept.get("display_name") for concept in item.get("concepts", []) if concept.get("display_name")]
                
                results.append(MetadataResponse(
                    title=title,
                    authors=authors,
                    doi=doi,
                    year=year,
                    source="openalex",
                    url=item_url,
                    abstract=abstract,
                    keywords=keywords
                ))
        except Exception as e:
            print(f"Error fetching from OpenAlex: {e}")
            
    return results

async def get_by_doi_openalex(doi: str) -> Optional[MetadataResponse]:
    # OpenAlex expects the doi to be prefixed with https://doi.org/
    # The endpoint is /works/https://doi.org/{doi} or simply /works/doi:{doi}
    url = f"https://api.openalex.org/works/doi:{doi}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            item = response.json()
            
            title = item.get("title") or "No title"
            authors = [
                auth.get("author", {}).get("display_name", "") 
                for auth in item.get("authorships", [])
            ]
            authors = [a for a in authors if a]
            
            retrieved_doi = item.get("doi")
            if retrieved_doi and retrieved_doi.startswith("https://doi.org/"):
                retrieved_doi = retrieved_doi.replace("https://doi.org/", "")
                
            year = item.get("publication_year")
            item_url = item.get("id")
            abstract = _reconstruct_openalex_abstract(item.get("abstract_inverted_index"))
            
            keywords = []
            if item.get("keywords"):
                keywords = [kw.get("display_name") for kw in item.get("keywords", []) if kw.get("display_name")]
            elif item.get("concepts"):
                keywords = [concept.get("display_name") for concept in item.get("concepts", []) if concept.get("display_name")]
            
            return MetadataResponse(
                title=title,
                authors=authors,
                doi=retrieved_doi,
                year=year,
                source="openalex",
                url=item_url,
                abstract=abstract,
                keywords=keywords
            )
        except Exception as e:
            print(f"Error fetching from OpenAlex by DOI: {e}")
            
    return None
