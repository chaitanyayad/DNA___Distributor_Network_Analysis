import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'

export default function Login() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await client.post('/api/auth/login', { email, password })
      login(data)
      navigate(data.role === 'org_admin' ? '/dashboard' : '/my-territory')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight:'100vh', display:'flex',
      background:'linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #1E40AF 100%)',
    }}>
      {/* Left branding panel */}
      <div style={{
        flex:1, display:'flex', flexDirection:'column',
        justifyContent:'center', padding:'60px 80px',
        display:'flex',
      }} className="fade-in">
        <div style={{ maxWidth:440 }}>
          <div style={{ marginBottom:40 }}>
            <div style={{
              display:'inline-block', background:'#fff',
              padding:'6px 14px', borderRadius:6,
            }}>
              <img
                src="/maruti-suzuki-logo.svg"
                alt="Maruti Suzuki"
                style={{ height:36, width:'auto', display:'block' }}
              />
            </div>
            <div style={{ color:'#e2e5ea', fontSize:12, marginTop:8 }}>Distributor Network Analysis</div>
          </div>

          <h1 style={{
            fontSize:36, fontWeight:700, color:'#F8FAFC',
            lineHeight:1.2, marginBottom:16,
          }}>
            Pan-India<br />
            <span style={{ color:'#F59E0B' }}>Distribution Intelligence</span>
          </h1>
          <p style={{ color:'#94A3B8', fontSize:15, lineHeight:1.7, marginBottom:40 }}>
            Visualize your distributor network, identify untapped market pockets,
            and manage territory boundaries — all in one platform.
          </p>

          {/* Stats row */}
          <div style={{ display:'flex', gap:32 }}>
            {[
              { val:'5,800+', label:'Touchpoints' },
              { val:'25',     label:'Cities Covered' },
              { val:'414K',   label:'Grid Cells' },
            ].map(({ val, label }) => (
              <div key={label}>
                <div style={{ fontSize:22, fontWeight:700, color:'#F59E0B', fontFamily:'var(--font-mono)' }}>{val}</div>
                <div style={{ fontSize:11, color:'#64748B', marginTop:2 }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right login form */}
      <div style={{
        width:420, background:'#fff',
        display:'flex', alignItems:'center', justifyContent:'center',
        padding:48,
      }}>
        <div style={{ width:'100%', maxWidth:340 }} className="fade-in">
          <h2 style={{ fontSize:22, fontWeight:700, color:'var(--text-dark)', marginBottom:6 }}>
            Sign in
          </h2>
          <p style={{ color:'var(--text-muted)', fontSize:13, marginBottom:28 }}>
            Enter your credentials to access the platform
          </p>

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom:16 }}>
              <label style={{ display:'block', fontSize:12, fontWeight:600, color:'var(--text-dark)', marginBottom:6 }}>
                Email address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@marutisuzuki.com"
                required
                autoFocus
                style={{
                  width:'100%', padding:'10px 12px',
                  border:'1.5px solid var(--border)',
                  borderRadius:8, fontSize:14,
                  outline:'none', transition:'var(--transition)',
                  fontFamily:'var(--font-body)',
                  color:'var(--text-dark)',
                }}
                onFocus={(e) => e.target.style.borderColor='var(--primary)'}
                onBlur={(e) => e.target.style.borderColor='var(--border)'}
              />
            </div>

            <div style={{ marginBottom:24 }}>
              <label style={{ display:'block', fontSize:12, fontWeight:600, color:'var(--text-dark)', marginBottom:6 }}>
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width:'100%', padding:'10px 12px',
                  border:'1.5px solid var(--border)',
                  borderRadius:8, fontSize:14,
                  outline:'none', transition:'var(--transition)',
                  fontFamily:'var(--font-body)',
                  color:'var(--text-dark)',
                }}
                onFocus={(e) => e.target.style.borderColor='var(--primary)'}
                onBlur={(e) => e.target.style.borderColor='var(--border)'}
              />
            </div>

            {error && (
              <div style={{
                padding:'10px 12px', borderRadius:8, marginBottom:16,
                background:'#FEE2E2', border:'1px solid #FECACA',
                color:'#B91C1C', fontSize:13, lineHeight:1.4,
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                width:'100%', padding:'11px', borderRadius:8,
                background: loading ? '#93C5FD' : 'var(--primary)',
                color:'#fff', border:'none', cursor: loading ? 'not-allowed' : 'pointer',
                fontSize:14, fontWeight:600,
                display:'flex', alignItems:'center', justifyContent:'center', gap:8,
                transition:'var(--transition)',
              }}
              onMouseEnter={(e) => { if(!loading) e.currentTarget.style.background='var(--primary-lt)' }}
              onMouseLeave={(e) => { if(!loading) e.currentTarget.style.background='var(--primary)' }}
            >
              {loading && <span className="spinner" style={{ width:16, height:16, borderTopColor:'#fff', borderColor:'rgba(255,255,255,.4)' }} />}
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <div style={{
            marginTop:28, padding:'12px 14px',
            background:'#F8FAFC', borderRadius:8,
            border:'1px solid var(--border)',
          }}>
            <div style={{ fontSize:11, fontWeight:700, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'.4px', marginBottom:6 }}>
              Demo accounts
            </div>
            {[
              { role:'Admin',       email:'rahul.sharma@marutisuzuki.com', pw:'AdminPass@123' },
              { role:'Distributor', email:'dist.mumbai1@partner.com',       pw:'DistPass@001' },
            ].map(({ role, email: e, pw }) => (
              <div key={role} style={{ marginBottom:4 }}>
                <button
                  onClick={() => { setEmail(e); setPassword(pw) }}
                  style={{
                    background:'none', border:'none', padding:0,
                    cursor:'pointer', fontSize:11, color:'var(--primary)',
                    textAlign:'left', fontFamily:'var(--font-body)',
                  }}
                >
                  <span style={{ fontWeight:600, color:'var(--text-muted)' }}>{role}: </span>
                  {e}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
