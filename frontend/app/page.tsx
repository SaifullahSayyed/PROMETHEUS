'use client'
import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'

const BOOT_SEQUENCE = [
  'INITIALIZING...',
  'LOADING AGENTS...',
  'ARMING CRITICS...',
  'SYSTEMS ONLINE ●',
]

const EXAMPLE_MISSIONS = [
  'A platform for campus clubs to manage events, recruit members, and collect dues online',
  'A freelance invoicing tool with time tracking and automated payment reminders via email and SMS',
  'A marketplace for local food producers to sell directly to restaurants with order management',
]

const PHASES = [
  { num: '01', name: 'GENESIS', desc: 'Generate company blueprint from your idea' },
  { num: '02', name: 'CONSTRUCTION', desc: '4 AI agents build the full MVP codebase' },
  { num: '03', name: 'ATTACK', desc: '5 specialized critics assault from every angle' },
  { num: '04', name: 'DEFENSE', desc: 'Autonomous loop patches every vulnerability' },
  { num: '05', name: 'DEPLOY', desc: 'Survivor ships to a live URL' },
]

export default function HomePage() {
  const router = useRouter()
  const [prompt, setPrompt] = useState('')
  const [bootStatus, setBootStatus] = useState(BOOT_SEQUENCE[0])
  const [isLoading, setIsLoading] = useState(false)
  const [loadingDots, setLoadingDots] = useState('')
  const [error, setError] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Boot sequence animation
  useEffect(() => {
    let idx = 0
    const interval = setInterval(() => {
      idx++
      if (idx < BOOT_SEQUENCE.length) {
        setBootStatus(BOOT_SEQUENCE[idx])
      } else {
        clearInterval(interval)
      }
    }, 800)
    return () => clearInterval(interval)
  }, [])

  // Loading dots animation
  useEffect(() => {
    if (!isLoading) return
    let count = 0
    const interval = setInterval(() => {
      count = (count + 1) % 4
      setLoadingDots('.'.repeat(count))
    }, 400)
    return () => clearInterval(interval)
  }, [isLoading])

  const handleSubmit = async () => {
    if (!prompt.trim() || isLoading) return
    setIsLoading(true)
    setError('')

    try {
      const res = await fetch('/api/missions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt.trim() }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to create mission')
      }

      const data = await res.json()
      router.push(`/mission/${data.mission_id}`)
    } catch (err: any) {
      setError(err.message || 'Connection failed. Is the backend running?')
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit()
    }
  }

  const charCount = prompt.length
  const maxChars = 500

  return (
    <main className={styles.main}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.logo}>PROMETHEUS</span>
          <span className={styles.version}>v1.0.0</span>
        </div>
        <div className={styles.headerCenter}>
          <span className={styles.bootStatus}>{bootStatus}</span>
        </div>
        <div className={styles.headerRight}>
          <span className={`${styles.onlineDot} ${bootStatus.includes('ONLINE') ? styles.online : ''}`}></span>
          <span className={styles.onlineText}>
            {bootStatus.includes('ONLINE') ? 'SYSTEMS ONLINE' : bootStatus}
          </span>
        </div>
      </header>

      {/* Content */}
      <div className={styles.content}>
        {/* Badges */}
        <div className={styles.badges}>
          <span className={styles.badge}>
            <span className={styles.badgeDot} style={{ background: 'var(--cod-red)' }}></span>
            5 CRITIC AGENTS ARMED
          </span>
          <span className={styles.badge}>
            <span className={styles.badgeDot} style={{ background: 'var(--cod-amber)' }}></span>
            AUTONOMOUS DEFENSE LOOP
          </span>
          <span className={styles.badge}>
            <span className={styles.badgeDot} style={{ background: 'var(--cod-green)' }}></span>
            LIVE DEPLOY ON SURVIVE
          </span>
        </div>

        {/* Headline */}
        <h1 className={styles.headline}>DEFINE YOUR TARGET</h1>
        <p className={styles.description}>
          Enter a plain-English business problem. PROMETHEUS generates a complete company,
          builds it with AI agents, unleashes 5 adversarial critics, patches every flaw,
          and deploys the survivor.
        </p>

        {/* Examples */}
        <div className={styles.examples}>
          <span className={styles.examplesLabel}>EXAMPLE MISSIONS:</span>
          <div className={styles.examplePills}>
            {EXAMPLE_MISSIONS.map((ex, i) => (
              <button
                key={i}
                className={styles.examplePill}
                onClick={() => {
                  setPrompt(ex)
                  textareaRef.current?.focus()
                }}
              >
                {ex.slice(0, 55)}...
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <div className={styles.inputGroup}>
          <div className={styles.inputHeader}>
            <label className={styles.inputLabel}>TARGET DESCRIPTION</label>
            <span className={`${styles.charCount} ${charCount > maxChars * 0.9 ? styles.charCountWarn : ''}`}>
              {charCount} / {maxChars}
            </span>
          </div>
          <textarea
            ref={textareaRef}
            className={styles.textarea}
            placeholder="Describe the business problem you want PROMETHEUS to solve and build..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value.slice(0, maxChars))}
            onKeyDown={handleKeyDown}
            rows={5}
            disabled={isLoading}
          />
          <div className={styles.inputFooter}>
            <span className={styles.hint}>⌘ + ENTER to launch</span>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className={styles.errorBox}>
            <span className={styles.errorIcon}>⚠</span>
            <span>{error}</span>
          </div>
        )}

        {/* Launch button */}
        <button
          className={`${styles.launchBtn} ${!prompt.trim() || isLoading ? styles.launchBtnDisabled : ''}`}
          onClick={handleSubmit}
          disabled={!prompt.trim() || isLoading}
          id="launch-mission-btn"
        >
          {isLoading ? (
            <span>ESTABLISHING UPLINK{loadingDots}</span>
          ) : (
            <span>INITIATE MISSION ▶</span>
          )}
        </button>

        {/* Phase tracker */}
        <div className={styles.phaseSection}>
          <div className={styles.phaseSectionHeader}>
            <span className={styles.phaseSectionTitle}>THREAT ASSESSMENT PIPELINE</span>
          </div>
          <div className={styles.phases}>
            {PHASES.map((phase, i) => (
              <div key={phase.num} className={styles.phase}>
                <div className={styles.phaseNumWrapper}>
                  <span className={styles.phaseNum}>{phase.num}</span>
                  {i < PHASES.length - 1 && <div className={styles.phaseConnector}></div>}
                </div>
                <div className={styles.phaseInfo}>
                  <span className={styles.phaseName}>{phase.name}</span>
                  <span className={styles.phaseDesc}>{phase.desc}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className={styles.footer}>
        <span>PROMETHEUS ADVERSARIAL VENTURE ENGINE</span>
        <span className={styles.footerSep}>|</span>
        <span>Powered by Claude claude-sonnet-4-6 · LangGraph · FastAPI · Next.js</span>
        <span className={styles.footerSep}>|</span>
        <span>COST: $0.00</span>
      </footer>
    </main>
  )
}
