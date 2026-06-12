import { useState, useEffect, useCallback } from 'react'
import AppLayout from '../components/AppLayout'
import MainMap from '../components/Map/MainMap'
import client from '../api/client'

function TerritoryListItem({ t, onLock, onDelete }) {
  const [locking, setLocking] = useState(false)
  const [deleting, setDeleting] = useState(false)

  async function handleLock() {
    setLocking(true)
    try { await onLock(t.id) }
    finally { setLocking(false) }
  }

  async function handleDelete() {
    const msg = t.locked
      ? `"${t.territory_name}" is LOCKED and actively used by distributor ${t.distributor_id}. Deleting it will remove their map boundary and block their access. Are you sure?`
      : `Delete "${t.territory_name}"? This cannot be undone.`
    if (!window.confirm(msg)) return
    setDeleting(true)
    try { await onDelete(t.id) }
    finally { setDeleting(false) }
  }

  return (
    <div style={{
      padding:'12px 14px',
      borderBottom:'1px solid var(--border)',
      animation:'fadeIn 200ms ease both',
    }}>
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:8 }}>
        <div style={{ flex:1, minWidth:0 }}>
          <div style={{ fontSize:13, fontWeight:700, color:'var(--text-dark)', marginBottom:2, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
            {t.territory_name}
          </div>
          <div style={{ fontSize:11, color:'var(--text-muted)', fontFamily:'var(--font-mono)', marginBottom:4 }}>
            {t.distributor_id}
          </div>
          <span className={`badge ${t.locked ? 'badge-green' : 'badge-gray'}`}>
            {t.locked ? 'Locked' : 'Unlocked'}
          </span>
        </div>
        <div style={{ display:'flex', gap:6, flexShrink:0 }}>
          {!t.locked && (
            <button
              onClick={handleLock}
              disabled={locking || deleting}
              style={{
                padding:'5px 12px', borderRadius:6, border:'none',
                background:'var(--primary)', color:'#fff',
                fontWeight:600, fontSize:11, cursor: locking ? 'not-allowed' : 'pointer',
                transition:'var(--transition)', opacity: locking ? .6 : 1,
              }}
            >
              {locking ? '…' : 'Lock'}
            </button>
          )}
          <button
            onClick={handleDelete}
            disabled={deleting || locking}
            title={t.locked ? 'Delete locked territory (removes distributor boundary)' : 'Delete territory'}
            style={{
              padding:'5px 8px', borderRadius:6,
              border:`1.5px solid ${t.locked ? '#FCA5A5' : '#FECACA'}`,
              background: t.locked ? '#FEE2E2' : '#FEF2F2',
              color:'#DC2626',
              cursor: deleting ? 'not-allowed' : 'pointer',
              transition:'var(--transition)', opacity: deleting ? .6 : 1,
              display:'flex', alignItems:'center',
            }}
          >
            {deleting ? '…' : (
              <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6m4-6v6"/><path d="M9 6V4h6v2"/>
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function TerritoryManager() {
  const [territories, setTerritories] = useState([])
  const [loading, setLoading]         = useState(true)
  const [mode, setMode]               = useState('view')   // 'view' | 'draw'
  const [drawnPolygon, setDrawnPolygon] = useState(null)
  const [modal, setModal]             = useState(false)
  const [form, setForm]               = useState({ territory_name:'', distributor_id:'' })
  const [saving, setSaving]           = useState(false)
  const [error, setError]             = useState('')
  const [toast, setToast]             = useState(null)
  const [territoriesVersion, setTerritoriesVersion] = useState(0)

  const loadTerritories = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await client.get('/api/territories')
      setTerritories(Array.isArray(data) ? data : [])
      setTerritoriesVersion((v) => v + 1)
    } catch { setTerritories([]) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { loadTerritories() }, [loadTerritories])

  function handlePolygonDraw(polygon) {
    setDrawnPolygon(polygon)
    setModal(true)
    setMode('view')
    setError('')
  }

  async function handleSave() {
    if (!form.territory_name.trim() || !form.distributor_id.trim()) {
      setError('Both fields are required.')
      return
    }
    setSaving(true)
    setError('')
    try {
      await client.post('/api/territories', {
        territory_name:  form.territory_name.trim(),
        distributor_id:  form.distributor_id.trim(),
        geojson_polygon: drawnPolygon,
      })
      setToast({ msg:'Territory created successfully!', type:'success' })
      setModal(false)
      setDrawnPolygon(null)
      setForm({ territory_name:'', distributor_id:'' })
      loadTerritories()
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to save territory.'
      if (err.response?.status === 409) {
        setError(`Overlap detected: ${msg}`)
      } else {
        setError(msg)
      }
    } finally {
      setSaving(false)
    }
    if (toast) setTimeout(() => setToast(null), 3000)
  }

  async function handleLock(id) {
    try {
      await client.patch(`/api/territories/${id}/lock`)
      setToast({ msg:'Territory locked successfully.', type:'success' })
      setTimeout(() => setToast(null), 3000)
      loadTerritories()
    } catch (err) {
      setToast({ msg: err.response?.data?.detail || 'Failed to lock territory.', type:'error' })
      setTimeout(() => setToast(null), 3000)
    }
  }

  async function handleDelete(id) {
    try {
      await client.delete(`/api/territories/${id}`)
      setToast({ msg:'Territory deleted.', type:'success' })
      setTimeout(() => setToast(null), 3000)
      loadTerritories()
    } catch (err) {
      setToast({ msg: err.response?.data?.detail || 'Failed to delete territory.', type:'error' })
      setTimeout(() => setToast(null), 3000)
    }
  }

  return (
    <AppLayout>
      <div style={{ display:'flex', flexDirection:'column', height:'100%' }}>
        {/* Topbar */}
        <div style={{
          padding:'12px 20px',
          borderBottom:'1px solid var(--border)',
          background:'var(--card-bg)',
          display:'flex', alignItems:'center', justifyContent:'space-between',
          flexShrink:0,
        }}>
          <div>
            <h1 style={{ fontSize:16, fontWeight:700, color:'var(--text-dark)' }}>Territory Manager</h1>
            <p style={{ fontSize:11, color:'var(--text-muted)' }}>Draw, assign, and lock distributor territories</p>
          </div>
          <button
            onClick={() => setMode(mode === 'draw' ? 'view' : 'draw')}
            style={{
              padding:'8px 16px', borderRadius:6, border:'none',
              background: mode === 'draw' ? 'var(--danger)' : 'var(--cta)',
              color:'#fff', fontWeight:600, fontSize:13, cursor:'pointer',
              transition:'var(--transition)',
              display:'flex', alignItems:'center', gap:6,
            }}
          >
            {mode === 'draw' ? (
              <>
                <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>
                Cancel Drawing
              </>
            ) : (
              <>
                <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M12 5v14m7-7H5"/></svg>
                Draw Territory
              </>
            )}
          </button>
        </div>

        {mode === 'draw' && (
          <div style={{
            padding:'8px 20px', background:'#FEF3C7', borderBottom:'1px solid #FDE68A',
            fontSize:12, color:'#92400E', display:'flex', alignItems:'center', gap:6,
          }}>
            <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg>
            Click on the map to add polygon vertices. Click <strong>Complete Polygon</strong> when done (minimum 3 points).
          </div>
        )}

        <div style={{ display:'flex', flex:1, overflow:'hidden' }}>
          {/* Map */}
          <div style={{ flex:1, position:'relative' }}>
            <MainMap
              mode={mode}
              visibleTypes={new Set(['Dealer','Retail Office','Mother Warehouse','Additional Warehouse'])}
              showHeatmap={false}
              showWhitespace={false}
              showTerritories
              territoriesVersion={territoriesVersion}
              onPolygonDraw={handlePolygonDraw}
            />
          </div>

          {/* Territory list sidebar */}
          <div style={{
            width:280, background:'var(--card-bg)',
            borderLeft:'1px solid var(--border)',
            display:'flex', flexDirection:'column',
            overflow:'hidden',
          }}>
            <div style={{
              padding:'12px 14px', borderBottom:'1px solid var(--border)',
              fontSize:12, fontWeight:700, color:'var(--text-muted)',
              textTransform:'uppercase', letterSpacing:'.4px',
              display:'flex', alignItems:'center', justifyContent:'space-between',
            }}>
              <span>Territories ({territories.length})</span>
              <span style={{ color:'var(--success)' }}>
                {territories.filter(t=>t.locked).length} locked
              </span>
            </div>
            <div style={{ overflowY:'auto', flex:1 }}>
              {loading ? (
                <div style={{ display:'flex', justifyContent:'center', padding:24 }}>
                  <div className="spinner" />
                </div>
              ) : territories.length === 0 ? (
                <div style={{ padding:24, textAlign:'center', color:'var(--text-muted)', fontSize:12 }}>
                  No territories yet.<br />Draw one using the button above.
                </div>
              ) : (
                territories.map((t) => (
                  <TerritoryListItem key={t.id} t={t} onLock={handleLock} onDelete={handleDelete} />
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Save territory modal */}
      {modal && (
        <div style={{
          position:'fixed', inset:0, zIndex:200,
          background:'rgba(0,0,0,.45)', backdropFilter:'blur(4px)',
          display:'flex', alignItems:'center', justifyContent:'center',
        }} onClick={(e) => { if(e.target===e.currentTarget){ setModal(false); setDrawnPolygon(null) } }}>
          <div style={{
            background:'#fff', borderRadius:12, width:400,
            boxShadow:'var(--shadow-lg)', overflow:'hidden',
            animation:'fadeIn 200ms ease both',
          }}>
            <div style={{ padding:'16px 20px', borderBottom:'1px solid var(--border)' }}>
              <h2 style={{ fontSize:16, fontWeight:700, color:'var(--text-dark)' }}>Save Territory</h2>
              <p style={{ fontSize:12, color:'var(--text-muted)' }}>Assign this polygon to a distributor</p>
            </div>
            <div style={{ padding:'20px' }}>
              <div style={{ marginBottom:14 }}>
                <label style={{ display:'block', fontSize:12, fontWeight:600, color:'var(--text-dark)', marginBottom:6 }}>
                  Territory Name
                </label>
                <input
                  value={form.territory_name}
                  onChange={(e) => setForm(f => ({ ...f, territory_name:e.target.value }))}
                  placeholder="e.g. Mumbai North Zone"
                  style={{
                    width:'100%', padding:'9px 11px',
                    border:'1.5px solid var(--border)', borderRadius:7, fontSize:13,
                    outline:'none', fontFamily:'var(--font-body)', color:'var(--text-dark)',
                  }}
                  onFocus={(e) => e.target.style.borderColor='var(--primary)'}
                  onBlur={(e) => e.target.style.borderColor='var(--border)'}
                />
              </div>
              <div style={{ marginBottom:16 }}>
                <label style={{ display:'block', fontSize:12, fontWeight:600, color:'var(--text-dark)', marginBottom:6 }}>
                  Distributor ID
                </label>
                <input
                  value={form.distributor_id}
                  onChange={(e) => setForm(f => ({ ...f, distributor_id:e.target.value }))}
                  placeholder="e.g. DLR-0001"
                  style={{
                    width:'100%', padding:'9px 11px',
                    border:'1.5px solid var(--border)', borderRadius:7, fontSize:13,
                    outline:'none', fontFamily:'var(--font-mono)', color:'var(--text-dark)',
                  }}
                  onFocus={(e) => e.target.style.borderColor='var(--primary)'}
                  onBlur={(e) => e.target.style.borderColor='var(--border)'}
                />
              </div>

              {error && (
                <div style={{
                  padding:'9px 12px', borderRadius:7, marginBottom:14,
                  background: error.includes('Overlap') ? '#FEF3C7' : '#FEE2E2',
                  border:`1px solid ${error.includes('Overlap') ? '#FDE68A' : '#FECACA'}`,
                  color: error.includes('Overlap') ? '#92400E' : '#B91C1C',
                  fontSize:12, lineHeight:1.5,
                }}>
                  {error}
                </div>
              )}

              <div style={{ display:'flex', gap:8 }}>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  style={{
                    flex:1, padding:'9px', borderRadius:7, border:'none',
                    background: saving ? '#93C5FD' : 'var(--primary)',
                    color:'#fff', fontWeight:600, fontSize:13,
                    cursor: saving ? 'not-allowed' : 'pointer',
                    transition:'var(--transition)',
                  }}
                >
                  {saving ? 'Saving…' : 'Save Territory'}
                </button>
                <button
                  onClick={() => { setModal(false); setDrawnPolygon(null); setError('') }}
                  style={{
                    padding:'9px 16px', borderRadius:7,
                    border:'1.5px solid var(--border)',
                    background:'#fff', cursor:'pointer',
                    fontWeight:500, fontSize:13, color:'var(--text-muted)',
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div style={{
          position:'fixed', bottom:24, right:24, zIndex:300,
          padding:'12px 20px', borderRadius:8,
          background: toast.type==='success' ? '#DCFCE7' : '#FEE2E2',
          border:`1px solid ${toast.type==='success' ? '#BBF7D0' : '#FECACA'}`,
          color: toast.type==='success' ? '#15803D' : '#B91C1C',
          fontWeight:600, fontSize:13, boxShadow:'var(--shadow-md)',
          animation:'fadeIn 200ms ease both',
        }}>
          {toast.msg}
        </div>
      )}
    </AppLayout>
  )
}
