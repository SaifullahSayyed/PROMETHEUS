'use client'
import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'

const BOOT_SEQUENCE = [
  'INITIALIZING NEURAL CORES...',
  'LOADING ADVERSARIAL AGENTS...',
  'ARMING CRITIC COUNCIL...',
  'SYSTEMS ONLINE ●',
]

const EXAMPLE_MISSIONS = [
  {
    label: 'Campus club management platform with events, recruitment, and dues collection',
    demoIndex: 0,
    company: 'ClubFlow',
    icon: '🎓',
  },
  {
    label: 'Freelance invoicing tool with time tracking and automated payment reminders',
    demoIndex: 1,
    company: 'Billdr',
    icon: '⚡',
  },
  {
    label: 'Marketplace for local food producers selling directly to restaurants',
    demoIndex: 2,
    company: 'Cultivar',
    icon: '🌱',
  },
]

const PHASES = [
  { num: '01', name: 'GENESIS',       desc: 'AI blueprint from your idea',          color: 'var(--cod-cyan)'   },
  { num: '02', name: 'CONSTRUCTION',  desc: '4 agents build full MVP codebase',      color: 'var(--cod-green)'  },
  { num: '03', name: 'ASSAULT',       desc: '5 critics attack from every angle',     color: 'var(--cod-red)'    },
  { num: '04', name: 'DEFENSE',       desc: 'Autonomous loop patches every flaw',    color: 'var(--cod-amber)'  },
  { num: '05', name: 'DEPLOY',        desc: 'Survivor ships to a live URL',          color: 'var(--cod-green)'  },
]

const AGENTS = [
  { name: 'THE BREACH',     role: 'SECURITY',    color: 'var(--cod-red)'    },
  { name: 'THE ADVOCATE',   role: 'PRODUCT',     color: 'var(--cod-purple)' },
  { name: 'THE REGULATOR',  role: 'COMPLIANCE',  color: 'var(--cod-amber)'  },
  { name: 'THE ARCHITECT',  role: 'SCALABILITY', color: 'var(--cod-cyan)'   },
  { name: 'THE INVESTOR',   role: 'BUSINESS',    color: 'var(--cod-pink)'   },
]

function ParticleCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animId: number
    let w = canvas.width  = window.innerWidth
    let h = canvas.height = window.innerHeight

    const onResize = () => {
      w = canvas.width  = window.innerWidth
      h = canvas.height = window.innerHeight
    }
    window.addEventListener('resize', onResize)

    const COL = 'rgba(74,255,145,'
    const CYAN = 'rgba(0,229,255,'

    const dots: { x: number; y: number; vx: number; vy: number; r: number; o: number; c: string }[] = []
    for (let i = 0; i < 60; i++) {
      const isCyan = Math.random() < 0.2
      dots.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        r: Math.random() * 1.5 + 0.5,
        o: Math.random() * 0.5 + 0.1,
        c: isCyan ? CYAN : COL,
      })
    }

    const streams: { x: number; y: number; speed: number; len: number; o: number }[] = []
    for (let i = 0; i < 12; i++) {
      streams.push({
        x: Math.random() * w,
        y: Math.random() * h,
        speed: Math.random() * 1 + 0.5,
        len: Math.random() * 80 + 40,
        o: Math.random() * 0.15 + 0.05,
      })
    }

    let t = 0

    function draw() {
      ctx!.clearRect(0, 0, w, h)
      t += 0.008

      const GRID = 80
      for (let x = 0; x <= w; x += GRID) {
        const prog = ((x / w) + t * 0.1) % 1
        const alpha = Math.sin(prog * Math.PI) * 0.06
        ctx!.strokeStyle = `rgba(74,255,145,${alpha})`
        ctx!.lineWidth = 1
        ctx!.beginPath()
        ctx!.moveTo(x, 0)
        ctx!.lineTo(x, h)
        ctx!.stroke()
      }
      for (let y = 0; y <= h; y += GRID) {
        const prog = ((y / h) + t * 0.07) % 1
        const alpha = Math.sin(prog * Math.PI) * 0.06
        ctx!.strokeStyle = `rgba(74,255,145,${alpha})`
        ctx!.lineWidth = 1
        ctx!.beginPath()
        ctx!.moveTo(0, y)
        ctx!.lineTo(w, y)
        ctx!.stroke()
      }

      streams.forEach(s => {
        s.y += s.speed
        if (s.y > h + s.len) { s.y = -s.len; s.x = Math.random() * w }
        const grad = ctx!.createLinearGradient(s.x, s.y - s.len, s.x, s.y)
        grad.addColorStop(0, `rgba(74,255,145,0)`)
        grad.addColorStop(1, `rgba(74,255,145,${s.o})`)
        ctx!.strokeStyle = grad
        ctx!.lineWidth = 1
        ctx!.beginPath()
        ctx!.moveTo(s.x, s.y - s.len)
        ctx!.lineTo(s.x, s.y)
        ctx!.stroke()
      })

      dots.forEach(d => {
        d.x += d.vx; d.y += d.vy
        if (d.x < 0) d.x = w; if (d.x > w) d.x = 0
        if (d.y < 0) d.y = h; if (d.y > h) d.y = 0
        ctx!.beginPath()
        ctx!.arc(d.x, d.y, d.r, 0, Math.PI * 2)
        ctx!.fillStyle = `${d.c}${d.o})`
        ctx!.fill()
      })

      dots.forEach((a, i) => {
        for (let j = i + 1; j < dots.length; j++) {
          const b = dots[j]
          const dx = a.x - b.x, dy = a.y - b.y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 120) {
            const alpha = (1 - dist / 120) * 0.12
            ctx!.strokeStyle = `rgba(74,255,145,${alpha})`
            ctx!.lineWidth = 0.5
            ctx!.beginPath()
            ctx!.moveTo(a.x, a.y)
            ctx!.lineTo(b.x, b.y)
            ctx!.stroke()
          }
        }
      })

      animId = requestAnimationFrame(draw)
    }

    draw()
    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', onResize)
    }
  }, [])

  return <canvas ref={canvasRef} className={styles.particleCanvas} />
}

