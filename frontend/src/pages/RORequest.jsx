import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppLayout from '../components/AppLayout'
import MainMap from '../components/Map/MainMap'
import client from '../api/client'

export default function RORequest() {
  const navigate = useNavigate()
  const [pin, setPin]         = useState(null)   // { lat, lng }
  const [form, setForm]       = useState({ proposed_name:'', proposed_address:'', justification:'' })
  const [saving, setSaving]   = useState(false)
  const [error, setError]     = useState('')
  const [success, setSuccess] = useState(false)

  function handlePinDrop(lat, lng) {
    setPin({ lat, lng })
    setError('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!pin) { setError('Drop a pin on the map first.'); return }
    if (!form.proposed_name.trim()) { setError('Name is required.'); return }
    setSaving(true)
    setError('')
    try {
      await client.post('/api/workflow/request-ro', {
        proposed_name:    form.proposed_name.trim(),
        proposed_address: form.proposed_address.trim(),
        justification:    form.justification.trim(),
        latitude:         pin.lat,
        longitude:        pin.lng,
      })
      setSuccess(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Submission failed. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  if (success) {
    return (
      <AppLayout>
        <div style={{
          flex:1, display:'flex', alignItems:'center', justifyContent:'center',
          flexDirection:'column', gap:16, padding:40,
          animation:'fadeIn 300ms ease both',
        }}>
          <div style={{
            width:64, height:64, borderRadius:'50%', background:'#DCFCE7',
            display:'flex', alignItems:'center', justifyContent:'center',
          }}>
            <svg width="28" height="28" fill="none" stroke="#16A34A" strokeWidth="2.5" viewBox="0 0 24 24">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <div style={{ textAlign:'center' }}>
            <h2 style={{ fontSize:20, fontWeight:700, color:'var(--text-dark)', marginBottom:8 }}>
              Request Submitted!
            </h2>
            <p style={{ color:'var(--text-muted)', fontSize:14, maxWidth:320 }}>
              Your Retail Office request is under review. You'll see it on your dashboard once the admin approves it.
            </p>
          </div>
          <div style={{ display:'flex', gap:10 }}>
            <button
              onClick={() => { setSuccess(false); setPin(null); setForm({ proposed_name:'', proposed_address:'', justification:'' }) }}
              style={{
                padding:'9px 20px', borderRadius:7,
                border:'1.5px solid var(--border)', background:'#fff',
                cursor:'pointer', fontWeight:500, fontSize:13, color:'var(--text-dark)',
              }}
            >
              Submit Another
            </button>
            <button
              onClick={() => navigate('/my-territory')}
              style={{
                padding:'9px 20px', borderRadius:7, border:'none',
                background:'var(--primary)', color:'#fff',
                cursor:'pointer', fontWeight:600, fontSize:13,
              }}
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </AppLayout>
    )
  }

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
          <h1 style={{ fontSize:16, fontWeight:700, color:'var(--text-dark)' }}>Request New Retail Office</h1>
          <p style={{ fontSize:11, color:'var(--text-muted)' }}>Drop a pin inside your territory, then fill in the details</p>
        </div>
        <button
          onClick={() => navigate('/my-territory')}
          style={{
            padding:'7px 14px', borderRadius:6,
            border:'1.5px solid var(--border)', background:'#fff',
            cursor:'pointer', fontWeight:500, fontSize:12, color:'var(--text-muted)',
            display:'flex', alignItems:'center', gap:6,
          }}
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M19 12H5m7-7l-7 7 7 7"/>
          </svg>
          Back
        </button>
      </div>

      <div style={{ display:'flex', flex:1, overflow:'hidden' }}>
        {/* Map */}
        <div style={{ flex:1, position:'relative' }}>
          {!pin && (
            <div style={{
              position:'absolute', top:12, left:'50%', transform:'translateX(-50%)',
              zIndex:20, background:'rgba(15,23,42,.85)', backdropFilter:'blur(8px)',
              borderRadius:8, padding:'8px 18px',
              fontSize:12, color:'#F8FAFC', fontWeight:500,
              pointerEvents:'none',
            }}>
              Click anywhere on the map to place your proposed location
            </div>
          )}
          {pin && (
            <div style={{
              position:'absolute', top:12, left:'50%', transform:'translateX(-50%)',
              zIndex:20, background:'rgba(30,64,175,.9)', backdropFilter:'blur(8px)',
              borderRadius:8, padding:'7px 16px',
              fontSize:11, color:'#fff',
              fontFamily:'var(--font-mono)', pointerEvents:'none',
            }}>
              {pin.lat.toFixed(5)}, {pin.lng.toFixed(5)} — Click again to move the pin
            </div>
          )}
          <MainMap
            mode="ro-request"
            onPinDrop={handlePinDrop}
            droppedPin={pin}
            visibleTypes={new Set(['Dealer','Retail Office','Independent Workshop','MASS'])}
            showHeatmap={false}
            showWhitespace={false}
            showTerritories
          />
        </div>

        {/* Form panel */}
        <div style={{
          width:320, background:'var(--card-bg)',
          borderLeft:'1px solid var(--border)',
          display:'flex', flexDirection:'column',
          overflow:'hidden',
        }}>
          <div style={{
            padding:'14px 16px', borderBottom:'1px solid var(--border)',
            fontSize:12, fontWeight:700, color:'var(--text-muted)',
            textTransform:'uppercase', letterSpacing:'.4px',
          }}>
            Request Details
          </div>

          <form onSubmit={handleSubmit} style={{ padding:16, overflowY:'auto', flex:1 }}>
            {/* Pin status */}
            <div style={{
              padding:'10px 12px', borderRadius:8, marginBottom:16,
              background: pin ? '#DCFCE7' : '#F8FAFC',
              border:`1px solid ${pin ? '#BBF7D0' : 'var(--border)'}`,
              display:'flex', alignItems:'center', gap:8,
            }}>
              <div style={{
                width:10, height:10, borderRadius:'50%', flexShrink:0,
                background: pin ? 'var(--success)' : '#CBD5E1',
              }} />
              <span style={{ fontSize:12, color: pin ? '#15803D' : 'var(--text-muted)' }}>
                {pin
                  ? `Pin placed at ${pin.lat.toFixed(4)}, ${pin.lng.toFixed(4)}`
                  : 'No pin placed yet'}
              </span>
            </div>

            <div style={{ marginBottom:14 }}>
              <label style={{ display:'block', fontSize:12, fontWeight:600, color:'var(--text-dark)', marginBottom:6 }}>
                Proposed Name <span style={{ color:'var(--danger)' }}>*</span>
              </label>
              <input
                value={form.proposed_name}
                onChange={(e) => setForm(f=>({...f,proposed_name:e.target.value}))}
                placeholder="e.g. Andheri West Retail Office"
                style={{
                  width:'100%', padding:'9px 11px',
                  border:'1.5px solid var(--border)', borderRadius:7, fontSize:13,
                  outline:'none', fontFamily:'var(--font-body)', color:'var(--text-dark)',
                }}
                onFocus={(e)=>e.target.style.borderColor='var(--primary)'}
                onBlur={(e)=>e.target.style.borderColor='var(--border)'}
              />
            </div>

            <div style={{ marginBottom:14 }}>
              <label style={{ display:'block', fontSize:12, fontWeight:600, color:'var(--text-dark)', marginBottom:6 }}>
                Proposed Address
              </label>
              <input
                value={form.proposed_address}
                onChange={(e) => setForm(f=>({...f,proposed_address:e.target.value}))}
                placeholder="Street, area, city"
                style={{
                  width:'100%', padding:'9px 11px',
                  border:'1.5px solid var(--border)', borderRadius:7, fontSize:13,
                  outline:'none', fontFamily:'var(--font-body)', color:'var(--text-dark)',
                }}
                onFocus={(e)=>e.target.style.borderColor='var(--primary)'}
                onBlur={(e)=>e.target.style.borderColor='var(--border)'}
              />
            </div>

            <div style={{ marginBottom:20 }}>
              <label style={{ display:'block', fontSize:12, fontWeight:600, color:'var(--text-dark)', marginBottom:6 }}>
                Business Justification
              </label>
              <textarea
                value={form.justification}
                onChange={(e) => setForm(f=>({...f,justification:e.target.value}))}
                placeholder="Explain why this location needs an RO — nearby workshop density, current coverage gaps, etc."
                rows={4}
                style={{
                  width:'100%', padding:'9px 11px',
                  border:'1.5px solid var(--border)', borderRadius:7, fontSize:13,
                  outline:'none', resize:'vertical', fontFamily:'var(--font-body)',
                  color:'var(--text-dark)', lineHeight:1.5,
                }}
                onFocus={(e)=>e.target.style.borderColor='var(--primary)'}
                onBlur={(e)=>e.target.style.borderColor='var(--border)'}
              />
            </div>

            {error && (
              <div style={{
                padding:'9px 12px', borderRadius:7, marginBottom:14,
                background:'#FEE2E2', border:'1px solid #FECACA',
                color:'#B91C1C', fontSize:12, lineHeight:1.5,
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={saving || !pin}
              style={{
                width:'100%', padding:'10px', borderRadius:7, border:'none',
                background: (!pin || saving) ? '#93C5FD' : 'var(--cta)',
                color:'#fff', cursor: (!pin || saving) ? 'not-allowed' : 'pointer',
                fontWeight:700, fontSize:13,
                display:'flex', alignItems:'center', justifyContent:'center', gap:8,
                transition:'var(--transition)',
              }}
            >
              {saving && <span className="spinner" style={{ width:16,height:16,borderTopColor:'#fff',borderColor:'rgba(255,255,255,.3)' }} />}
              {saving ? 'Submitting…' : 'Submit Request'}
            </button>

            <p style={{ fontSize:11, color:'var(--text-muted)', marginTop:10, lineHeight:1.5 }}>
              The system will verify the pin is inside your assigned territory before saving.
            </p>
          </form>
        </div>
      </div>
    </AppLayout>
  )
}
