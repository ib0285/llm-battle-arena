import styles from './arena.module.css'

export function TodayDelta({ value, place }: { value: number | null; place: 'card' | 'core' | 'inline' }) {
  if (value === null || Number.isNaN(value)) return null
  const rounded = Math.round(value)
  const tone = rounded > 0 ? styles.up : rounded < 0 ? styles.down : styles.flat
  const arrow = rounded > 0 ? '▲' : rounded < 0 ? '▼' : ''
  const text = `${arrow ? `${arrow} ` : ''}${Math.abs(rounded)}% today`
  const placeClass = place === 'core' ? styles.coreDelta : place === 'inline' ? styles.inlineDelta : styles.cardDelta
  if (place === 'inline') return <span className={`${placeClass} ${tone}`}>{text}</span>
  return <p className={`${placeClass} ${tone}`}>{text}</p>
}
