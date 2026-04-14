'use client'
import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { useSSEMission } from '@/lib/useSSEMission'
import PhaseTracker from '@/components/PhaseTracker'
import SurvivalMeter from '@/components/SurvivalMeter'
import CombatLog from '@/components/CombatLog'
import KillReportCard from '@/components/KillReportCard'
import DeployButton from '@/components/DeployButton'
import styles from './mission.module.css'

function useElapsedTime(createdAt?: string) {
  const [elapsed, setElapsed] = useState('00:00:00')

  useEffect(() => {
    if (!createdAt) return
    const startTime = new Date(createdAt).getTime()

    const update = () => {
      const diff = Math.floor((Date.now() - startTime) / 1000)
      const h = Math.floor(diff / 3600).toString().padStart(2, '0')
      const m = Math.floor((diff % 3600) / 60).toString().padStart(2, '0')
      const s = (diff % 60).toString().padStart(2, '0')
      setElapsed(`${h}:${m}:${s}`)
    }

    update()
    const interval = setInterval(update, 1000)
    return () => clearInterval(interval)
  }, [createdAt])

  return elapsed
}

export default function MissionPage() {
  const params = useParams()
  const missionId = params.id as string
  const { mission, isConnected, error } = useSSEMission(missionId)
  const elapsed = useElapsedTime(mission?.created_at)
  const [isDeploying, setIsDeploying] = useState(false)
  const [contractExpanded, setContractExpanded] = useState(false)
  const [seenReports, setSeenReports] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (!mission?.kill_reports) return
    const newIds = mission.kill_reports.map(r => r.id)
    setSeenReports(prev => new Set([...prev, ...newIds]))
  }, [mission?.kill_reports?.length])

  const handleDeploy = () => {
    setIsDeploying(true)
  }

  if (!mission) {
    return (
      <div className={styles.loading}>
        <div className={styles.loadingInner}>
          <div className={styles.loadingSpinner}></div>
          <div className={styles.loadingText}>
            ESTABLISHING UPLINK<span className={styles.blink}>_</span>
          </div>
          <div className={styles.loadingMissionId}>{missionId?.slice(0, 8).toUpperCase()}</div>
        </div>
      </div>
    )
  }

  const sortedReports = [...(mission.kill_reports || [])].sort((a, b) => {
    const severityOrder: Record<string, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 }
    const so = (severityOrder[a.severity] ?? 4) - (severityOrder[b.severity] ?? 4)
    if (so !== 0) return so
    return b.kill_potential - a.kill_potential
  })

  const resolvedCount = mission.kill_reports.filter(r => r.status === 'PATCHED' || r.status === 'DISMISSED').length

  return (
    <div className={styles.root}>
      {}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.headerLogo}>PROMETHEUS</span>
          <span className={styles.headerSep}>|</span>
          <span className={styles.headerStatus} data-status={mission.status}>
            {mission.status}
          </span>
        </div>
        <div className={styles.headerCenter}>
          <span className={styles.missionId}>MISSION: {missionId.slice(0, 8).toUpperCase()}</span>
        </div>
        <div className={styles.headerRight}>
          <span className={`${styles.connDot} ${isConnected ? styles.connDotActive : ''}`}></span>
          <span className={styles.elapsed}>{elapsed}</span>
        </div>
      </header>

      {}
      <div className={styles.warRoom}>
        {}
        <aside className={styles.leftCol}>
          <PhaseTracker currentPhase={mission.current_phase} status={mission.status} />
        </aside>

        {}
        <main className={styles.centerCol}>
          {}
          {mission.contract?.company_name && (
            <div className={styles.companyReveal}>
              <span className={styles.companyLabel}>TARGET IDENTIFIED</span>
              <div className={styles.companyName}>{mission.contract.company_name}</div>
              {mission.contract.tagline && (
                <div className={styles.companyTagline}>{mission.contract.tagline}</div>
              )}
            </div>
          )}

          {}
          <SurvivalMeter
            score={mission.survival_score}
            resolved={resolvedCount}
            total={mission.kill_reports.length}
            status={mission.status}
          />

          {}
          <CombatLog logs={mission.combat_log || []} />

          {}
          <DeployButton
            score={mission.survival_score}
            deployUrl={mission.deploy_url}
            onDeploy={handleDeploy}
            isDeploying={isDeploying || mission.status === 'DEPLOYING'}
            isFailed={mission.status === 'FAILED'}
          />

          {}
          {mission.status === 'FAILED' && mission.error && (
            <div className={styles.errorBox}>
              <span className={styles.errorLabel}>MISSION FAILED</span>
              <span className={styles.errorMsg}>{mission.error}</span>
            </div>
          )}
        </main>

        {}
        <aside className={styles.rightCol}>
          {}
          <div className={styles.rightSection}>
            <div className={styles.sectionHeader}>
              <span className={styles.sectionTitle}>THREAT INTELLIGENCE</span>
              <span className={styles.sectionCount}>
                {mission.kill_reports.length > 0 && (
                  `${resolvedCount}/${mission.kill_reports.length} RESOLVED`
                )}
              </span>
            </div>
            <div className={styles.killFeed}>
              {mission.kill_reports.length === 0 && (
                <div className={styles.emptyFeed}>
                  <span className={styles.emptyText}>
                    {mission.status === 'ATTACK' ? 'Critic council analyzing...' : 'Awaiting attack phase...'}
                  </span>
                </div>
              )}
              {sortedReports.map((report, i) => (
                <KillReportCard
                  key={report.id}
                  report={report}
                  isNew={!seenReports.has(report.id)}
                />
              ))}
            </div>
          </div>

          {}
          {mission.contract && (
            <div className={styles.contractSection}>
              <button
                className={styles.contractHeader}
                onClick={() => setContractExpanded(prev => !prev)}
              >
                <span className={styles.sectionTitle}>MISSION CONTRACT</span>
                <span className={styles.contractVersion}>
                  v{mission.contract ? '1' : '0'} {contractExpanded ? '▲' : '▼'}
                </span>
              </button>

              {contractExpanded && mission.contract && (
                <div className={styles.contractBody}>
                  <pre className={styles.contractCode}>
{`COMPANY:    ${mission.contract.company_name}
TAGLINE:    ${mission.contract.tagline || 'N/A'}

STACK:
  Frontend: ${mission.contract.tech_stack?.frontend || 'N/A'}
  Backend:  ${mission.contract.tech_stack?.backend || 'N/A'}
  Database: ${mission.contract.tech_stack?.database || 'N/A'}

TABLES:     ${mission.contract.database_schema?.length || 0} tables
ENDPOINTS:  ${mission.contract.api_endpoints?.length || 0} endpoints
FEATURES:   ${mission.contract.core_features?.length || 0} features

PRICING:
${(mission.contract.pricing_tiers || []).map(p =>
  `  ${p.name}: $${p.price_monthly_usd}/mo`
).join('\n')}`}
                  </pre>
                </div>
              )}
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}
