import httpx
import logging
from typing import Optional, Dict, Any
from app.config.config import settings


logger = logging.getLogger(__name__)

class DSpaceAuthClient:
    """
    Cliente para interactuar con la API REST de DSpace.
    Maneja la autenticación y peticiones base.
    """
    def __init__(self, base_url: str = settings.dspace_api_url):
        self.base_url = base_url.rstrip('/')
        self.email = settings.dspace_username
        self.password = settings.dspace_password
        
    async def authenticate(self) -> Optional[str]:
        """
        Realiza el login en DSpace manejando el token Anti-CSRF.
        Devuelve el token de autorización (JWT).
        """
        url = f"{self.base_url}/authn/login"
        
        payload = {
            "user": self.email,
            "password": self.password
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # 1. Primer intento (falla intencionadamente con 403 para obtener el token CSRF)
                response_1 = await client.post(url, data=payload)
                
                # Rescatar el token de los headers de respuesta
                csrf_token = response_1.headers.get("DSPACE-XSRF-TOKEN")
                
                if not csrf_token:
                    logger.error("No se pudo obtener el DSPACE-XSRF-TOKEN en el primer intento.")
                    # Por si acaso la primera petición fue exitosa (menos común en DSpace 7)
                    if response_1.status_code == 200:
                        auth_header = response_1.headers.get("Authorization")
                        if auth_header and auth_header.startswith("Bearer "):
                            return auth_header.split(" ")[1]
                    return None

                # 2. Reintento usando el token CSRF obtenido
                headers = {
                    "X-XSRF-TOKEN": csrf_token,
                    "DSPACE-XSRF-TOKEN": csrf_token # A veces DSpace también lo espera con este nombre
                }
                
                # El AsyncClient de httpx ya preserva las cookies (ej. SESSION cookie) que 
                # DSpace pudo haber devuelto en el primer intento, lo cual es necesario.
                response_2 = await client.post(url, data=payload, headers=headers)
                response_2.raise_for_status() # Esperamos un 200 OK
                
                # Obtener el token de autorización
                auth_header = response_2.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    return auth_header.split(" ")[1]
                
                return None
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Error HTTP en DSpace ({e.response.status_code}): {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Error de conexión con DSpace: {e}")
                raise

    async def get_items(self, token: str, query_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Recupera ítems a través de la API de descubrimiento (Search).
        Es el endpoint permitido para usuarios que no son administradores del sistema.
        """
        url = f"{self.base_url}/discover/search/objects" 
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        if query_params is None:
            query_params = {}
        # Aseguramos que solo busque ítems (y no comunidades o colecciones)
        query_params["dsoType"] = "item"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=query_params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error al obtener datos de DSpace: {e}")
                raise

    async def get_item(self, token: str, identifier: str) -> Dict[str, Any]:
        """
        Obtiene un ítem específico por su UUID.
        """
        url = f"{self.base_url}/core/items/{identifier}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Error al obtener el ítem {identifier}: {e}")
                raise
