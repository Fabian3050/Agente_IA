# Agente IA - Frontend Desacoplado (Vue 3 + TypeScript + Tailwind CSS)

Frontend desacoplado para el **Agente Inteligente de Enriquecimiento de Metadatos DSpace-CRIS** (USACH / VRIIC), migrado desde el mockup reactivo `app.tsx` hacia una arquitectura modular en **Vue 3**.

---

## 🚀 Arquitectura y Tecnologías

- **Framework**: Vue 3.5 (Composition API con `<script setup lang="ts">`)
- **Build Tool**: Vite 5.4 + TypeScript (`vue-tsc`)
- **Estilos**: Tailwind CSS 3.4 (Paleta institucional USACH: `#00aea7`, `#1a2332`, `#F7F9FB`)
- **Iconografía**: `lucide-vue-next` (Iconos equivalentes idénticos a los del mockup)
- **Cliente HTTP**: Axios con interceptores JWT Bearer automáticos y base URLs configurables.

---

## 📁 Estructura del Proyecto

```tree
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── style.css
│   ├── types/
│   │   └── index.ts                 # Interfaces TypeScript (User, Proposal, AuditLog, etc.)
│   ├── services/                    # Capa desacoplada de comunicación con Microservicios
│   │   ├── api.ts                   # Cliente Axios base e interceptores JWT
│   │   ├── authService.ts           # MS3 (:8003) - Login, Mock SSO, OIDC y Usuarios
│   │   ├── proposalService.ts       # MS4 (:8000) - Ciclo de vida, Curaduría, Exportación CSV
│   │   ├── retrievalService.ts      # MS1 (:8001) - Fuentes OpenAlex, Crossref, etc.
│   │   ├── classificationService.ts # MS2 (:8002) - Inferencia LLM OCDE/ODS
│   │   ├── auditService.ts          # MS3 (:8003) - Logs de auditoría inmutables
│   │   ├── systemService.ts         # Health checks de los 4 microservicios
│   │   └── index.ts
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.vue          # Barra lateral colapsable institucional
│   │   │   └── Header.vue           # Barra superior con notificaciones y perfil
│   │   └── common/
│   │       ├── Badge.vue            # Badges de estado del ciclo de vida
│   │       ├── Card.vue             # Tarjeta contenedor estilo mockup
│   │       └── SectionHeader.vue    # Encabezado de sección estandarizado
│   └── views/                       # Vistas completas migradas desde app.tsx
│       ├── LoginView.vue            # Login institucional / OIDC USACH / Mock Roles
│       ├── DashboardView.vue        # KPIs, Gráfico Donut SVG y Actividad semanal
│       ├── MonitoreoView.vue        # Monitoreo de registros incompletos y detalle
│       ├── AnalisisView.vue         # Extracción de PDF con OCR/IA y validación
│       ├── ValidacionView.vue       # Validación sintáctica y algorítmica
│       ├── AprobacionView.vue       # Aprobación curatorial, comparación y export CSV seguro
│       ├── AuditoriaView.vue        # Trazabilidad completa e inmutable
│       ├── ReportesView.vue         # Reportes y rendimiento de fuentes científicas
│       ├── UsuariosView.vue         # Gestión de usuarios y control de permisos RBAC
│       ├── ConfiguracionView.vue    # Estado de microservicios y parámetros de IA
│       └── PerfilView.vue           # Perfil del usuario y credenciales
```

---

## ⚙️ Conexión con Microservicios

El frontend se comunica con los microservicios mediante variables de entorno o defaults locales:

| Microservicio | URL por Defecto | Responsabilidad |
|---|---|---|
| **MS4 Orchestrator** | `http://localhost:8000` | Orquestación, 12 estados de ciclo de vida, detección, exportación CSV en 2 pasos |
| **MS1 Retrieval** | `http://localhost:8001` | Consultas asíncronas a OpenAlex, Crossref, Unpaywall |
| **MS2 Classification** | `http://localhost:8002` | Inferencia semántica con LLM local Ollama (OCDE / ODS) |
| **MS3 Auth & Audit** | `http://localhost:8003` | OAuth 2.0 / OpenID Connect (OIDC), JWT Bearer, Auditoría INSERT-only |

### Variables de Entorno Opcionales (`.env`):
```env
VITE_MS4_URL=http://localhost:8000
VITE_MS1_URL=http://localhost:8001
VITE_MS2_URL=http://localhost:8002
VITE_MS3_URL=http://localhost:8003
```

---

## 🛠️ Instrucciones de Ejecución

### 1. Modo Desarrollo
```bash
cd frontend
npm run dev
```
La aplicación estará disponible en `http://localhost:5173`.

### 2. Compilación para Producción
```bash
cd frontend
npm run build
```
Genera los archivos estáticos optimizados y minificados en `frontend/dist/`.

