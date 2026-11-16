import unittest
from services.ms4_orchestrator.config.config import settings
from services.ms4_orchestrator.clients.dspace_auth_client import DSpaceAuthClient


class TestDSpaceConfig(unittest.IsolatedAsyncioTestCase):
    def test_dspace_settings_loaded(self):
        """Verifica que las credenciales de DSpace se cargan correctamente desde .env o secrets."""
        self.assertTrue(settings.dspace_api_url.startswith(("http://", "https://")), 
                        f"dspace_api_url debe comenzar con protocolo HTTP/HTTPS: {settings.dspace_api_url}")
        self.assertEqual(settings.dspace_username, "agente-ia@usach.cl")
        self.assertTrue(len(settings.dspace_password) > 0, "dspace_password no debe estar vacío")

    def test_dspace_auth_client_initialization(self):
        """Verifica que DSpaceAuthClient hereda la URL y credenciales de configuración."""
        client = DSpaceAuthClient()
        self.assertTrue(client.base_url.startswith(("http://", "https://")))
        self.assertEqual(client.email, "agente-ia@usach.cl")

    async def test_dspace_auth_client_invalid_url_raises_clear_error(self):
        """Verifica que una URL vacía o sin protocolo genera un ValueError descriptivo."""
        client = DSpaceAuthClient(base_url="")
        client.base_url = ""
        with self.assertRaises(ValueError) as ctx:
            await client.authenticate()
        self.assertIn("URL de DSpace inválida", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

