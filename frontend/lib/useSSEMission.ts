'use client'
import { useState, useEffect, useRef } from 'react'

export interface LogEntry {
  timestamp: string
  agent: string
  message: string
  level: 'INFO' | 'WARNING' | 'CRITICAL' | 'SUCCESS'
}

export interface KillReport {
  id: string
  critic_type: 'SECURITY' | 'PRODUCT' | 'COMPLIANCE' | 'SCALABILITY' | 'BUSINESS'
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  title: string
  description: string
  kill_potential: number
  status: 'OPEN' | 'PATCHED' | 'CHALLENGED' | 'DISMISSED'
  patch_description?: string
  challenge_argument?: string
  arbiter_verdict?: string
  affected_layer: string
  suggested_fix: string
}

export interface MissionState {
  id: string
  status: string
  current_phase: string
  survival_score: number
  combat_log: LogEntry[]
  kill_reports: KillReport[]
  deploy_url?: string
  contract?: {
    company_name: string
    tagline: string
    tech_stack?: {
      frontend: string
      backend: string
      database: string
    }
    pricing_tiers: Array<{ name: string; price_monthly_usd: number }>
    core_features?: Array<{ name: string; description: string; priority: string }>
    api_endpoints?: Array<{ method: string; path: string }>
    database_schema?: Array<{ name: string }>
  }
  error?: string
}

export function useSSEMission(missionId: string) {
  const [mission, setMission] = useState<MissionState | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    if (!missionId) return

    const es = new EventSource(`${API_BASE}/api/missions/${missionId}/stream`)
    eventSourceRef.current = es

    es.onopen = () => {
      setIsConnected(true)
    }

    es.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data)

        if (parsed.type === 'init') {
          setMission(parsed.data)
          return
        }
        if (parsed.type === 'ping') return
        if (parsed.type === 'complete') {
          setIsConnected(false)
          return
        }

        setMission((prev) => {
          if (!prev) return prev
          const updated = { ...prev }

          switch (parsed.type) {
            case 'phase_change': {
              updated.current_phase = parsed.data.phase
              if (parsed.data.phase === 'GENESIS') updated.status = 'GENESIS'
              if (parsed.data.phase === 'CONSTRUCTION') updated.status = 'CONSTRUCTION'
              if (parsed.data.phase === 'ATTACK') updated.status = 'ATTACK'
              if (parsed.data.phase === 'DEFENSE') updated.status = 'DEFENSE'
              if (parsed.data.phase === 'DEPLOYING') updated.status = 'DEPLOYING'
              if (parsed.data.company_name) {
                updated.contract = updated.contract
                  ? { ...updated.contract, company_name: parsed.data.company_name, tagline: parsed.data.tagline || updated.contract.tagline }
                  : { company_name: parsed.data.company_name, tagline: parsed.data.tagline || '', pricing_tiers: [] }
              }
              break
            }
            case 'log_entry': {
              const newLog: LogEntry = {
                timestamp: parsed.data.timestamp || new Date().toLocaleTimeString('en-US', { hour12: false }),
                agent: parsed.data.agent || 'SYSTEM',
                message: parsed.data.message || '',
                level: parsed.data.level || 'INFO',
              }
              updated.combat_log = [...(prev.combat_log || []), newLog].slice(-150)
              break
            }
            case 'kill_report': {
              const reportData = parsed.data as KillReport
              const exists = (prev.kill_reports || []).find((r) => r.id === reportData.id)
              if (exists) {
                updated.kill_reports = prev.kill_reports.map((r) =>
                  r.id === reportData.id ? reportData : r
                )
              } else {
                updated.kill_reports = [...(prev.kill_reports || []), reportData]
              }
              break
            }
            case 'score_update': {
              updated.survival_score = parsed.data.score
              break
            }
            case 'deploy_complete': {
              updated.deploy_url = parsed.data.url
              updated.status = 'DEPLOYED'
              updated.survival_score = 100
              break
            }
            case 'error': {
              updated.status = 'FAILED'
              updated.error = parsed.data.message
              setError(parsed.data.message)
              break
            }
          }
          return updated
        })
      } catch (e) {
        console.error('SSE parse error:', e)
      }
    }

    es.onerror = () => {
      setIsConnected(false)
    }

    return () => {
      es.close()
      setIsConnected(false)
    }
  }, [missionId, API_BASE])

  return { mission, isConnected, error }
}
