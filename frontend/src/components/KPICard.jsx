export default function KPICard({ label, value, sub, accent, icon: Icon, loading }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,.92)',
      backdropFilter: 'blur(12px)',
      border: '1px solid var(--border)',
      borderRadius: 10,
      padding: '14px 16px',
      minWidth: 160,
      boxShadow: 'var(--shadow-sm)',
      borderTop: `3px solid ${accent || 'var(--primary)'}`,
      animation: 'fadeIn 300ms ease both',
    }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:6 }}>
        <span style={{ fontSize:11, fontWeight:600, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'.5px' }}>
          {label}
        </span>
        {Icon && <Icon style={{ width:16, height:16, color: accent || 'var(--primary)', opacity:.7 }} />}
      </div>
      {loading ? (
        <div style={{ height:28, display:'flex', alignItems:'center' }}>
          <div className="spinner" style={{ width:16, height:16 }} />
        </div>
      ) : (
        <>
          <div style={{
            fontSize: 22, fontWeight: 700,
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-dark)',
            lineHeight: 1.2,
          }}>
            {value ?? '—'}
          </div>
          {sub && (
            <div style={{ fontSize:11, color:'var(--text-muted)', marginTop:2 }}>{sub}</div>
          )}
        </>
      )}
    </div>
  )
}
