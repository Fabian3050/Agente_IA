import httpx
from typing import List, Optional
from app.models.metadata_model import MetadataResponse

# Unpaywall uses email for authentication/politeness
UNPAYWALL_EMAIL = "test@example.com"

async def search_unpaywall(query: str, limit: int = 5) -> List[MetadataResponse]:
    # Unpaywall REST API doesn't natively support free-text search of metadata.
    # It focuses on DOI lookup.
    return []

async def get_by_doi_unpaywall(doi: str) -> Optional[MetadataResponse]:
    url = f"https://api.unpaywall.org/v2/{doi}"
    params = {"email": UNPAYWALL_EMAIL}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            
            title = data.get("title") or "No title"
            
            authors = []
            for author in data.get("z_authors", []):
                name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                if name:
                    authors.append(name)
            
            retrieved_doi = data.get("doi", doi)
            year = data.get("year")
            
            # Find the best open access URL if available
            best_oa_location = data.get("best_oa_location")
            item_url = None
            if best_oa_location:
                item_url = best_oa_location.get("url_for_pdf") or best_oa_location.get("url_for_landing_page") or best_oa_location.get("url")
            
            # Unpaywall doesn't typically provide abstracts
            abstract = None
            
            return MetadataResponse(
                title=title,
                authors=authors,
                doi=retrieved_doi,
                year=year,
                source="unpaywall",
                url=item_url,
                abstract=abstract
            )
        except Exception as e:
            print(f"Error fetching from Unpaywall by DOI: {e}")
            
    return None
