import { ms3Client } from './api'

export interface RealAuditLog {
  id: string
  user_id?: string
  user_name?: string
  role?: string
  item_id: string
  action: string
  previous_value?: any
  new_value?: any
  rejection_reason?: string
  timestamp: string
}

export const auditService = {
  async getAuditLogs(): Promise<RealAuditLog[]> {
    try {
      const res = await ms3Client.get<RealAuditLog[]>('/audit/')
      return Array.isArray(res.data) ? res.data : []
    } catch {
      return []
    }
  },

  async getAuditTrailForItem(itemId: string): Promise<RealAuditLog[]> {
    try {
      const res = await ms3Client.get<RealAuditLog[]>(`/audit/${itemId}`)
      return Array.isArray(res.data) ? res.data : []
    } catch {
      return []
    }
  }
}

