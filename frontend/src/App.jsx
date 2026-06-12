import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'

import Login               from './pages/Login'
import AdminDashboard      from './pages/AdminDashboard'
import TerritoryManager    from './pages/TerritoryManager'
import Approvals           from './pages/Approvals'
import DistributorDashboard from './pages/DistributorDashboard'
import RORequest           from './pages/RORequest'

function RootRedirect() {
  const { auth } = useAuth()
  if (!auth)            return <Navigate to="/login" replace />
  if (auth.role === 'org_admin') return <Navigate to="/dashboard" replace />
  return <Navigate to="/my-territory" replace />
}

function Forbidden() {
  return (
    <div style={{
      minHeight:'100vh', display:'flex', alignItems:'center', justifyContent:'center',
      flexDirection:'column', gap:12, background:'var(--bg)',
    }}>
      <div style={{ fontSize:48, fontFamily:'var(--font-mono)', fontWeight:700, color:'var(--danger)' }}>403</div>
      <div style={{ fontSize:18, fontWeight:700, color:'var(--text-dark)' }}>Access Denied</div>
      <div style={{ fontSize:14, color:'var(--text-muted)' }}>You don't have permission to view this page.</div>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login"   element={<Login />} />
          <Route path="/forbidden" element={<Forbidden />} />
          <Route path="/" element={<RootRedirect />} />

          {/* Admin routes */}
          <Route path="/dashboard"   element={<ProtectedRoute role="org_admin"><AdminDashboard /></ProtectedRoute>} />
          <Route path="/territories" element={<ProtectedRoute role="org_admin"><TerritoryManager /></ProtectedRoute>} />
          <Route path="/approvals"   element={<ProtectedRoute role="org_admin"><Approvals /></ProtectedRoute>} />

          {/* Distributor routes */}
          <Route path="/my-territory" element={<ProtectedRoute role="distributor_user"><DistributorDashboard /></ProtectedRoute>} />
          <Route path="/request-ro"   element={<ProtectedRoute role="distributor_user"><RORequest /></ProtectedRoute>} />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
