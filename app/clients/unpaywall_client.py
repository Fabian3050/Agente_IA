import httpx
from typing import List, Optional
from app.models.metadata_model import MetadataResponse

# Unpaywall uses email for authentication/politeness
UNPAYWALL_EMAIL = "fescobedo182@gmail.com"

async def search_unpaywall(query: str, limit: int = 5) -> List[MetadataResponse]:
    # Unpaywall REST API doesn't natively support free-text search of metadata.
    # It focuses on DOI lookup.
    return []

async def get_by_doi_unpaywall(doi: str) -> Optional[dict]:
    url = f"https://api.unpaywall.org/v2/{doi}"
    params = {"email": UNPAYWALL_EMAIL}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            
            return data
        except Exception as e:
            print(f"Error fetching from Unpaywall by DOI: {e}")
            
    return None
