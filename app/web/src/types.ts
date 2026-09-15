export interface ProviderProps {
  npi: string
  provider_name: string | null
  provider_category: string
  taxonomy_label: string | null
  is_organization: boolean
  city: string | null
  location_source: string
  in_mua_tract: boolean
}

export interface ProviderFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] } // [lon, lat]
  properties: ProviderProps
}

export interface FeatureCollection {
  type: 'FeatureCollection'
  features: ProviderFeature[]
}

export interface County {
  county_fips: string
  county_name: string | null
  population: number
  pc_provider_count: number
  physician_count: number
  app_provider_count: number
  pc_per_10k: number
  hpsa_population_count: number
  correctional_hpsa_count: number
  fqhc_hpsa_count: number
  hpsa_population_max_score: number | null
  mua_tract_count: number
  mua_designation_count: number
}

export interface Tract {
  tract_fips: string
  county_fips: string
  county_name: string | null
  is_mua: boolean
  is_mua_tract: boolean
  imu_score: number | null
  pc_provider_count: number
  is_underserved: boolean
}

export interface TractProps {
  tract_fips: string
  county_name: string | null
  is_underserved: boolean
  is_mua: boolean
  imu_score: number | null
  pc_provider_count: number
}

export interface TractFeature {
  type: 'Feature'
  geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon
  properties: TractProps
}

export interface TractFeatureCollection {
  type: 'FeatureCollection'
  features: TractFeature[]
}

export interface CountyProps {
  county_fips: string
  county_name: string | null
  pc_per_10k: number
  worst_imu: number | null
  is_underserved: boolean
}

export interface CountyFeature {
  type: 'Feature'
  geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon
  properties: CountyProps
}

export interface CountyFeatureCollection {
  type: 'FeatureCollection'
  features: CountyFeature[]
}

export interface Spending {
  provider_category: string
  provider_count: number
  total_services: number
  total_medicare_paid: number | null
  total_medicare_allowed: number | null
  medical_paid: number | null
  drug_paid: number | null
  pct_of_paid: number | null
}

export type VolumeMetric = 'total_services' | 'total_beneficiaries' | 'medical_medicare_paid'

export interface VolumeProvider {
  npi: string
  provider_name: string | null
  provider_category: string
  taxonomy_label: string | null
  city: string | null
  total_services: number
  total_beneficiaries: number
  total_medicare_paid: number | null
  medical_medicare_paid: number | null
  drug_medicare_paid: number | null
}

export interface ServiceRow {
  hcpcs_cd: string
  hcpcs_desc: string | null
  hcpcs_drug_ind: string | null
  place_of_srvc: string | null
  services: number
  beneficiaries: number
  avg_medicare_paid: number | null
  total_medicare_paid: number | null
}

export interface Group {
  group_pac_id: string
  group_name: string | null
  group_state: string | null
  pc_member_count: number
  physician_count: number
  app_provider_count: number
}

export interface Member {
  npi: string
  provider_name: string | null
  provider_category: string
  taxonomy_label: string | null
  city: string | null
}

export interface SearchHit {
  npi: string
  provider_name: string | null
  provider_category: string
  taxonomy_label: string | null
  city: string | null
}

export interface PeerComparison {
  npi: string
  provider_name: string | null
  provider_category: string
  primary_taxonomy: string | null
  taxonomy_label: string | null
  city: string | null
  total_services: number
  total_beneficiaries: number
  medical_medicare_paid: number | null
  peer_group_size: number
  pct_services: number | null
  pct_beneficiaries: number | null
  pct_medical_paid: number | null
  low_confidence: boolean
}
