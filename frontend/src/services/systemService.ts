import axios from 'axios'
import { MS_ENDPOINTS } from './api'
import type { ServiceStatus } from '../types'

export const systemService = {
  async checkAllServices(): Promise<ServiceStatus[]> {
    const services = [
      { name: 'MS4 Orquestador & Gateway', service: 'ms4_orchestrator', port: 8000, url: `${MS_ENDPOINTS.MS4_ORCHESTRATOR}/health` },
      { name: 'MS1 Recuperación de Metadatos', service: 'ms1_retrieval', port: 8001, url: `${MS_ENDPOINTS.MS1_RETRIEVAL}/health` },
      { name: 'MS2 Clasificación Semántica (LLM)', service: 'ms2_classification', port: 8002, url: `${MS_ENDPOINTS.MS2_CLASSIFICATION}/health` },
      { name: 'MS3 Autenticación y Auditoría (OIDC)', service: 'ms3_auth', port: 8003, url: `${MS_ENDPOINTS.MS3_AUTH}/health` },
    ]

    const results: ServiceStatus[] = []

    for (const s of services) {
      try {
        const res = await axios.get(s.url, { timeout: 3000 })
        results.push({
          name: s.name,
          service: s.service,
          port: s.port,
          url: s.url.replace('/health', ''),
          status: res.status === 200 ? 'online' : 'offline',
          version: res.data?.version || '3.0.0',
        })
      } catch {
        results.push({
          name: s.name,
          service: s.service,
          port: s.port,
          url: s.url.replace('/health', ''),
          status: 'offline',
        })
      }
    }

    return results
  }
}

