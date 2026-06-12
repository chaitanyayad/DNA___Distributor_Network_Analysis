import { useState, useEffect, useCallback } from 'react'
import AppLayout from '../components/AppLayout'
import client from '../api/client'

const StatusBadge = ({ status }) => {
  const map = { PENDING:'badge-amber', APPROVED:'badge-green', REJECTED:'badge-red' }
  return <span className={`badge ${map[status] || 'badge-gray'}`}>{status}</span>
}

function MiniMap({ lat, lng }) {
  const zoom = 13
  const tile = `https://tile.openstreetmap.org/${zoom}/${Math.floor((lng+180)/360*Math.pow(2,zoom))}/${Math.floor((1-Math.log(Math.tan(lat*Math.PI/180)+1/Math.cos(lat*Math.PI/180))/Math.PI)/2*Math.pow(2,zoom))}.png`
  return (
    <div style={{ position:'relative', width:'100%', height:160, borderRadius:8, overflow:'hidden', background:'#E2E8F0' }}>
      <div style={{
        position:'absolute', inset:0,
        background:`url(https://a.tile.openstreetmap.org/${zoom}/${Math.floor((lng+180)/360*(1<<zoom))}/${Math.floor((1-Math.log(Math.tan(lat*Math.PI/180)+1/Math.cos(lat*Math.PI/180))/Math.PI)/2*(1<<zoom))}.png)`,
        backgroundSize:'cover', filter:'saturate(.8)',
      }} />
      <div style={{
        position:'absolute', top:'50%', left:'50%', transform:'translate(-50%,-100%)',
        width:12, height:12, borderRadius:'50%',
        background:'var(--danger)', border:'2.5px solid #fff',
        boxShadow:'0 2px 6px rgba(0,0,0,.4)',
      }} />
      <div style={{
        position:'absolute', bottom:6, right:6,
        background:'rgba(255,255,255,.9)', borderRadius:4,
        padding:'2px 6px', fontSize:10, color:'var(--text-muted)',
        fontFamily:'var(--font-mono)',
      }}>
        {lat.toFixed(4)}, {lng.toFixed(4)}
      </div>
    </div>
  )
}

