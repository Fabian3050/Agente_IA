import os
import httpx
import uuid
from typing import Dict, Any, Optional

MS1_URL = os.getenv("MS1_RETRIEVAL_URL", "http://localhost:8001")
MS2_URL = os.getenv("MS2_CLASSIFICATION_URL", "http://localhost:8002")
MS3_URL = os.getenv("MS3_AUTH_URL", "http://localhost:8003")


class MS1Client:
    async def retrieve(self, item_id: uuid.UUID, doi: Optional[str], title: Optional[str]) -> Dict[str, Any]:
        url = f"{MS1_URL.rstrip('/')}/retrieve"
        payload = {
            "item_id": str(item_id),
            "doi": doi,
            "title": title
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()


class MS2Client:
    async def classify(self, item_id: uuid.UUID, title: Optional[str], abstract: Optional[str], keywords: Optional[str]) -> Dict[str, Any]:
        url = f"{MS2_URL.rstrip('/')}/classify"
        payload = {
            "item_id": str(item_id),
            "title": title,
            "abstract": abstract,
            "keywords": keywords,
            "temperature": 0.0,
            "repetition_number": 1
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()


class MS3Client:
    async def record_audit(
        self,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        action: str,
        previous_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        rejection_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        url = f"{MS3_URL.rstrip('/')}/audit"
        payload = {
            "user_id": str(user_id),
            "item_id": str(item_id),
            "action": action,
            "previous_value": previous_value,
            "new_value": new_value,
            "rejection_reason": rejection_reason
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def verify_role(self, user_id: uuid.UUID, required_role: str) -> bool:
        url = f"{MS3_URL.rstrip('/')}/auth/verify-role"
        params = {"user_id": str(user_id), "required_role": required_role}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            return resp.status_code == 200

    async def introspect_token(self, token: str) -> Dict[str, Any]:
        url = f"{MS3_URL.rstrip('/')}/auth/introspect"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"token": token})
            if resp.status_code == 200:
                return resp.json()
            return {"active": False}

