import { useEffect, useRef, useCallback, useState } from 'react'
import maplibregl from 'maplibre-gl'
import client from '../../api/client'

const INDIA_CENTER = [78.9629, 20.5937]
const INDIA_ZOOM   = 5.2
const MAP_STYLE    = 'https://tiles.openfreemap.org/styles/liberty'

const TYPE_COLORS = {
  'Mother Warehouse':     '#7C3AED',
  'Additional Warehouse': '#06B6D4',
  'Retail Office':        '#16A34A',
  'Dealer':               '#2563EB',
  'Independent Workshop': '#F97316',
  'MASS':                 '#E11D48',
}

const TYPE_RADIUS = {
  'Mother Warehouse':     12,
  'Additional Warehouse': 10,
  'Retail Office':        9,
  'Dealer':               8,
  'Independent Workshop': 6,
  'MASS':                 8,
}

function buildPopupHTML(props) {
  const color = TYPE_COLORS[props.type] || '#64748B'
  return `
    <div style="padding:12px 14px">
      <div style="display:flex;align-items:center;gap:6;margin-bottom:8px">
        <div style="width:10px;height:10px;border-radius:50%;background:${color};flex-shrink:0"></div>
        <span style="font-size:10px;font-weight:700;color:${color};text-transform:uppercase;letter-spacing:.5px">${props.type}</span>
      </div>
      <div style="font-size:13px;font-weight:700;color:#0F172A;margin-bottom:6px;line-height:1.3">${props.name}</div>
      <div style="font-size:11px;color:#475569;margin-bottom:2px">${props.city || ''}${props.state ? ', ' + props.state : ''}</div>
      ${props.address ? `<div style="font-size:11px;color:#64748B;margin-bottom:4px">${props.address}</div>` : ''}
      ${props.contact_person ? `<div style="font-size:11px;color:#0F172A;margin-top:6px;font-weight:600">${props.contact_person}</div>` : ''}
      ${props.phone ? `<div style="font-size:11px;color:#2563EB;font-family:'Fira Code',monospace">${props.phone}</div>` : ''}
      <div style="margin-top:8px">
        <span style="display:inline-block;padding:2px 8px;border-radius:999px;font-size:10px;font-weight:600;
          background:${props.active ? '#DCFCE7' : '#FEE2E2'};color:${props.active ? '#15803D' : '#B91C1C'}">
          ${props.active ? 'Active' : 'Inactive'}
        </span>
      </div>
    </div>
  `
}

