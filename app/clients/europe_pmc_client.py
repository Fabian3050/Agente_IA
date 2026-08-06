import httpx
from typing import List, Optional
from app.models.metadata_model import MetadataResponse

async def search_europe_pmc(query: str, limit: int = 5) -> List[MetadataResponse]:
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": query,
        "format": "json",
        "resultType": "core",
        "pageSize": limit
    }
    results = []
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            items = data.get("resultList", {}).get("result", [])
            
            for item in items:
                title = item.get("title") or "No title"
                
                author_string = item.get("authorString", "")
                authors = [a.strip() for a in author_string.split(",")] if author_string else []
                
                doi = item.get("doi")
                
                year_str = item.get("pubYear")
                year = int(year_str) if year_str and year_str.isdigit() else None
                
                pmcid = item.get("pmcid")
                item_url = f"https://europepmc.org/article/PMC/{pmcid}" if pmcid else None
                abstract = item.get("abstractText")
                
                keyword_list = item.get("keywordList")
                keywords = []
                if keyword_list and "keyword" in keyword_list:
                    kws = keyword_list["keyword"]
                    if isinstance(kws, list):
                        keywords = kws
                    elif isinstance(kws, str):
                        keywords = [kws]
                
                results.append(MetadataResponse(
                    title=title,
                    authors=authors,
                    doi=doi,
                    year=year,
                    source="europepmc",
                    url=item_url,
                    abstract=abstract,
                    keywords=keywords
                ))
        except Exception as e:
            print(f"Error fetching from Europe PMC: {e}")
            
    return results

async def get_by_doi_europe_pmc(doi: str) -> Optional[MetadataResponse]:
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": f"DOI:{doi}",
        "format": "json",
        "resultType": "core",
        "pageSize": 1
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            items = data.get("resultList", {}).get("result", [])
            
            if not items:
                return None
                
            item = items[0]
            
            title = item.get("title") or "No title"
            
            author_string = item.get("authorString", "")
            authors = [a.strip() for a in author_string.split(",")] if author_string else []
            
            retrieved_doi = item.get("doi", doi)
            
            year_str = item.get("pubYear")
            year = int(year_str) if year_str and year_str.isdigit() else None
            
            pmcid = item.get("pmcid")
            item_url = f"https://europepmc.org/article/PMC/{pmcid}" if pmcid else None
            abstract = item.get("abstractText")
            
            keyword_list = item.get("keywordList")
            keywords = []
            if keyword_list and "keyword" in keyword_list:
                kws = keyword_list["keyword"]
                if isinstance(kws, list):
                    keywords = kws
                elif isinstance(kws, str):
                    keywords = [kws]
            
            return MetadataResponse(
                title=title,
                authors=authors,
                doi=retrieved_doi,
                year=year,
                source="europepmc",
                url=item_url,
                abstract=abstract,
                keywords=keywords
            )
        except Exception as e:
            print(f"Error fetching from Europe PMC by DOI: {e}")
            
    return None
