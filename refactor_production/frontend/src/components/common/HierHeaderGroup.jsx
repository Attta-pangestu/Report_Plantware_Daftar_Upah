import React, { useMemo, useState } from 'react'

export default function HierHeaderGroup(props) {
  const { columnGroup, api } = props
  const level = useMemo(() => {
    let l = 1
    let p = columnGroup.getOriginalParent()
    while (p) {
      l += 1
      p = p.getOriginalParent()
    }
    return l
  }, [columnGroup])

  const [expanded, setExpanded] = useState(true)

  const collectLeafIds = group => {
    const children = group.getLeafColumns()
    return children.map(c => c.getColId())
  }

  const toggle = () => {
    const ids = collectLeafIds(columnGroup)
    api.setColumnsVisible(ids, !expanded)
    setExpanded(!expanded)
  }

  const label = columnGroup.getDisplayName()
  const upper = String(label || '').toUpperCase()
  const kind = (upper.includes('POTONGAN') ? 'kind-deduction'
                : (upper.includes('PENDAPATAN') || upper.includes('TUNJANGAN') || upper.includes('PREMI')) ? 'kind-income'
                : 'kind-neutral')

  const indent = (level - 1) * 8
  return (
    <div className={`hdr-group hdr-level-${level} ${kind}`} style={{ paddingLeft: indent }}>
      <button className={`hdr-toggle ${expanded ? 'open' : 'closed'}`} onClick={toggle} aria-label="toggle" type="button">{expanded ? '▾' : '▸'}</button>
      <span className="hdr-label">{label}</span>
    </div>
  )
}
