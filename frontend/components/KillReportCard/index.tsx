'use client'
import styles from './KillReportCard.module.css'
import { KillReport } from '@/lib/useSSEMission'

const CRITIC_META: Record<string, { label: string; color: string }> = {
  SECURITY: { label: 'THE BREACH', color: 'var(--cod-red)' },
  PRODUCT: { label: 'THE ADVOCATE', color: '#7B68EE' },
  COMPLIANCE: { label: 'THE REGULATOR', color: 'var(--cod-amber)' },
  SCALABILITY: { label: 'THE ARCHITECT', color: 'var(--cod-cyan)' },
  BUSINESS: { label: 'THE INVESTOR', color: '#FF69B4' },
}

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: 'var(--cod-red)',
  HIGH: 'var(--cod-amber)',
  MEDIUM: 'var(--cod-steel)',
  LOW: 'var(--cod-steel-dim)',
}

const STATUS_META: Record<string, { label: string; className: string }> = {
  OPEN: { label: 'OPEN', className: 'statusOpen' },
  PATCHED: { label: 'PATCHED', className: 'statusPatched' },
  CHALLENGED: { label: 'CHALLENGED', className: 'statusChallenged' },
  DISMISSED: { label: 'DISMISSED', className: 'statusDismissed' },
}

interface KillReportCardProps {
  report: KillReport
  isNew?: boolean
}

export default function KillReportCard({ report, isNew }: KillReportCardProps) {
  const meta = CRITIC_META[report.critic_type] || { label: report.critic_type, color: 'var(--cod-steel)' }
  const severityColor = SEVERITY_COLORS[report.severity] || 'var(--cod-steel)'
  const statusMeta = STATUS_META[report.status] || STATUS_META.OPEN

  const isDismissed = report.status === 'DISMISSED'
  const isPatched = report.status === 'PATCHED'

  return (
    <div
      className={`${styles.card} ${isNew ? styles.cardNew : ''} ${isDismissed ? styles.cardDismissed : ''} ${isPatched ? styles.cardPatched : ''}`}
      style={{ borderLeftColor: severityColor }}
    >
      {/* Kill potential bar */}
      <div className={styles.killBar}>
        <div
          className={styles.killBarFill}
          style={{
            width: `${(report.kill_potential / 10) * 100}%`,
            background: severityColor,
          }}
        ></div>
      </div>

      {/* Header */}
      <div className={styles.header}>
        <span className={styles.criticName} style={{ color: meta.color }}>
          {meta.label}
        </span>
        <span className={styles.severity} style={{ color: severityColor, borderColor: severityColor }}>
          {report.severity}
        </span>
      </div>

      {/* Title */}
      <div className={styles.title}>{report.title}</div>

      {/* Description */}
      <div className={styles.description}>{report.description}</div>

      {/* Status row */}
      <div className={styles.statusRow}>
        <span className={`${styles.statusBadge} ${styles[statusMeta.className]}`}>
          {statusMeta.label}
        </span>
        <span className={styles.killPotential} style={{ color: severityColor }}>
          KILL: {report.kill_potential}/10
        </span>
      </div>

      {/* Patch description */}
      {isPatched && report.patch_description && (
        <div className={styles.patchNote}>
          <span className={styles.patchIcon}>✓</span>
          <span>{report.patch_description}</span>
        </div>
      )}

      {/* Dismiss note */}
      {isDismissed && report.challenge_argument && (
        <div className={styles.dismissNote}>
          <span className={styles.dismissIcon}>↩</span>
          <span>DISMISSED: {report.challenge_argument}</span>
        </div>
      )}
    </div>
  )
}
