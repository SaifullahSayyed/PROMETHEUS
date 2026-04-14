'use client'
import { useEffect, useRef } from 'react'
import styles from './CombatLog.module.css'
import { LogEntry } from '@/lib/useSSEMission'

const AGENT_COLORS: Record<string, { bg: string; text: string }> = {
  'BUILDER': { bg: 'var(--cod-green)', text: '#000' },
  'THE BREACH': { bg: 'var(--cod-red)', text: '#fff' },
  'SECURITY': { bg: 'var(--cod-red)', text: '#fff' },
  'THE ADVOCATE': { bg: '#7B68EE', text: '#fff' },
  'PRODUCT': { bg: '#7B68EE', text: '#fff' },
  'THE REGULATOR': { bg: 'var(--cod-amber)', text: '#000' },
  'COMPLIANCE': { bg: 'var(--cod-amber)', text: '#000' },
  'THE ARCHITECT': { bg: 'var(--cod-cyan)', text: '#000' },
  'SCALABILITY': { bg: 'var(--cod-cyan)', text: '#000' },
  'THE INVESTOR': { bg: '#FF69B4', text: '#000' },
  'BUSINESS': { bg: '#FF69B4', text: '#000' },
  'DEFENDER': { bg: 'var(--cod-green-dim)', text: 'var(--cod-green)' },
  'ARBITER': { bg: '#4A4F5E', text: '#E8EAF0' },
  'SYSTEM': { bg: 'var(--cod-surface)', text: 'var(--cod-steel)' },
  'DEPLOYER': { bg: 'var(--cod-surface)', text: 'var(--cod-cyan)' },
}

const LEVEL_COLORS: Record<string, string> = {
  INFO: 'var(--cod-steel)',
  WARNING: 'var(--cod-amber)',
  CRITICAL: 'var(--cod-red)',
  SUCCESS: 'var(--cod-green)',
}

interface CombatLogProps {
  logs: LogEntry[]
}

export default function CombatLog({ logs }: CombatLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs.length])

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.title}>
          COMBAT LOG <span className={styles.cursor}>▌</span>
        </span>
        <span className={styles.liveIndicator}>
          <span className={styles.liveDot}></span>
          LIVE
        </span>
      </div>

      <div className={styles.logArea}>
        {logs.length === 0 && (
          <div className={styles.emptyState}>
            <span className={styles.emptyText}>Awaiting pipeline activation...</span>
          </div>
        )}
        {logs.map((log, i) => {
          const agentStyle = AGENT_COLORS[log.agent] || AGENT_COLORS['SYSTEM']
          const levelColor = LEVEL_COLORS[log.level] || LEVEL_COLORS.INFO
          return (
            <div key={i} className={styles.logEntry}>
              <span className={styles.timestamp}>{log.timestamp}</span>
              <span
                className={styles.agentBadge}
                style={{ background: agentStyle.bg, color: agentStyle.text }}
              >
                {log.agent}
              </span>
              <span className={styles.message} style={{ color: levelColor }}>
                {log.message}
              </span>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