export default function HomePage() {
  const router = useRouter()
  const [prompt, setPrompt] = useState('')
  const [bootStatus, setBootStatus]   = useState(BOOT_SEQUENCE[0])
  const [bootDone, setBootDone]       = useState(false)
  const [isLoading, setIsLoading]     = useState(false)
  const [loadingDots, setLoadingDots] = useState('')
  const [error, setError]             = useState('')
  const [demoLoadingIndex, setDemoLoadingIndex] = useState<number | null>(null)
  const [activeAgent, setActiveAgent] = useState(0)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    let idx = 0
    const iv = setInterval(() => {
      idx++
      if (idx < BOOT_SEQUENCE.length) {
        setBootStatus(BOOT_SEQUENCE[idx])
      } else {
        clearInterval(iv)
        setBootDone(true)
      }
    }, 700)
    return () => clearInterval(iv)
  }, [])

  useEffect(() => {
    const iv = setInterval(() => setActiveAgent(p => (p + 1) % AGENTS.length), 1800)
    return () => clearInterval(iv)
  }, [])

  useEffect(() => {
    if (!isLoading) return
    let c = 0
    const iv = setInterval(() => { c = (c + 1) % 4; setLoadingDots('.'.repeat(c)) }, 320)
    return () => clearInterval(iv)
  }, [isLoading])

  const handleSubmit = async () => {
    if (!prompt.trim() || isLoading) return
    setIsLoading(true); setError('')
    try {
      const res = await fetch('/api/missions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt.trim() }),
      })
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || 'Failed') }
      const data = await res.json()
      router.push(`/mission/${data.mission_id}`)
    } catch (err: any) {
      setError(err.message || 'Connection failed. Is the backend running?')
      setIsLoading(false)
    }
  }

  const handleDemoLaunch = async (demoIndex: number) => {
    if (isLoading || demoLoadingIndex !== null) return
    setDemoLoadingIndex(demoIndex); setError('')
    try {
      const res = await fetch(`/api/demo/${demoIndex}`, { method: 'POST' })
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || 'Failed') }
      const data = await res.json()
      router.push(`/mission/${data.mission_id}`)
    } catch (err: any) {
      setError(err.message || 'Demo launch failed.')
      setDemoLoadingIndex(null)
    }
  }

  const charCount = prompt.length
  const maxChars  = 500

  return (
    <main className={styles.main}>
      <ParticleCanvas />

      <div className={styles.radialGlow} />
      <div className={styles.radialGlowBlue} />

      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.logoMark}>P</div>
          <div>
            <div className={styles.logo}>PROMETHEUS</div>
            <div className={styles.logoSub}>ADVERSARIAL VENTURE ENGINE</div>
          </div>
        </div>
        <div className={styles.headerCenter}>
          <span className={styles.bootStatus}>{bootStatus}</span>
        </div>
        <div className={styles.headerRight}>
          <div className={`${styles.statusPill} ${bootDone ? styles.statusPillOnline : ''}`}>
            <span className={styles.statusDot} />
            {bootDone ? 'ONLINE' : 'BOOTING'}
          </div>
        </div>
      </header>

      <div className={styles.content}>

        <div className={styles.hero}>
          <div className={styles.heroEyebrow}>
            <span className={styles.eyebrowDot} />
            NEXT-GENERATION AI-POWERED STARTUP FORGE
          </div>

          <h1 className={styles.headline}>
            <span className={styles.headlineTop}>BUILD. ATTACK.</span>
            <span className={styles.headlineBottom}>SURVIVE.</span>
          </h1>

          <p className={styles.subtext}>
            Describe any business idea. PROMETHEUS generates a full company blueprint,
            constructs the MVP codebase, deploys 5 adversarial critic AI agents,
            autonomously patches every flaw, and ships the survivor to a live URL.
          </p>

          <div className={styles.agentStrip}>
            {AGENTS.map((a, i) => (
              <div
                key={a.role}
                className={`${styles.agentChip} ${i === activeAgent ? styles.agentChipActive : ''}`}
                style={{ '--agent-color': a.color } as React.CSSProperties}
              >
                <span className={styles.agentChipDot} />
                {a.name}
              </div>
            ))}
          </div>
        </div>

        <div className={styles.demoSection}>
          <div className={styles.demoLabel}>
            <span className={styles.demoLabelLine} />
            <span>⚡ INSTANT DEMO — ZERO API QUOTA</span>
            <span className={styles.demoLabelLine} />
          </div>
          <div className={styles.demoCards}>
            {EXAMPLE_MISSIONS.map((ex, i) => (
              <button
                key={i}
                className={`${styles.demoCard} ${demoLoadingIndex === i ? styles.demoCardLoading : ''}`}
                onClick={() => handleDemoLaunch(ex.demoIndex)}
                disabled={isLoading || demoLoadingIndex !== null}
                id={`demo-mission-btn-${i}`}
              >
                <div className={styles.demoCardCornerTL} />
                <div className={styles.demoCardCornerBR} />
                <div className={styles.demoCardIcon}>{ex.icon}</div>
                <div className={styles.demoCardRight}>
                  <div className={styles.demoCardCompany}>{ex.company}</div>
                  <div className={styles.demoCardDesc}>{ex.label}</div>
                </div>
                <div className={styles.demoCardAction}>
                  {demoLoadingIndex === i ? (
                    <span className={styles.demoCardLaunching}>LAUNCHING<span className={styles.blink}>_</span></span>
                  ) : (
                    <span className={styles.demoCardArrow}>▶</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className={styles.orDivider}>
          <span className={styles.orLine} />
          <span className={styles.orText}>OR ENTER YOUR OWN MISSION TARGET</span>
          <span className={styles.orLine} />
        </div>

        <div className={styles.inputWrapper}>
          <div className={styles.inputCornerTL} />
          <div className={styles.inputCornerTR} />
          <div className={styles.inputCornerBL} />
          <div className={styles.inputCornerBR} />
          <div className={styles.inputHeader}>
            <span className={styles.inputLabel}>
              <span className={styles.inputLabelDot} />
              TARGET BRIEFING
            </span>
            <span className={`${styles.charCount} ${charCount > maxChars * 0.9 ? styles.charCountWarn : ''}`}>
              {charCount}<span className={styles.charSep}>/</span>{maxChars}
            </span>
          </div>
          <textarea
            ref={textareaRef}
            className={styles.textarea}
            placeholder="Describe the business problem you want PROMETHEUS to solve, build, attack, defend, and deploy..."
            value={prompt}
            onChange={e => setPrompt(e.target.value.slice(0, maxChars))}
            onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit() }}
            rows={4}
            disabled={isLoading}
          />
          <div className={styles.inputFooter}>
            <span className={styles.shortcutHint}>
              <kbd className={styles.kbd}>⌘</kbd>
              <kbd className={styles.kbd}>↵</kbd>
              to launch
            </span>
          </div>
        </div>

        {error && (
          <div className={styles.errorBox}>
            <span className={styles.errorIcon}>⚠</span>
            <span>{error}</span>
          </div>
        )}

        <button
          className={`${styles.launchBtn} ${(!prompt.trim() || isLoading) ? styles.launchBtnDisabled : ''}`}
          onClick={handleSubmit}
          disabled={!prompt.trim() || isLoading}
          id="launch-mission-btn"
        >
          {isLoading ? (
            <>
              <span className={styles.launchBtnSpinner} />
              ESTABLISHING UPLINK{loadingDots}
            </>
          ) : (
            <>
              <span className={styles.launchBtnGlow} />
              INITIATE MISSION
              <span className={styles.launchBtnArrow}>▶▶</span>
            </>
          )}
        </button>

        <div className={styles.pipelineSection}>
          <div className={styles.pipelineTitle}>THREAT PIPELINE</div>
          <div className={styles.pipeline}>
            {PHASES.map((ph, i) => (
              <div key={ph.num} className={styles.pipelineStep}>
                <div className={styles.pipelineNode} style={{ '--phase-color': ph.color } as React.CSSProperties}>
                  <span className={styles.pipelineNum}>{ph.num}</span>
                </div>
                {i < PHASES.length - 1 && (
                  <div className={styles.pipelineArrow}>
                    <div className={styles.pipelineArrowLine} />
                    <span className={styles.pipelineArrowHead}>›</span>
                  </div>
                )}
                <div className={styles.pipelineInfo}>
                  <span className={styles.pipelineName} style={{ color: ph.color }}>{ph.name}</span>
                  <span className={styles.pipelineDesc}>{ph.desc}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      <footer className={styles.footer}>
        <div className={styles.footerLeft}>
          <span className={styles.footerLogo}>PROMETHEUS</span>
          <span className={styles.footerVersion}>v1.0.0</span>
        </div>
        <div className={styles.footerCenter}>
          Gemini 2.0 Flash · LangGraph · FastAPI · Next.js
        </div>
        <div className={styles.footerRight}>
          MISSION COST: <span className={styles.footerCost}>$0.00</span>
        </div>
      </footer>
    </main>
  )
}
