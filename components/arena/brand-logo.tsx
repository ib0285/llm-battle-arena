import type { CSSProperties } from 'react'
import type { Company } from '@/lib/arena-data'
import styles from './arena.module.css'

export function BrandLogo({ company, className }: { company: Company; className?: string }) {
  if (company.logoMode === 'image') {
    return <img src={company.logo} alt="" className={className} />
  }

  const style: CSSProperties = {
    background: company.logoColor || company.accent,
    WebkitMaskImage: `url(${company.logo})`,
    maskImage: `url(${company.logo})`,
  }
  const classes = className ? `${styles.logoMask} ${className}` : styles.logoMask

  return <span className={classes} style={style} aria-hidden="true" />
}
