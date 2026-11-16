import { ms1Client } from './api'
import type { ApiSource, CandidateMatch } from '../types'

export const retrievalService = {
  async getSources(): Promise<ApiSource[]> {
    try {
      const res = await ms1Client.get<any[]>('/sources')
      return res.data.map((s) => ({
        name: s.name || s.api_name || 'API',
        status: s.status || 'Conectado',
        latency: s.latency ? `${s.latency}ms` : '120ms',
        queries: s.queries_total || s.queries || 0,
        recovered: s.success_total || s.recovered || 0,
        availability: s.availability_pct || 99.8,
        lastQuery: s.last_query || 'Reciente',
      }))
    } catch {
      return []
    }
  },

  async retrieveByDoiOrTitle(itemId: string, doi?: string, title?: string): Promise<{
    outcome: string
    max_score: number
    best_source?: string
    consolidated?: any
    candidates?: CandidateMatch[]
  }> {
    const res = await ms1Client.post('/retrieve', {
      item_id: itemId,
      doi: doi || '',
      title: title || ''
    })
    return res.data
  }
}

