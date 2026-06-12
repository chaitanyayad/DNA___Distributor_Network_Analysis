import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'

const IconMap      = () => <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><path d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 13l4.553 2.276A1 1 0 0021 21.382V10.618a1 1 0 00-1.447-.894L15 12m0 8V12m0 0L9 7"/></svg>
const IconTerritory= () => <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>
const IconApproval = () => <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
const IconZone     = () => <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2a10 10 0 100 20A10 10 0 0012 2z"/><path d="M12 2C8 6 8 18 12 22M12 2c4 4 4 16 0 20M2 12h20"/></svg>
const IconRequest  = () => <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><path d="M12 5v14m7-7H5"/></svg>
const IconLogout   = () => <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4m7 14l5-5-5-5m5 5H9"/></svg>

const ADMIN_NAV = [
  { to: '/dashboard',   label: 'Dashboard',   Icon: IconMap },
  { to: '/territories', label: 'Territories',  Icon: IconTerritory },
  { to: '/approvals',   label: 'Approvals',    Icon: IconApproval },
]
const DIST_NAV = [
  { to: '/my-territory', label: 'My Territory', Icon: IconZone },
  { to: '/request-ro',   label: 'Request RO',   Icon: IconRequest },
]

export default function AppLayout({ children }) {
  const { auth, logout, isAdmin } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    try { await client.post('/api/auth/logout') } catch {}
    logout()
    navigate('/login')
  }

  const navItems = isAdmin ? ADMIN_NAV : DIST_NAV

  return (
    <div style={{ display:'flex', height:'100vh', overflow:'hidden' }}>
      {/* Sidebar */}
      <aside style={{
        width: 220, flexShrink: 0,
        background: 'var(--sidebar-bg)',
        display: 'flex', flexDirection: 'column',
        borderRight: '1px solid rgba(255,255,255,.06)',
      }}>
        {/* Logo */}
        <div style={{ padding:'20px 16px 12px', borderBottom:'1px solid rgba(255,255,255,.08)' }}>
          <div style={{ display:'flex', alignItems:'center', gap:10 }}>
            <div style={{
              width:36, height:36, borderRadius:8,
              background:'var(--cta)',
              display:'flex', alignItems:'center', justifyContent:'center',
              fontFamily:'var(--font-mono)', fontWeight:700, fontSize:13, color:'#fff',
            }}>MS</div>
            <div>
              <div style={{ color:'#F8FAFC', fontSize:12, fontWeight:700, lineHeight:1.2 }}>Maruti Suzuki</div>
              <div style={{ color:'#64748B', fontSize:10, fontWeight:500 }}>Distributor Network</div>
            </div>
          </div>
        </div>

        {/* Role badge */}
        <div style={{ padding:'10px 16px 4px' }}>
          <span className={`badge ${isAdmin ? 'badge-amber' : 'badge-blue'}`} style={{ fontSize:10 }}>
            {isAdmin ? 'Org Admin' : 'Distributor'}
          </span>
        </div>

        {/* Nav */}
        <nav style={{ flex:1, padding:'8px 8px', overflowY:'auto' }}>
          {navItems.map(({ to, label, Icon }) => (
            <NavLink key={to} to={to} style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '9px 10px', borderRadius: 6, marginBottom: 2,
              color: isActive ? '#F8FAFC' : '#94A3B8',
              background: isActive ? 'var(--sidebar-hover)' : 'transparent',
              textDecoration: 'none', fontSize: 13, fontWeight: isActive ? 600 : 400,
              transition: 'var(--transition)', cursor: 'pointer',
              borderLeft: isActive ? '3px solid var(--cta)' : '3px solid transparent',
            })}>
              <Icon />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div style={{
          padding: '12px 12px',
          borderTop: '1px solid rgba(255,255,255,.08)',
        }}>
          <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:8 }}>
            <div style={{
              width:30, height:30, borderRadius:'50%',
              background:'var(--primary)',
              display:'flex', alignItems:'center', justifyContent:'center',
              color:'#fff', fontSize:12, fontWeight:700, flexShrink:0,
            }}>
              {auth?.username?.[0]?.toUpperCase() || 'U'}
            </div>
            <div style={{ overflow:'hidden' }}>
              <div style={{ color:'#E2E8F0', fontSize:12, fontWeight:600, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>
                {auth?.username || 'User'}
              </div>
              {auth?.distributorId && (
                <div style={{ color:'#64748B', fontSize:10, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis', fontFamily:'var(--font-mono)' }}>
                  {auth.distributorId}
                </div>
              )}
            </div>
          </div>
          <button onClick={handleLogout} style={{
            display:'flex', alignItems:'center', gap:6,
            width:'100%', padding:'7px 8px', borderRadius:6,
            background:'rgba(220,38,38,.12)', color:'#F87171',
            border:'none', cursor:'pointer', fontSize:12, fontWeight:500,
            transition:'var(--transition)',
          }}
          onMouseEnter={e => e.currentTarget.style.background='rgba(220,38,38,.22)'}
          onMouseLeave={e => e.currentTarget.style.background='rgba(220,38,38,.12)'}
          >
            <IconLogout /> Sign Out
          </button>
        </div>
      </aside>

      {/* Main area */}
      <main style={{ flex:1, overflow:'hidden', display:'flex', flexDirection:'column' }}>
        {children}
      </main>
    </div>
  )
}
