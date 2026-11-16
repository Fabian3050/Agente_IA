export type Page =
  | 'dashboard'
  | 'monitoreo'
  | 'recuperacion'
  | 'validacion'
  | 'aprobacion'
  | 'auditoria'
  | 'reportes'
  | 'usuarios'
  | 'configuracion'
  | 'perfil'

export type ProposalState =
  | 'Detectada'
  | 'En recuperación'
  | 'Coincidencia dudosa'
  | 'En clasificación'
  | 'En reintento'
  | 'En revisión'
  | 'Invalidada'
  | 'Rechazada'
  | 'Aprobada'
  | 'Exportada'
  | 'Cargada'
  | 'Cerrada'

export interface User {
  id: string
  sub?: string
  username?: string
  name?: string
  lastName?: string
  email: string
  role: 'Administrador' | 'Curador' | 'Auditor' | 'Admin' | 'Curador_VRIIC' | 'Academico' | string
  fullName: string
  avatarUrl?: string
  isActive: boolean
  orcid?: string
  dspacePersonId?: string
  createdAt?: string
}

export interface MonitoreoRecord {
  id: string
  title: string
  campo: string
  fecha: string
  prioridad: 'Alta' | 'Media' | 'Baja'
  estado: ProposalState | string
  completitud: number
  completitudPre: number
  coleccion: string
  comunidad: string
  autor: string
  doi: string
  last_modified_dspace?: string
  abstractEnriquecido?: string
  palabrasClave?: string[]
  fuente?: string
  areaOcde?: any
  areaOds?: any
}

export interface MetadataProposal {
  id: string
  item_id: string
  doi?: string
  field_name: string
  proposed_value: string
  source: string
  confidence_score: number
  state: ProposalState
  curator_id?: string
  curator_notes?: string
  last_modified_dspace?: string
  created_at?: string
  updated_at?: string
  // Display helpers
  title?: string
  author?: string
}

export interface ApiSource {
  name: string
  status: 'Conectado' | 'Degradado' | 'Desconectado'
  latency: string
  queries: number
  recovered: number
  availability: number
  lastQuery: string
}

export interface AuditLogEntry {
  id: string | number
  timestamp: string
  user: string
  role: string
  action: string
  item_id: string
  field: string
  prev_value: string
  new_value: string
  confidence?: number
  state: string
}

export interface CandidateMatch {
  source: string
  title: string
  authors: string[]
  year: number | string
  doi: string
  fuzzy_score: number
  abstract?: string
  keywords?: string[]
  ocde?: string
  ods?: string
}

export interface ServiceStatus {
  name: string
  service: string
  port: number
  url: string
  status: 'online' | 'offline' | 'checking'
  version?: string
}
