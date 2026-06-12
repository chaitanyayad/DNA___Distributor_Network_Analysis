import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import AppLayout from '../components/AppLayout'
import MainMap from '../components/Map/MainMap'
import KPICard from '../components/KPICard'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'

export default function DistributorDashboard() {
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [territory, setTerritory] = useState(null)
  const [whitespaces, setWhitespaces] = useState([])
  const [locationCount, setLocationCount] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showWhitespace, setShowWhitespace] = useState(true)
  const [fitBounds, setFitBounds] = useState(null)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const [terrRes, wsRes, locRes] = await Promise.allSettled([
          client.get('/api/territories'),
          client.get('/api/analytics/whitespaces'),
          client.get('/api/locations', { params:{ limit:1 } }),
        ])

        if (terrRes.status === 'fulfilled') {
          const myTerritory = (terrRes.value.data || []).find(t => t.distributor_id === auth?.distributorId)
          setTerritory(myTerritory || null)

          if (myTerritory?.geojson?.coordinates?.[0]) {
            const coords = myTerritory.geojson.coordinates[0]
            const lons = coords.map(c => c[0])
            const lats = coords.map(c => c[1])
            setFitBounds([
              [Math.min(...lons), Math.min(...lats)],
              [Math.max(...lons), Math.max(...lats)],
            ])
          }
        }
        if (wsRes.status === 'fulfilled') {
          setWhitespaces(wsRes.value.data || [])
        }
        if (locRes.status === 'fulfilled') {
          setLocationCount(locRes.value.data.total)
        }
      } catch {}
      finally { setLoading(false) }
    }
    load()
  }, [auth?.distributorId])

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
          <h1 style={{ fontSize:16, fontWeight:700, color:'var(--text-dark)' }}>My Territory</h1>
          <p style={{ fontSize:11, color:'var(--text-muted)' }}>
            {auth?.distributorId ? (
              <>Distributor ID: <span style={{ fontFamily:'var(--font-mono)', color:'var(--primary)' }}>{auth.distributorId}</span></>
            ) : 'Your assigned territory view'}
          </p>
        </div>
        <button
          onClick={() => navigate('/request-ro')}
          style={{
            padding:'8px 18px', borderRadius:6, border:'none',
            background:'var(--cta)', color:'#fff',
            fontWeight:700, fontSize:13, cursor:'pointer',
            display:'flex', alignItems:'center', gap:6,
            transition:'var(--transition)',
            boxShadow:'0 2px 8px rgba(245,158,11,.4)',
          }}
          onMouseEnter={(e) => e.currentTarget.style.background='var(--cta-dark)'}
          onMouseLeave={(e) => e.currentTarget.style.background='var(--cta)'}
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
            <path d="M12 5v14m7-7H5"/>
          </svg>
          Request New RO
        </button>
      </div>

      {/* KPI strip */}
      <div style={{
        display:'flex', gap:12, padding:'12px 16px',
        overflowX:'auto', flexShrink:0,
        background:'var(--bg)', borderBottom:'1px solid var(--border)',
      }}>
        <KPICard
          label="My Touchpoints"
          value={loading ? null : locationCount?.toLocaleString('en-IN') ?? '—'}
          sub="within territory"
          accent="#1E40AF"
          loading={loading}
        />
        <KPICard
          label="Territory Status"
          value={loading ? null : territory ? (territory.locked ? 'Locked' : 'Active') : 'No Territory'}
          sub={territory?.territory_name || '—'}
          accent={territory?.locked ? '#16A34A' : '#F59E0B'}
          loading={loading}
        />
        <KPICard
          label="Untapped Pockets"
          value={loading ? null : whitespaces.length}
          sub="expansion opportunities"
          accent="#7C3AED"
          loading={loading}
        />
      </div>

      {/* Map */}
      <div style={{ flex:1, position:'relative', overflow:'hidden' }}>
        {!territory && !loading && (
          <div style={{
            position:'absolute', top:12, left:'50%', transform:'translateX(-50%)',
            zIndex:20, background:'#FEF3C7', border:'1px solid #FDE68A',
            borderRadius:8, padding:'8px 16px',
            fontSize:12, color:'#92400E', fontWeight:500,
            boxShadow:'var(--shadow-sm)',
          }}>
            No territory assigned to your account yet. Contact your admin.
          </div>
        )}

        <MainMap
          mode="view"
          visibleTypes={new Set(['Dealer','Retail Office','Independent Workshop','MASS','Mother Warehouse','Additional Warehouse'])}
          showHeatmap={false}
          showWhitespace={showWhitespace}
          showTerritories
          fitBounds={fitBounds}
        />

        {/* Whitespace toggle */}
        <div style={{
          position:'absolute', right:12, top:12, zIndex:10,
          background:'rgba(255,255,255,.92)', backdropFilter:'blur(12px)',
          border:'1px solid var(--border)', borderRadius:10,
          padding:'10px 14px', boxShadow:'var(--shadow-md)',
          minWidth:160,
        }}>
          <div style={{ fontSize:10, fontWeight:700, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'.5px', marginBottom:8 }}>
            Analytics
          </div>
          <label style={{ display:'flex', alignItems:'center', gap:8, cursor:'pointer', userSelect:'none' }}>
            <div onClick={() => setShowWhitespace(v=>!v)} style={{
              width:32, height:18, borderRadius:999, flexShrink:0,
              background: showWhitespace ? '#8B5CF6' : '#CBD5E1',
              position:'relative', transition:'var(--transition)', cursor:'pointer',
            }}>
              <div style={{
                width:14, height:14, borderRadius:'50%', background:'#fff',
                position:'absolute', top:2,
                left: showWhitespace ? 16 : 2,
                transition:'var(--transition)',
                boxShadow:'0 1px 3px rgba(0,0,0,.2)',
              }} />
            </div>
            <div>
              <div style={{ fontSize:12, color:'var(--text-dark)', fontWeight:500 }}>Untapped Pockets</div>
              <div style={{ fontSize:10, color:'var(--text-muted)' }}>{whitespaces.length} identified</div>
            </div>
          </label>

          {whitespaces.length > 0 && (
            <div style={{
              marginTop:10, padding:'8px 10px',
              background:'#EDE9FE', borderRadius:6,
              fontSize:11, color:'#5B21B6',
            }}>
              <strong>{whitespaces.length}</strong> areas with high workshop density
              but no dealer coverage within 15 km.
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
