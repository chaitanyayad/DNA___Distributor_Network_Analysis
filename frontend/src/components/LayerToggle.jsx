const TYPE_META = {
  'Mother Warehouse':     { color:'#7C3AED', label:'Mother WH' },
  'Additional Warehouse': { color:'#06B6D4', label:'Add. WH' },
  'Retail Office':        { color:'#16A34A', label:'Retail Office' },
  'Dealer':               { color:'#2563EB', label:'Dealer' },
  'Independent Workshop': { color:'#F97316', label:'Workshop' },
  'MASS':                 { color:'#E11D48', label:'MASS' },
}

export default function LayerToggle({ visible, onChange, showHeatmap, onHeatmapToggle, showWhitespace, onWhitespaceToggle }) {
  return (
    <div style={{
      position:'absolute', right:12, top:12, zIndex:10,
      background:'rgba(255,255,255,.94)', backdropFilter:'blur(12px)',
      border:'1px solid var(--border)',
      borderRadius:10, padding:'12px 14px',
      boxShadow:'var(--shadow-md)',
      minWidth:160,
      animation:'slideIn 200ms ease both',
    }}>
      <div style={{ fontSize:10, fontWeight:700, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'.5px', marginBottom:10 }}>
        Layers
      </div>

      {/* Entity types */}
      {Object.entries(TYPE_META).map(([type, { color, label }]) => (
        <label key={type} style={{
          display:'flex', alignItems:'center', gap:8, marginBottom:6,
          cursor:'pointer', userSelect:'none',
        }}>
          <input
            type="checkbox"
            checked={visible.has(type)}
            onChange={() => onChange(type)}
            style={{ display:'none' }}
          />
          <div style={{
            width:14, height:14, borderRadius:3, flexShrink:0,
            background: visible.has(type) ? color : '#E2E8F0',
            border: `2px solid ${visible.has(type) ? color : '#CBD5E1'}`,
            transition:'var(--transition)',
          }} />
          <span style={{ fontSize:12, color: visible.has(type) ? 'var(--text-dark)' : 'var(--text-muted)' }}>
            {label}
          </span>
        </label>
      ))}

      <div style={{ borderTop:'1px solid var(--border)', margin:'8px 0' }} />

      {/* Heatmap toggle */}
      <label style={{ display:'flex', alignItems:'center', gap:8, marginBottom:6, cursor:'pointer', userSelect:'none' }}>
        <div onClick={onHeatmapToggle} style={{
          width:32, height:18, borderRadius:999, flexShrink:0,
          background: showHeatmap ? 'var(--cta)' : '#CBD5E1',
          position:'relative', transition:'var(--transition)', cursor:'pointer',
        }}>
          <div style={{
            width:14, height:14, borderRadius:'50%', background:'#fff',
            position:'absolute', top:2,
            left: showHeatmap ? 16 : 2,
            transition:'var(--transition)',
            boxShadow:'0 1px 3px rgba(0,0,0,.2)',
          }} />
        </div>
        <span style={{ fontSize:12, color:'var(--text-dark)' }}>Heatmap</span>
      </label>

      {/* Whitespace toggle */}
      <label style={{ display:'flex', alignItems:'center', gap:8, cursor:'pointer', userSelect:'none' }}>
        <div onClick={onWhitespaceToggle} style={{
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
        <span style={{ fontSize:12, color:'var(--text-dark)' }}>Untapped Pockets</span>
      </label>
    </div>
  )
}

export { TYPE_META }