export default function MainMap({
  visibleTypes,
  showHeatmap,
  showWhitespace,
  showTerritories = true,
  territoriesVersion = 0,
  mode = 'view',           // 'view' | 'draw' | 'ro-request'
  onPolygonDraw,           // (geojson polygon) => void
  onPinDrop,               // (lat, lng) => void
  droppedPin,              // { lat, lng } | null
  fitBounds,               // [[minLon,minLat],[maxLon,maxLat]] | null
}) {
  const containerRef = useRef(null)
  const mapRef       = useRef(null)
  const popupRef     = useRef(null)
  const drawPointsRef = useRef([])
  const markersRef    = useRef([])
  const [drawPointCount, setDrawPointCount] = useState(0)
  const pinMarkerRef  = useRef(null)
  const fetchTimerRef = useRef(null)

  const [mapReady, setMapReady] = useState(false)

  // ── Initialize map ──────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: containerRef.current,
      style:     MAP_STYLE,
      center:    INDIA_CENTER,
      zoom:      INDIA_ZOOM,
      minZoom:   3,
      maxZoom:   18,
    })

    map.addControl(new maplibregl.NavigationControl(), 'bottom-right')
    map.addControl(new maplibregl.ScaleControl({ maxWidth:100, unit:'metric' }), 'bottom-left')

    popupRef.current = new maplibregl.Popup({ closeButton:true, closeOnClick:false, maxWidth:'280px' })

    map.on('load', () => {
      // ── Sources ──────────────────────────────────────────────────────
      map.addSource('locations', {
        type: 'geojson',
        data: { type:'FeatureCollection', features:[] },
        cluster:           true,
        clusterMaxZoom:    8,
        clusterRadius:     25,
      })

      map.addSource('hotspots', {
        type: 'geojson',
        data: { type:'FeatureCollection', features:[] },
      })

      map.addSource('whitespace', {
        type: 'geojson',
        data: { type:'FeatureCollection', features:[] },
      })

      map.addSource('territories', {
        type: 'geojson',
        data: { type:'FeatureCollection', features:[] },
      })

      map.addSource('draw-preview', {
        type: 'geojson',
        data: { type:'FeatureCollection', features:[] },
      })

      // ── Heatmap layer ─────────────────────────────────────────────────
      map.addLayer({
        id:     'hotspot-heat',
        type:   'heatmap',
        source: 'hotspots',
        layout: { visibility:'none' },
        paint: {
          'heatmap-weight':     ['interpolate',['linear'],['get','hotspot_score'],0,0,1,1],
          'heatmap-intensity':  ['interpolate',['linear'],['zoom'],0,1,9,3],
          'heatmap-color': [
            'interpolate',['linear'],['heatmap-density'],
            0,'rgba(33,102,172,0)',
            0.2,'#2166ac',
            0.4,'#4dac26',
            0.6,'#f4e842',
            0.8,'#f97316',
            1,'#dc2626'
          ],
          'heatmap-radius':   ['interpolate',['linear'],['zoom'],0,4,9,30],
          'heatmap-opacity':  0.75,
        },
      })

      // ── Territory fill/outline ────────────────────────────────────────
      map.addLayer({
        id:'territory-fill', type:'fill', source:'territories',
        paint:{
          'fill-color':   ['case',['get','locked'],'#1E40AF','#3B82F6'],
          'fill-opacity': 0.12,
        },
      })
      map.addLayer({
        id:'territory-line', type:'line', source:'territories',
        paint:{
          'line-color': ['case',['get','locked'],'#1E40AF','#3B82F6'],
          'line-width': 2,
          'line-opacity': 0.8,
        },
      })
      map.addLayer({
        id:'territory-label', type:'symbol', source:'territories',
        layout:{
          'text-field':       ['get','territory_name'],
          'text-size':        11,
          'text-font':        ['Open Sans Semibold','Arial Unicode MS Bold'],
          'text-offset':      [0,0],
          'text-anchor':      'center',
          'symbol-placement': 'point',
        },
        paint:{
          'text-color':'#1E40AF',
          'text-halo-color':'rgba(255,255,255,.85)',
          'text-halo-width':2,
        },
      })

      // ── Cluster circles ───────────────────────────────────────────────
      map.addLayer({
        id:'cluster-circle', type:'circle', source:'locations',
        filter:['has','point_count'],
        paint:{
          'circle-color':  ['step',['get','point_count'],'#93C5FD',50,'#3B82F6',200,'#1E40AF'],
          'circle-radius': ['step',['get','point_count'],16,50,22,200,28],
          'circle-opacity':0.75,
          'circle-stroke-width':2,
          'circle-stroke-color':'#fff',
        },
      })
      map.addLayer({
        id:'cluster-count', type:'symbol', source:'locations',
        filter:['has','point_count'],
        layout:{
          'text-field':'{point_count_abbreviated}',
          'text-size':  11,
          'text-font':  ['Open Sans Bold','Arial Unicode MS Bold'],
        },
        paint:{ 'text-color':'#ffffff' },
      })

      // ── Individual location circles (one layer per type) ─────────────
      Object.entries(TYPE_COLORS).forEach(([type, color]) => {
        const id = `loc-${type.replace(/\s/g,'-')}`
        map.addLayer({
          id, type:'circle', source:'locations',
          filter:['all',['!',['has','point_count']],['==',['get','type'],type]],
          layout:{ visibility:'visible' },
          paint:{
            'circle-color':        color,
            'circle-radius':       TYPE_RADIUS[type] || 6,
            'circle-stroke-width': 1.5,
            'circle-stroke-color': '#fff',
            'circle-opacity':      0.92,
          },
        })

        // Popup on click
        map.on('click', id, (e) => {
          const props = e.features[0].properties
          const coords = e.features[0].geometry.coordinates.slice()
          popupRef.current
            .setLngLat(coords)
            .setHTML(buildPopupHTML(props))
            .addTo(map)
        })
        map.on('mouseenter', id, () => { map.getCanvas().style.cursor = 'pointer' })
        map.on('mouseleave', id, () => { map.getCanvas().style.cursor = '' })
      })

      // ── Whitespace layer ──────────────────────────────────────────────
      map.addLayer({
        id:'whitespace-circles', type:'circle', source:'whitespace',
        layout:{ visibility:'none' },
        paint:{
          'circle-color':        '#8B5CF6',
          'circle-radius':       ['interpolate',['linear'],['get','hotspot_score'],0,8,1,18],
          'circle-stroke-color': '#fff',
          'circle-stroke-width': 2,
          'circle-opacity':      0.75,
        },
      })

      // ── Draw preview layers ───────────────────────────────────────────
      map.addLayer({
        id:'draw-fill', type:'fill', source:'draw-preview',
        filter:['==',['geometry-type'],'Polygon'],
        paint:{ 'fill-color':'#F59E0B', 'fill-opacity':0.15 },
      })
      map.addLayer({
        id:'draw-line', type:'line', source:'draw-preview',
        paint:{ 'line-color':'#F59E0B', 'line-width':2.5, 'line-dasharray':[4,2] },
      })

      // ── Cluster click zoom ────────────────────────────────────────────
      map.on('click','cluster-circle',(e) => {
        const id = e.features[0].properties.cluster_id
        map.getSource('locations').getClusterExpansionZoom(id).then((zoom) => {
          map.easeTo({ center:e.features[0].geometry.coordinates, zoom })
        })
      })

      setMapReady(true)
    })

    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, [])

  // ── Fetch locations when map moves ───────────────────────────────────
  const fetchLocations = useCallback(async () => {
    const map = mapRef.current
    if (!map || !mapReady) return
    const b = map.getBounds()
    const bounds = `${b.getWest()},${b.getSouth()},${b.getEast()},${b.getNorth()}`
    try {
      const { data } = await client.get('/api/locations', { params:{ bounds, limit:2000 } })
      const geojson = {
        type: 'FeatureCollection',
        features: (data.locations || []).map((loc) => ({
          type:'Feature',
          geometry:{ type:'Point', coordinates:[loc.longitude, loc.latitude] },
          properties: loc,
        })),
      }
      map.getSource('locations')?.setData(geojson)
    } catch {}
  }, [mapReady])

  const debouncedFetch = useCallback(() => {
    clearTimeout(fetchTimerRef.current)
    fetchTimerRef.current = setTimeout(fetchLocations, 400)
  }, [fetchLocations])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapReady) return
    map.on('moveend', debouncedFetch)
    fetchLocations()
    return () => map.off('moveend', debouncedFetch)
  }, [mapReady, debouncedFetch, fetchLocations])

  // ── Fetch hotspots — only when heatmap is turned on ─────────────────
  const hotspotLoadedRef = useRef(false)
  useEffect(() => {
    if (!mapReady || !showHeatmap) return
    if (hotspotLoadedRef.current) return
    hotspotLoadedRef.current = true
    async function load() {
      try {
        const { data } = await client.get('/api/analytics/hotspots', { params:{ min_score:0.5, limit:5000 } })
        const geojson = {
          type:'FeatureCollection',
          features: data.map((d) => ({
            type:'Feature',
            geometry:{ type:'Point', coordinates:[d.longitude, d.latitude] },
            properties: d,
          })),
        }
        mapRef.current?.getSource('hotspots')?.setData(geojson)
      } catch {}
    }
    load()
  }, [mapReady, showHeatmap])

  // ── Fetch whitespace — only when layer is turned on ──────────────────
  const wsLoadedRef = useRef(false)
  useEffect(() => {
    if (!mapReady || !showWhitespace) return
    if (wsLoadedRef.current) return
    wsLoadedRef.current = true
    async function load() {
      try {
        const { data } = await client.get('/api/analytics/whitespaces')
        const geojson = {
          type:'FeatureCollection',
          features: data.map((d) => ({
            type:'Feature',
            geometry:{ type:'Point', coordinates:[d.longitude, d.latitude] },
            properties: d,
          })),
        }
        mapRef.current?.getSource('whitespace')?.setData(geojson)
      } catch {}
    }
    load()
  }, [mapReady, showWhitespace])

  // ── Fetch territories ────────────────────────────────────────────────
  useEffect(() => {
    if (!mapReady || !showTerritories) return
    async function load() {
      try {
        const { data } = await client.get('/api/territories')
        const geojson = {
          type:'FeatureCollection',
          features: data.map((t) => ({
            type:'Feature',
            geometry: t.geojson,
            properties: { territory_name:t.territory_name, distributor_id:t.distributor_id, locked:t.locked, id:t.id },
          })),
        }
        mapRef.current?.getSource('territories')?.setData(geojson)
      } catch {}
    }
    load()
  }, [mapReady, showTerritories, territoriesVersion])

  // ── Heatmap visibility ───────────────────────────────────────────────
  useEffect(() => {
    if (!mapReady) return
    mapRef.current?.setLayoutProperty('hotspot-heat','visibility', showHeatmap ? 'visible' : 'none')
  }, [mapReady, showHeatmap])

  // ── Whitespace visibility ────────────────────────────────────────────
  useEffect(() => {
    if (!mapReady) return
    mapRef.current?.setLayoutProperty('whitespace-circles','visibility', showWhitespace ? 'visible' : 'none')
  }, [mapReady, showWhitespace])

  // ── Type layer visibility ────────────────────────────────────────────
  useEffect(() => {
    if (!mapReady) return
    Object.keys(TYPE_COLORS).forEach((type) => {
      const id = `loc-${type.replace(/\s/g,'-')}`
      mapRef.current?.setLayoutProperty(id, 'visibility', visibleTypes?.has(type) ? 'visible' : 'none')
    })
  }, [mapReady, visibleTypes])

  // ── Territory visibility ─────────────────────────────────────────────
  useEffect(() => {
    if (!mapReady) return
    const vis = showTerritories ? 'visible' : 'none'
    ;['territory-fill','territory-line','territory-label'].forEach((id) => {
      mapRef.current?.setLayoutProperty(id,'visibility',vis)
    })
  }, [mapReady, showTerritories])

  // ── fitBounds ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapReady || !fitBounds) return
    mapRef.current?.fitBounds(fitBounds, { padding:60, duration:800 })
  }, [mapReady, fitBounds])

  // ── Drawing mode ─────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapReady) return

    if (mode === 'draw') {
      map.getCanvas().style.cursor = 'crosshair'

      const onClick = (e) => {
        const pt = [e.lngLat.lng, e.lngLat.lat]
        drawPointsRef.current = [...drawPointsRef.current, pt]
        setDrawPointCount(drawPointsRef.current.length)
        updateDrawPreview()

        const el = document.createElement('div')
        el.style.cssText = 'width:10px;height:10px;border-radius:50%;background:#F59E0B;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.3)'
        const m = new maplibregl.Marker({ element:el }).setLngLat(pt).addTo(map)
        markersRef.current.push(m)
      }

      map.on('click', onClick)
      return () => {
        map.off('click', onClick)
        map.getCanvas().style.cursor = ''
      }
    } else if (mode === 'ro-request') {
      map.getCanvas().style.cursor = 'crosshair'
      const onClick = (e) => onPinDrop?.(e.lngLat.lat, e.lngLat.lng)
      map.on('click', onClick)
      return () => { map.off('click', onClick); map.getCanvas().style.cursor = '' }
    } else {
      map.getCanvas().style.cursor = ''
    }
  }, [mapReady, mode, onPinDrop])

  function updateDrawPreview() {
    const pts = drawPointsRef.current
    if (!mapRef.current) return
    let features = []
    if (pts.length >= 2) {
      features.push({ type:'Feature', geometry:{ type:'LineString', coordinates:pts } })
    }
    if (pts.length >= 3) {
      features.push({ type:'Feature', geometry:{ type:'Polygon', coordinates:[[...pts, pts[0]]] } })
    }
    mapRef.current.getSource('draw-preview')?.setData({ type:'FeatureCollection', features })
  }

  function completePolygon() {
    const pts = drawPointsRef.current
    if (pts.length < 3) return
    const polygon = { type:'Polygon', coordinates:[[...pts, pts[0]]] }
    onPolygonDraw?.(polygon)
    clearDraw()
  }

  function clearDraw() {
    drawPointsRef.current = []
    setDrawPointCount(0)
    markersRef.current.forEach((m) => m.remove())
    markersRef.current = []
    mapRef.current?.getSource('draw-preview')?.setData({ type:'FeatureCollection', features:[] })
  }

  // ── Dropped pin for RO request ────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapReady) return
    if (pinMarkerRef.current) { pinMarkerRef.current.remove(); pinMarkerRef.current = null }
    if (!droppedPin) return
    const el = document.createElement('div')
    el.style.cssText = `
      width:24px;height:24px;border-radius:50%;
      background:var(--primary);border:3px solid #fff;
      box-shadow:0 2px 8px rgba(0,0,0,.4);
      cursor:pointer;
    `
    pinMarkerRef.current = new maplibregl.Marker({ element:el })
      .setLngLat([droppedPin.lng, droppedPin.lat])
      .addTo(map)
    map.easeTo({ center:[droppedPin.lng, droppedPin.lat], zoom:Math.max(map.getZoom(), 11), duration:600 })
  }, [mapReady, droppedPin])

  return (
    <div style={{ position:'relative', width:'100%', height:'100%' }}>
      <div ref={containerRef} style={{ width:'100%', height:'100%' }} />

      {mode === 'draw' && (
        <div style={{
          position:'absolute', bottom:40, left:'50%', transform:'translateX(-50%)',
          display:'flex', gap:8, zIndex:20,
        }}>
          <button
            onClick={completePolygon}
            disabled={drawPointCount < 3}
            style={{
              padding:'8px 20px', borderRadius:6, border:'none', cursor:'pointer',
              background:'var(--cta)', color:'#fff', fontWeight:600, fontSize:13,
              boxShadow:'var(--shadow-md)', opacity: drawPointCount < 3 ? .5 : 1,
              transition:'var(--transition)',
            }}>
            Complete Polygon
          </button>
          <button onClick={clearDraw} style={{
            padding:'8px 16px', borderRadius:6, border:'1px solid var(--border)',
            background:'#fff', cursor:'pointer', fontWeight:500, fontSize:13,
            boxShadow:'var(--shadow-sm)',
          }}>
            Clear
          </button>
        </div>
      )}
    </div>
  )
}
