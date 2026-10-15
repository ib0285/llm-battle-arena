import styles from './arena.module.css'

export function ArenaRings() {
  return (
    <div className={styles.rings} aria-hidden="true">
      <span />
      <span />
      <span />
      <span />
    </div>
  )
}
