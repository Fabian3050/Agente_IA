import { ms4Client } from './api'
import type { MetadataProposal, ProposalState } from '../types'

export interface CurateRequest {
  action: 'APPROVE' | 'REJECT'
  modified_value?: string
  curator_id?: string
  notes?: string
}

export interface CSVExportResult {
  message: string
  files: Array<{
    filename: string
    columns: string[]
    rows_count: number
    content: string
  }>
  total_exported: number
  omitted_count: number
}

export const proposalService = {
  async listProposals(params?: { state?: ProposalState; item_id?: string; field_name?: string }): Promise<any[]> {
    try {
      const res = await ms4Client.get<any>('/v3/proposals', { params: { status_filter: params?.state, ...params } })
      if (Array.isArray(res.data)) return res.data
      if (Array.isArray(res.data?.items)) return res.data.items
      return []
    } catch {
      return []
    }
  },

  async getQueue(params?: { estado?: string; tipo_falencia?: string; page?: number; size?: number; q?: string }): Promise<{ total: number; page: number; size: number; items: any[] }> {
    try {
      const res = await ms4Client.get<any>('/dspace/enrichment-queue', { params })
      return res.data || { total: 0, page: 0, size: 50, items: [] }
    } catch {
      return { total: 0, page: 0, size: 50, items: [] }
    }
  },

  async getQueueStats(): Promise<{ total_en_cola: number; por_estado: Record<string, number> }> {
    try {
      const res = await ms4Client.get<any>('/dspace/enrichment-queue/stats')
      return res.data || { total_en_cola: 0, por_estado: {} }
    } catch {
      return { total_en_cola: 0, por_estado: {} }
    }
  },

  async getCountMissing(saveToDb: boolean = false): Promise<any> {
    try {
      const res = await ms4Client.get<any>('/dspace/count-missing', { params: { save_to_db: saveToDb } })
      return res.data
    } catch {
      return null
    }
  },

  async getMetricsHistory(limit: number = 30): Promise<any[]> {
    try {
      const res = await ms4Client.get<any[]>('/dspace/metrics-history', { params: { limit } })
      return Array.isArray(res.data) ? res.data : []
    } catch {
      return []
    }
  },

  async getProposal(id: string): Promise<MetadataProposal | null> {
    try {
      const res = await ms4Client.get<MetadataProposal>(`/v3/proposals/${id}`)
      return res.data
    } catch {
      return null
    }
  },

  async curateProposal(id: string, req: CurateRequest): Promise<MetadataProposal> {
    const res = await ms4Client.post<MetadataProposal>(`/v3/proposals/${id}/curate`, req)
    return res.data
  },

  async exportCSV(items: Array<{ item_id: string; last_modified_dspace?: string; proposal_ids?: string[] }>): Promise<CSVExportResult> {
    const res = await ms4Client.post<CSVExportResult>('/v3/proposals/export-csv', { items })
    return res.data
  },

  async detectMissing(items: Array<{ item_id: string; title: string; missing_fields: string[]; doi?: string; last_modified_dspace?: string }>) {
    const res = await ms4Client.post('/v3/proposals/detect-missing', { items })
    return res.data
  },

  async enrichQueueItem(idOrUuid: string): Promise<any> {
    try {
      if (/^\d+$/.test(idOrUuid)) {
        const res = await ms4Client.post(`/dspace/enrich/${idOrUuid}`)
        return res.data
      } else {
        const res = await ms4Client.post(`/dspace/enrich-by-uuid/${idOrUuid}`)
        return res.data
      }
    } catch {
      return await this.detectMissing([{ item_id: idOrUuid, title: 'Ítem DSpace', missing_fields: [] }])
    }
  },

  async enrichBatch(limit: number = 10): Promise<any> {
    const res = await ms4Client.post('/dspace/enrich-next', null, { params: { limit } })
    return res.data
  },

  async markLoaded(id: string): Promise<MetadataProposal> {
    const res = await ms4Client.post<MetadataProposal>(`/v3/proposals/${id}/mark-loaded`)
    return res.data
  },

  async markClosed(id: string): Promise<MetadataProposal> {
    const res = await ms4Client.post<MetadataProposal>(`/v3/proposals/${id}/mark-closed`)
    return res.data
  }
}

