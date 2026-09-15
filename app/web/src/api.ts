import type {
  County,
  CountyFeatureCollection,
  FeatureCollection,
  Group,
  Member,
  PeerComparison,
  SearchHit,
  ServiceRow,
  Spending,
  Tract,
  TractFeatureCollection,
  VolumeMetric,
  VolumeProvider,
} from './types'

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${url}: ${res.status}`)
  return res.json()
}

export const fetchProviders = () => getJson<FeatureCollection>('/api/providers')
export const fetchCounties = () => getJson<County[]>('/api/counties')
export const fetchTracts = () => getJson<Tract[]>('/api/tracts')
export const fetchTractGeo = () => getJson<TractFeatureCollection>('/api/tracts/geojson')
export const fetchCountyGeo = () => getJson<CountyFeatureCollection>('/api/counties/geojson')

export const fetchSpending = () => getJson<Spending[]>('/api/spending')

export const fetchVolume = (metric: VolumeMetric, limit = 50) =>
  getJson<VolumeProvider[]>(`/api/volume?metric=${metric}&limit=${limit}`)
export const fetchProviderServices = (npi: string) =>
  getJson<ServiceRow[]>(`/api/providers/${npi}/services`)

export const fetchGroups = () => getJson<Group[]>('/api/groups')
export const fetchGroupMembers = (groupPacId: string) =>
  getJson<Member[]>(`/api/groups/${groupPacId}/members`)

export const searchProviders = (q: string) =>
  getJson<SearchHit[]>(`/api/providers/search?q=${encodeURIComponent(q)}`)
export const fetchPeers = (npi: string) =>
  getJson<PeerComparison>(`/api/providers/${npi}/peers`)
