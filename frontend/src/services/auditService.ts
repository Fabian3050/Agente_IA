import { ms3Client, ms4Client } from './api'
import type { AuditLogEntry } from '../types'

export const auditService = {
  async getAuditLogs(): Promise<AuditLogEntry[]> {
    try {
      const res = await ms3Client.get<AuditLogEntry[]>('/audit')
      return res.data
    } catch {
      // Mock data matching the app.tsx audit table if endpoint returns 404
      return [
        {
          id: 1,
          timestamp: '2024-06-28 09:16:32',
          user: 'Agente IA (MS1)',
          role: 'Sistema',
          action: 'RECUPERAR',
          item_id: '13458',
          field: 'dc.description.abstract',
          prev_value: '[Vacío]',
          new_value: 'This study presents a machine learning framework...',
          confidence: 96,
          state: 'En clasificación'
        },
        {
          id: 2,
          timestamp: '2024-06-28 08:45:10',
          user: 'María González',
          role: 'Curador',
          action: 'APROBAR',
          item_id: '18954',
          field: 'dc.subject',
          prev_value: '[Vacío]',
          new_value: 'open science; scholarly communication; Chile',
          confidence: 88,
          state: 'Aprobada'
        },
        {
          id: 3,
          timestamp: '2024-06-27 16:20:00',
          user: 'Carlos Fuentes',
          role: 'Administrador',
          action: 'MODIFICAR',
          item_id: '31204',
          field: 'dc.rights',
          prev_value: 'Acceso Restringido',
          new_value: 'Acceso Abierto (CC BY 4.0)',
          confidence: 91,
          state: 'Aprobada'
        },
        {
          id: 4,
          timestamp: '2024-06-27 15:10:44',
          user: 'Fabián Escobedo',
          role: 'Curador',
          action: 'RECHAZAR',
          item_id: '22103',
          field: 'dc.subject.ocde',
          prev_value: '[Vacío]',
          new_value: '201 Ingeniería Civil',
          confidence: 42,
          state: 'Rechazada'
        },
      ]
    }
  }
}