function RequestCard({ req, onDecide }) {
  const [note, setNote]       = useState('')
  const [loading, setLoading] = useState(false)

  async function decide(action) {
    setLoading(true)
    try {
      await onDecide(req.id, action, note)
    } finally {
      setLoading(false)
    }
  }

  const isPending = req.status === 'PENDING'

  return (
    <div style={{
      background:'var(--card-bg)', borderRadius:10,
      border:'1px solid var(--border)',
      boxShadow:'var(--shadow-sm)',
      overflow:'hidden',
      animation:'fadeIn 250ms ease both',
    }}>
      {/* Header */}
      <div style={{
        padding:'14px 16px',
        borderBottom:'1px solid var(--border)',
        display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:12,
      }}>
        <div>
          <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:4 }}>
            <span style={{ fontSize:13, fontWeight:700, color:'var(--text-dark)' }}>
              {req.proposed_name}
            </span>
            {req.conflict_flag && (
              <span className="badge badge-amber" style={{ fontSize:9 }}>Conflict</span>
            )}
          </div>
          <div style={{ fontSize:11, color:'var(--text-muted)' }}>
            Requested by distributor <span style={{ fontFamily:'var(--font-mono)', color:'var(--primary)' }}>
              {req.distributor_id || '—'}
            </span>
          </div>
        </div>
        <StatusBadge status={req.status} />
      </div>

      <div style={{ padding:'14px 16px' }}>
        {/* Mini map */}
        <MiniMap lat={req.latitude} lng={req.longitude} />

        {/* Details */}
        <div style={{ marginTop:12, display:'grid', gridTemplateColumns:'1fr 1fr', gap:'6px 16px' }}>
          {[
            { label:'Address', val:req.proposed_address },
            { label:'Justification', val:req.justification },
            { label:'Submitted', val:new Date(req.created_at).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' }) },
            { label:'Request ID', val:`#${req.id}` },
          ].map(({ label, val }) => val ? (
            <div key={label} style={{ gridColumn: label === 'Justification' ? '1/-1' : 'auto' }}>
              <div style={{ fontSize:10, fontWeight:600, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'.4px', marginBottom:2 }}>{label}</div>
              <div style={{ fontSize:12, color:'var(--text-dark)', lineHeight:1.4 }}>{val}</div>
            </div>
          ) : null)}
        </div>

        {/* Conflict warning */}
        {req.conflict_flag && (
          <div style={{
            marginTop:12, padding:'8px 12px', borderRadius:6,
            background:'#FEF3C7', border:'1px solid #FDE68A',
            fontSize:12, color:'#B45309',
          }}>
            A Retail Office already exists within 5 km. Review carefully before approving.
          </div>
        )}

        {/* Admin note (existing) */}
        {req.admin_note && (
          <div style={{ marginTop:10 }}>
            <div style={{ fontSize:10, fontWeight:600, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'.4px', marginBottom:4 }}>Admin Note</div>
            <div style={{ fontSize:12, color:'var(--text-dark)', background:'#F8FAFC', padding:'8px 10px', borderRadius:6, border:'1px solid var(--border)' }}>
              {req.admin_note}
            </div>
          </div>
        )}

        {/* Action area */}
        {isPending && (
          <div style={{ marginTop:14 }}>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Optional note for the distributor…"
              rows={2}
              style={{
                width:'100%', padding:'8px 10px', borderRadius:6,
                border:'1.5px solid var(--border)', fontSize:12,
                fontFamily:'var(--font-body)', resize:'vertical',
                outline:'none', marginBottom:10, color:'var(--text-dark)',
              }}
              onFocus={(e) => e.target.style.borderColor='var(--primary)'}
              onBlur={(e) => e.target.style.borderColor='var(--border)'}
            />
            <div style={{ display:'flex', gap:8 }}>
              <button
                onClick={() => decide('APPROVED')}
                disabled={loading}
                style={{
                  flex:1, padding:'8px', borderRadius:6, border:'none',
                  background:'var(--success)', color:'#fff', cursor: loading ? 'not-allowed' : 'pointer',
                  fontWeight:600, fontSize:12, transition:'var(--transition)',
                }}
                onMouseEnter={(e) => { if (!loading) e.currentTarget.style.background='#15803D' }}
                onMouseLeave={(e) => { if (!loading) e.currentTarget.style.background='var(--success)' }}
              >
                {loading ? '…' : 'Approve'}
              </button>
              <button
                onClick={() => decide('REJECTED')}
                disabled={loading}
                style={{
                  flex:1, padding:'8px', borderRadius:6, border:'none',
                  background:'var(--danger)', color:'#fff', cursor: loading ? 'not-allowed' : 'pointer',
                  fontWeight:600, fontSize:12, transition:'var(--transition)',
                }}
                onMouseEnter={(e) => { if (!loading) e.currentTarget.style.background='#B91C1C' }}
                onMouseLeave={(e) => { if (!loading) e.currentTarget.style.background='var(--danger)' }}
              >
                {loading ? '…' : 'Reject'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function Approvals() {
  const [requests, setRequests] = useState([])
  const [loading, setLoading]   = useState(true)
  const [filter, setFilter]     = useState('PENDING')
  const [toast, setToast]       = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const endpoint = filter === 'ALL' ? '/api/workflow/requests/all' : '/api/workflow/requests'
      const { data } = await client.get(endpoint)
      setRequests(Array.isArray(data) ? data : [])
    } catch { setRequests([]) }
    finally { setLoading(false) }
  }, [filter])

  useEffect(() => { load() }, [load])

  async function handleDecide(id, action, note) {
    await client.patch(`/api/workflow/requests/${id}`, { action, admin_note: note || undefined })
    setToast({ msg: `Request ${action.toLowerCase()}d successfully.`, type: action === 'APPROVED' ? 'success' : 'error' })
    setTimeout(() => setToast(null), 3000)
    load()
  }

  const filtered = filter === 'ALL' ? requests : requests.filter((r) => r.status === filter)

  return (
    <AppLayout>
      {/* Topbar */}
      <div style={{
        padding:'16px 24px',
        borderBottom:'1px solid var(--border)',
        background:'var(--card-bg)',
        display:'flex', alignItems:'center', justifyContent:'space-between',
        flexShrink:0,
      }}>
        <div>
          <h1 style={{ fontSize:18, fontWeight:700, color:'var(--text-dark)' }}>RO Approval Queue</h1>
          <p style={{ fontSize:12, color:'var(--text-muted)' }}>Review and action Retail Office expansion requests</p>
        </div>
        <div style={{ display:'flex', gap:6 }}>
          {['PENDING','ALL'].map((f) => (
            <button key={f} onClick={() => setFilter(f)} style={{
              padding:'6px 14px', borderRadius:6, border:'1.5px solid',
              borderColor: filter === f ? 'var(--primary)' : 'var(--border)',
              background:  filter === f ? 'var(--primary)' : '#fff',
              color:       filter === f ? '#fff' : 'var(--text-muted)',
              fontWeight:600, fontSize:12, cursor:'pointer', transition:'var(--transition)',
            }}>
              {f === 'PENDING' ? `Pending ${requests.filter(r=>r.status==='PENDING').length > 0 ? `(${requests.filter(r=>r.status==='PENDING').length})` : ''}` : 'All History'}
            </button>
          ))}
        </div>
      </div>

      <div style={{ flex:1, overflowY:'auto', padding:24 }}>
        {loading ? (
          <div style={{ display:'flex', justifyContent:'center', paddingTop:60 }}>
            <div className="spinner" style={{ width:28, height:28 }} />
          </div>
        ) : filtered.length === 0 ? (
          <div style={{
            textAlign:'center', paddingTop:80, color:'var(--text-muted)',
          }}>
            <div style={{ fontSize:36, marginBottom:12 }}>✓</div>
            <div style={{ fontSize:16, fontWeight:600, color:'var(--text-dark)' }}>All clear</div>
            <div style={{ fontSize:13 }}>No {filter === 'PENDING' ? 'pending' : ''} requests to review</div>
          </div>
        ) : (
          <div style={{
            display:'grid',
            gridTemplateColumns:'repeat(auto-fill, minmax(320px, 1fr))',
            gap:16,
          }}>
            {filtered.map((req) => (
              <RequestCard key={req.id} req={req} onDecide={handleDecide} />
            ))}
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div style={{
          position:'fixed', bottom:24, right:24, zIndex:100,
          padding:'12px 20px', borderRadius:8,
          background: toast.type === 'success' ? '#DCFCE7' : '#FEE2E2',
          border:`1px solid ${toast.type === 'success' ? '#BBF7D0' : '#FECACA'}`,
          color: toast.type === 'success' ? '#15803D' : '#B91C1C',
          fontWeight:600, fontSize:13,
          boxShadow:'var(--shadow-md)',
          animation:'fadeIn 200ms ease both',
        }}>
          {toast.msg}
        </div>
      )}
    </AppLayout>
  )
}
