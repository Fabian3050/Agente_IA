import { ms2Client } from './api'

export interface ClassificationResult {
  code: string
  label: string
  confidence: number
  justification?: string
}

export const classificationService = {
  async getCategories(scheme: 'OCDE' | 'ODS' = 'OCDE') {
    try {
      const res = await ms2Client.get('/categories', { params: { scheme } })
      return res.data
    } catch {
      return []
    }
  },

  async classifyText(title: string, abstractText: string, scheme: 'OCDE' | 'ODS' = 'OCDE'): Promise<ClassificationResult | null> {
    try {
      const endpoint = scheme === 'OCDE' ? '/classify/ocde' : '/classify/ods'
      const res = await ms2Client.post(endpoint, {
        title,
        abstract: abstractText,
      })
      return res.data
    } catch {
      return null
    }
  }
}

