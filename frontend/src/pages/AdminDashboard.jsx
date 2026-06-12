import { useState, useEffect } from 'react'
import AppLayout from '../components/AppLayout'
import KPICard from '../components/KPICard'
import LayerToggle, { TYPE_META } from '../components/LayerToggle'
import MainMap from '../components/Map/MainMap'
import client from '../api/client'

const ALL_TYPES = new Set(Object.keys(TYPE_META))

const formatINR = (n) => {
  if (!n) return '₹0'
  if (n >= 1e12) return `₹${(n/1e12).toFixed(1)}T`
  if (n >= 1e9)  return `₹${(n/1e9).toFixed(1)}B`
  if (n >= 1e7)  return `₹${(n/1e7).toFixed(1)}Cr`
  if (n >= 1e5)  return `₹${(n/1e5).toFixed(1)}L`
  return `₹${Math.round(n).toLocaleString('en-IN')}`
}

export default function AdminDashboard() {
  const [summary, setSummary]           = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(true)
  const [visibleTypes, setVisibleTypes] = useState(new Set(ALL_TYPES))
  const [showHeatmap, setShowHeatmap]   = useState(false)
  const [showWhitespace, setShowWhitespace] = useState(false)

  useEffect(() => {
    async function load() {
      setSummaryLoading(true)
      try {
        const { data } = await client.get('/api/analytics/summary')
        setSummary(data)
      } catch {}
      finally { setSummaryLoading(false) }
    }
    load()
  }, [])

  function toggleType(type) {
    setVisibleTypes((prev) => {
      const next = new Set(prev)
      next.has(type) ? next.delete(type) : next.add(type)
      return next
    })
  }

  const kpis = summary ? [
    { label:'Total Touchpoints',    value: summary.total_locations?.toLocaleString('en-IN'),   sub:`${summary.active_locations?.toLocaleString('en-IN')} active`, accent:'#1E40AF' },
    { label:'Territories Locked',   value: `${summary.locked_territories}/${summary.total_territories}`,                sub:'boundaries secured',  accent:'#16A34A' },
    { label:'Pending Approvals',    value: summary.pending_ro_requests,  sub:'RO requests',         accent: summary.pending_ro_requests > 0 ? '#F59E0B' : '#64748B' },
    { label:'Market Potential',     value: formatINR(summary.total_predicted_revenue_inr), sub:'predicted annual rev.',  accent:'#7C3AED' },
  ] : Array(4).fill(null)

  return (
    <AppLayout>
      {/* Topbar */}
      <div style={{
        padding:'12px 20px',
        borderBottom:'1px solid var(--border)',
        background:'var(--card-bg)',
        display:'flex', alignItems:'center', justifyContent:'space-between',
        flexShrink:0,
      }}>
        <div>
          <h1 style={{ fontSize:16, fontWeight:700, color:'var(--text-dark)', marginBottom:1 }}>
            Pan-India Network Dashboard
          </h1>
          <p style={{ fontSize:11, color:'var(--text-muted)' }}>
            Live view — all distributor touchpoints across India
          </p>
        </div>
        <div style={{ display:'flex', gap:8 }}>
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            style={{
              padding:'7px 14px', borderRadius:6,
              border:'1.5px solid',
              borderColor: showHeatmap ? 'var(--cta)' : 'var(--border)',
              background:  showHeatmap ? '#FEF3C7' : '#fff',
              color:       showHeatmap ? '#B45309' : 'var(--text-muted)',
              fontWeight:600, fontSize:12, cursor:'pointer',
              transition:'var(--transition)',
            }}>
            {showHeatmap ? 'Hide Heatmap' : 'Show Heatmap'}
          </button>
        </div>
      </div>

      {/* KPI strip */}
      <div style={{
        display:'flex', gap:12, padding:'12px 16px',
        overflowX:'auto', flexShrink:0,
        background:'var(--bg)',
        borderBottom:'1px solid var(--border)',
      }}>
        {kpis.map((kpi, i) => (
          <KPICard key={i} loading={summaryLoading} {...(kpi || {})} />
        ))}

        {/* Type breakdown mini-cards */}
        {summary && Object.entries(summary.locations_by_type || {}).map(([type, count]) => (
          <KPICard
            key={type}
            label={type.replace(' Warehouse',' WH')}
            value={count?.toLocaleString('en-IN')}
            accent={TYPE_META[type]?.color}
          />
        ))}
      </div>

      {/* Map fills remaining space */}
      <div style={{ flex:1, position:'relative', overflow:'hidden' }}>
        <MainMap
          visibleTypes={visibleTypes}
          showHeatmap={showHeatmap}
          showWhitespace={showWhitespace}
          showTerritories
          mode="view"
        />
        <LayerToggle
          visible={visibleTypes}
          onChange={toggleType}
          showHeatmap={showHeatmap}
          onHeatmapToggle={() => setShowHeatmap((h) => !h)}
          showWhitespace={showWhitespace}
          onWhitespaceToggle={() => setShowWhitespace((w) => !w)}
        />
      </div>
    </AppLayout>
  )
}
