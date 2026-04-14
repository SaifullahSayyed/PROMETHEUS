'use client'
import { useState, useEffect } from 'react'
import styles from './DeployButton.module.css'

const DEPLOYING_MESSAGES = [
  'ESTABLISHING UPLINK...',
  'CONTAINERIZING APPLICATION...',
  'DEPLOYING TO SECTOR...',
  'UPLINK ESTABLISHED...',
]

interface DeployButtonProps {
  score: number
  deployUrl?: string
  onDeploy: () => void
  isDeploying: boolean
  isFailed?: boolean
}

export default function DeployButton({ score, deployUrl, onDeploy, isDeploying, isFailed }: DeployButtonProps) {
  
  const [msgIdx, setMsgIdx] = useState(0)

  useEffect(() => {
    if (!isDeploying) return
    const interval = setInterval(() => {
      setMsgIdx(prev => (prev + 1) % DEPLOYING_MESSAGES.length)
    }, 1000)
    return () => clearInterval(interval)
  }, [isDeploying])

  if (isFailed) {
    return (
      <div className={styles.failedContainer}>
        <span className={styles.failedIcon}>✗</span>
        <div>
          <div className={styles.failedTitle}>MISSION ABORTED</div>
          <div className={styles.failedHint}>
            Check your <code>GEMINI_API_KEY</code> in <code>backend/.env</code>. If hitting rate limits (429), wait 60 seconds and launch a new mission.
          </div>
        </div>
      </div>
    )
  }

  if (deployUrl) {
    return (
      <div className={styles.successContainer}>
        <div className={styles.successHeader}>
          <span className={styles.successIcon}>●</span>
          <span className={styles.successTitle}>OBJECTIVE SECURED</span>
        </div>
        <div className={styles.urlContainer}>
          <span className={styles.urlLabel}>DEPLOYED ASSET:</span>
          <a
            href={deployUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.deployUrl}
            id="deploy-url-link"
          >
            {deployUrl}
          </a>
        </div>
        <p className={styles.urlHint}>↗ CLICK TO ACCESS DEPLOYED APPLICATION</p>
      </div>
    )
  }

  if (isDeploying) {
    return (
      <div className={styles.deployingContainer}>
        <div className={styles.deployingSpinner}></div>
        <span className={styles.deployingText}>{DEPLOYING_MESSAGES[msgIdx]}</span>
      </div>
    )
  }

  if (score >= 100) {
    return (
      <button
        className={styles.readyBtn}
        onClick={onDeploy}
        id="deploy-survivor-btn"
      >
        ▶ DEPLOY SURVIVOR
      </button>
    )
  }

  return (
    <div className={styles.lockedContainer}>
      <div className={styles.lockedBar}>
        <div
          className={styles.lockedBarFill}
          style={{ width: `${score}%` }}
        ></div>
      </div>
      <span className={styles.lockedText}>DEFENSE LOOP IN PROGRESS... {score.toFixed(0)}%</span>
    </div>
  )
}
