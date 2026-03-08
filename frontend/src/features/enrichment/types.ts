export interface EnrichmentStats {
  total_items: number
  enriched_items: number
  unenriched_items: number
  coverage_pct: number
  by_enricher: EnricherStat[]
}

export interface EnricherStat {
  name: string
  total_runs: number
  items_enriched: number
  last_run: string | null
  avg_duration_secs: number
}

export interface EnrichmentRun {
  id: number
  enricher_name: string
  items_processed: number
  items_enriched: number
  items_skipped: number
  items_failed: number
  started_at: string | null
  completed_at: string | null
  status: string
  error_message: string | null
  trigger: string
}

export interface EnrichmentRunsResponse {
  runs: EnrichmentRun[]
  count: number
}

export interface TriggerEnrichmentResponse {
  enrichment_run_id: number
  items_queued: number
}
