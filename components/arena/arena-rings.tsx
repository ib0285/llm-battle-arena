import styles from './arena.module.css'

const CX = 380
const CY = 315

const dotAngles = [20, 65, 110, 160, 200, 245, 290, 335]

export function ArenaRings() {
  return (
    <svg className={styles.rings} viewBox="0 0 760 680" aria-hidden="true">
      <defs>
        <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#3a1f7a" stopOpacity="0.55" />
          <stop offset="45%" stopColor="#24124f" stopOpacity="0.4" />
          <stop offset="75%" stopColor="#120a28" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#07070c" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="coreFill" cx="50%" cy="45%" r="55%">
          <stop offset="0%" stopColor="#1b1430" />
          <stop offset="75%" stopColor="#0f0c1c" />
          <stop offset="100%" stopColor="#0a0812" />
        </radialGradient>
        <radialGradient id="purpleBand" cx="50%" cy="50%" r="50%">
          <stop offset="70%" stopColor="#6d3cf0" stopOpacity="0" />
          <stop offset="88%" stopColor="#6d3cf0" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#6d3cf0" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="goldOuter" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#f6cf6b" />
          <stop offset="35%" stopColor="#a67a2c" />
          <stop offset="60%" stopColor="#e8b84a" />
          <stop offset="100%" stopColor="#f6cf6b" />
        </linearGradient>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="6" />
        </filter>
        <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="14" />
        </filter>
      </defs>

      <circle cx={CX} cy={CY} r="360" fill="url(#bgGlow)" />

      {/* Outer gold ring */}
      <circle cx={CX} cy={CY} r="292" fill="none" stroke="#e8b84a" strokeOpacity="0.5" strokeWidth="6" filter="url(#glow)" />
      <circle cx={CX} cy={CY} r="292" fill="none" stroke="url(#goldOuter)" strokeWidth="2" />
      <circle cx={CX} cy={CY} r="278" fill="none" stroke="#ffffff" strokeOpacity="0.08" strokeWidth="1" />
      <circle cx={CX} cy={CY} r="262" fill="none" stroke="#8b7bd8" strokeOpacity="0.18" strokeWidth="1" />
      <circle cx={CX} cy={CY} r="240" fill="none" stroke="#ffffff" strokeOpacity="0.06" strokeWidth="1" strokeDasharray="2 6" />

      {dotAngles.map((a) => {
        const rad = (a * Math.PI) / 180
        return (
          <circle
            key={a}
            cx={CX + Math.cos(rad) * 292}
            cy={CY + Math.sin(rad) * 292}
            r="2.2"
            fill="#fbe3a0"
            opacity="0.85"
          />
        )
      })}

      {/* Purple band */}
      <circle cx={CX} cy={CY} r="230" fill="url(#purpleBand)" />
      <circle cx={CX} cy={CY} r="205" fill="none" stroke="#7c4dff" strokeOpacity="0.8" strokeWidth="14" filter="url(#softGlow)" />
      <circle cx={CX} cy={CY} r="205" fill="none" stroke="#8f63ff" strokeWidth="2.5" />
      <circle cx={CX} cy={CY} r="190" fill="none" stroke="#a78bfa" strokeOpacity="0.25" strokeWidth="1" />
      <circle cx={CX} cy={CY} r="172" fill="none" stroke="#a78bfa" strokeOpacity="0.15" strokeWidth="1" />

      {/* Gold core ring */}
      <circle cx={CX} cy={CY} r="150" fill="url(#coreFill)" />
      <circle cx={CX} cy={CY} r="150" fill="none" stroke="#f0c25a" strokeOpacity="0.6" strokeWidth="8" filter="url(#glow)" />
      <circle cx={CX} cy={CY} r="150" fill="none" stroke="#f3c75e" strokeWidth="2.5" />
      <circle cx={CX} cy={CY} r="140" fill="none" stroke="#f3c75e" strokeOpacity="0.12" strokeWidth="1" />
    </svg>
  )
}
