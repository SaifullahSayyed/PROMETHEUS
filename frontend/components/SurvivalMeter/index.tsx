'use client'
import { useState, useEffect, useRef } from 'react'
import styles from './SurvivalMeter.module.css'

interface SurvivalMeterProps {
  score: number
  resolved: number
  total: number
  status: string
}

function getScoreColor(score: number): string {
  if (score <= 40) return 'var(--cod-red)'
  if (score <= 70) return 'var(--cod-amber)'
  return 'var(--cod-green)'
}

function useAnimatedScore(targetScore: number) {
  const [displayScore, setDisplayScore] = useState(targetScore)
  const prevScore = useRef(targetScore)
  const rafRef = useRef<number>()

  useEffect(() => {
    const start = prevScore.current
    const end = targetScore
    const duration = 800
    const startTime = performance.now()

    if (rafRef.current) cancelAnimationFrame(rafRef.current)

    function animate(now: number) {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = start + (end - start) * eased
      setDisplayScore(Math.round(current * 10) / 10)

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate)
      } else {
        prevScore.current = end
      }
    }

    rafRef.current = requestAnimationFrame(animate)
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [targetScore])

  return displayScore
}

export default function SurvivalMeter({ score, resolved, total, status }: SurvivalMeterProps) {
  const displayScore = useAnimatedScore(score)
  const color = getScoreColor(displayScore)
  const criticalOpen = total - resolved

  const isComplete = status === 'DEPLOYED' || score >= 100

  return (
    <div className={`${styles.container} ${isComplete ? styles.containerComplete : ''}`}>
      <div className={styles.label}>VENTURE SURVIVAL RATING</div>

      {isComplete && (
        <div className={styles.accomplishedBanner}>
          ★ MISSION ACCOMPLISHED ★
        </div>
      )}

      <div className={styles.scoreRow}>
        <span
          className={styles.scoreNum}
          style={{ color }}
        >
          {displayScore.toFixed(0)}
        </span>
        <span className={styles.scorePercent} style={{ color }}>%</span>
      </div>

      {/* Progress bar */}
      <div className={styles.barTrack}>
        <div
          className={styles.barFill}
          style={{
            width: `${Math.min(displayScore, 100)}%`,
            background: color,
            boxShadow: `0 0 12px ${color}40`,
          }}
        ></div>
      </div>

      {/* Stats */}
      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={styles.statValue}>{resolved}</span>
          <span className={styles.statSep}>/</span>
          <span className={styles.statValue}>{total}</span>
          <span className={styles.statLabel}>THREATS RESOLVED</span>
        </div>
        {criticalOpen > 0 && !isComplete && (
          <div className={`${styles.criticalWarning}`}>
            <span className={styles.criticalDot}></span>
            {criticalOpen} CRITICAL OPEN
          </div>
        )}
      </div>

      {/* Score meter segments */}
      <div className={styles.segments}>
        {['CRITICAL', 'DANGER', 'CAUTION', 'STABLE', 'SECURE'].map((zone, i) => {
          const threshold = i * 20
          const isActive = displayScore >= threshold
          const colors = ['var(--cod-red)', 'var(--cod-red)', 'var(--cod-amber)', 'var(--cod-amber)', 'var(--cod-green)']
          return (
            <div
              key={zone}
              className={`${styles.segment} ${isActive ? styles.segmentActive : ''}`}
              style={isActive ? { background: colors[i] } : {}}
            >
              <span className={styles.segmentLabel}>{zone}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
