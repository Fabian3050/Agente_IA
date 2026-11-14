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
  async listProposals(params?: { state?: ProposalState; item_id?: string; field_name?: string }): Promise<MetadataProposal[]> {
    try {
      const res = await ms4Client.get<MetadataProposal[]>('/v3/proposals', { params })
      return res.data
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

  async markLoaded(id: string): Promise<MetadataProposal> {
    const res = await ms4Client.post<MetadataProposal>(`/v3/proposals/${id}/mark-loaded`)
    return res.data
  },

  async markClosed(id: string): Promise<MetadataProposal> {
    const res = await ms4Client.post<MetadataProposal>(`/v3/proposals/${id}/mark-closed`)
    return res.data
  }
}

