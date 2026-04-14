'use client'
import styles from './PhaseTracker.module.css'

const PHASES = [
  { key: 'GENESIS', label: 'GENESIS', desc: 'Blueprint Generation', num: '01' },
  { key: 'CONSTRUCTION', label: 'BUILD', desc: 'MVP Construction', num: '02' },
  { key: 'ATTACK', label: 'ATTACK', desc: 'Critic Assault', num: '03' },
  { key: 'DEFENSE', label: 'DEFENSE', desc: 'Patch Loop', num: '04' },
  { key: 'DEPLOYING', label: 'DEPLOY', desc: 'Ship Survivor', num: '05' },
]

const PHASE_ORDER = ['GENESIS', 'CONSTRUCTION', 'ATTACK', 'DEFENSE', 'DEPLOYING', 'DEPLOYED']

function getPhaseStatus(phaseKey: string, currentPhase: string, missionStatus: string) {
  const currentIdx = PHASE_ORDER.indexOf(currentPhase)
  const phaseIdx = PHASE_ORDER.indexOf(phaseKey)

  if (missionStatus === 'FAILED') {
    
    if (phaseKey === currentPhase) return 'failed'
    
    if (phaseIdx < currentIdx) return 'complete'
    
    return 'pending'
  }

  if (missionStatus === 'DEPLOYED') return 'complete'

  if (phaseIdx < currentIdx) return 'complete'
  if (phaseKey === currentPhase) return 'active'
  return 'pending'
}

interface PhaseTrackerProps {
  currentPhase: string
  status: string
}

export default function PhaseTracker({ currentPhase, status }: PhaseTrackerProps) {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.title}>PIPELINE STATUS</span>
      </div>
      <div className={styles.phases}>
        {PHASES.map((phase, i) => {
          const pStatus = getPhaseStatus(phase.key, currentPhase, status)
          return (
            <div key={phase.key} className={styles.phaseRow}>
              <div className={styles.phaseLeft}>
                <div className={`${styles.indicator} ${styles[pStatus]}`}>
                  {pStatus === 'complete' ? '✓' :
                   pStatus === 'failed' ? '✗' :
                   pStatus === 'active' ? <span className={`${styles.activeDot}`}></span> :
                   phase.num}
                </div>
                {i < PHASES.length - 1 && (
                  <div className={`${styles.connector} ${pStatus === 'complete' ? styles.connectorComplete : ''}`}></div>
                )}
              </div>
              <div className={`${styles.phaseInfo} ${styles[`info_${pStatus}`]}`}>
                <span className={styles.phaseName}>{phase.label}</span>
                <span className={styles.phaseDesc}>{phase.desc}</span>
              </div>
            </div>
          )
        })}
      </div>

      {}
      <div className={styles.agentRoster}>
        <div className={styles.rosterHeader}>
          <span className={styles.rosterTitle}>CRITIC COUNCIL</span>
        </div>
        {[
          { name: 'THE BREACH', type: 'SECURITY', color: 'var(--cod-red)' },
          { name: 'THE ADVOCATE', type: 'PRODUCT', color: '#7B68EE' },
          { name: 'THE REGULATOR', type: 'COMPLIANCE', color: 'var(--cod-amber)' },
          { name: 'THE ARCHITECT', type: 'SCALABILITY', color: 'var(--cod-cyan)' },
          { name: 'THE INVESTOR', type: 'BUSINESS', color: '#FF69B4' },
        ].map((agent) => {
          const isActive = currentPhase === 'ATTACK' || currentPhase === 'DEFENSE'
          return (
            <div key={agent.type} className={styles.agent}>
              <span
                className={`${styles.agentDot} ${isActive ? styles.agentDotActive : ''}`}
                style={{ background: isActive ? agent.color : 'var(--cod-steel-dim)' }}
              ></span>
              <div className={styles.agentInfo}>
                <span className={styles.agentName} style={{ color: isActive ? agent.color : 'var(--cod-steel)' }}>
                  {agent.name}
                </span>
                <span className={styles.agentType}>{agent.type}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
