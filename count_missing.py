import httpx
import asyncio

async def count_missing():
    base_url = "https://sic.usach.cl/server/api"
    auth_payload = {"user": "agente-ia@usach.cl", "password": "XQpawq^4dSXXCIO-UuVz"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Auth
        r1 = await client.post(f"{base_url}/authn/login", data=auth_payload)
        csrf = r1.headers.get("DSPACE-XSRF-TOKEN")
        r2 = await client.post(f"{base_url}/authn/login", data=auth_payload, headers={"X-XSRF-TOKEN": csrf})
        token = r2.headers.get("Authorization").split(" ")[1]
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        
        params = {"dsoType": "item", "f.entityType": "Publication,equals", "page": 0, "size": 100}
        r = await client.get(f"{base_url}/discover/search/objects", headers=headers, params=params)
        data = r.json()
        total_pages = data.get("_embedded", {}).get("searchResult", {}).get("page", {}).get("totalPages", 0)
        
        print(f"Total pages to fetch: {total_pages}")
        
        missing_abstract = 0
        missing_doi = 0
        both_missing = 0
        total_items = 0
        
        async def fetch_page(page):
            p = {"dsoType": "item", "f.entityType": "Publication,equals", "page": page, "size": 100}
            resp = await client.get(f"{base_url}/discover/search/objects", headers=headers, params=p)
            return resp.json()

        for i in range(0, total_pages, 10):
            tasks = [fetch_page(p) for p in range(i, min(i + 10, total_pages))]
            results = await asyncio.gather(*tasks)
            for res in results:
                objects = res.get("_embedded", {}).get("searchResult", {}).get("_embedded", {}).get("objects", [])
                for obj in objects:
                    total_items += 1
                    meta = obj.get("_embedded", {}).get("indexableObject", {}).get("metadata", {})
                    
                    has_abs = "dc.description.abstract" in meta
                    has_doi = "dc.identifier.doi" in meta
                    
                    if not has_abs:
                        missing_abstract += 1
                    if not has_doi:
                        missing_doi += 1
                    if not has_abs and not has_doi:
                        both_missing += 1
                        
            print(f"Processed {total_items} items...")
            
        print("--- RESULTS ---")
        print(f"Total Items Evaluated: {total_items}")
        print(f"Missing Abstract: {missing_abstract}")
        print(f"Missing DOI: {missing_doi}")
        print(f"Missing Both: {both_missing}")

asyncio.run(count_missing())
