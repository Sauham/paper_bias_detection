import React, { useState } from 'react'
import axios from 'axios'
import BiasAnalysisSection from './BiasAnalysisSection'

const panel: React.CSSProperties = {
  background: 'var(--panel)',
  boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
  borderRadius: 8,
  padding: 16,
  border: '1px solid rgba(0,0,0,0.05)'
}

function Section({name, data}: {name: string, data: any}){
  const [expanded, setExpanded] = useState(false)
  
  return (
    <div style={{...panel, marginBottom: 16}}>
      <div 
        style={{
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          cursor: 'pointer',
          padding: '8px 0'
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <h3 style={{margin: 0}}>{name} — {data?.best_similarity_percent?.toFixed(2)}%</h3>
        <div style={{
          fontSize: '20px',
          color: 'var(--accent)',
          transition: 'transform 0.2s',
          transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)'
        }}>
          ▼
        </div>
      </div>
      
      {expanded && (
        <div style={{marginTop: 16, borderTop: '1px solid rgba(0,0,0,0.1)', paddingTop: 16}}>
          <div style={{fontStyle:'italic', color:'#6b5b53', marginBottom: 12}}>{data?.category}</div>
          {data?.matches?.length ? (
            <table style={{width:'100%'}}>
              <thead>
                <tr>
                  <th align="left">% Match</th>
                  <th align="left">Title</th>
                  <th align="left">Link</th>
                </tr>
              </thead>
              <tbody>
                {data.matches.map((m: any, i: number) => (
                  <tr key={i}>
                    <td>{m.percent.toFixed(2)}%</td>
                    <td>{m.title}</td>
                    <td><a href={m.url} style={{color:'var(--accent)'}} target="_blank">Open</a></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{color:'#6b5b53'}}>No close matches found.</div>
          )}
        </div>
      )}
    </div>
  )
}

export default function App(){
  const [file, setFile] = useState<File|null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string|null>(null)
  const [report, setReport] = useState<any>(null)

  const onUpload = async () => {
    if(!file) return
    setLoading(true); setError(null); setReport(null)
    try{
      const form = new FormData()
      form.append('file', file)
      const resp = await axios.post('/analyze', form, { baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000', headers: { 'Content-Type': 'multipart/form-data' } })
      setReport(resp.data)
    }catch(e:any){
      setError(e?.response?.data?.error || e.message)
    }finally{
      setLoading(false)
    }
  }

  // Extract plagiarism data (handles both old and new response format)
  const plagiarismData = report?.plagiarism || report
  const biasData = report?.bias_analysis || null

  return (
    <div style={{maxWidth: 1100, margin:'0 auto', padding: 24}}>
      <header style={{marginBottom: 24}}>
        <h1 style={{margin:0}}>Research Paper Plagiarism & Bias Analysis</h1>
        <div style={{color:'#6b5b53'}}>Powered by AI-driven bias detection</div>
      </header>

      <div style={{display:'grid', gridTemplateColumns:'1fr', gap: 16}}>
        <div style={panel}>
          <h3 style={{marginTop:0}}>Upload Academic Paper (PDF)</h3>
          <input type="file" accept="application/pdf" onChange={e=> setFile(e.target.files?.[0] || null)} />
          <button onClick={onUpload} disabled={!file || loading} style={{marginLeft:12, background:'var(--accent)', color:'white', border:'none', padding:'8px 14px', borderRadius:6, cursor: !file || loading ? 'not-allowed' : 'pointer', opacity: !file || loading ? 0.6 : 1}}>
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
          {error && <div style={{color:'#a00000', marginTop:8}}>{error}</div>}
        </div>

        {report && (
          <>
            {/* Plagiarism Results */}
            <div style={panel}>
              <h2 style={{marginTop:0}}>📋 Plagiarism Analysis</h2>
              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div style={{fontSize: 28, fontWeight: 700}}>{plagiarismData?.overall_percent?.toFixed(2)}%</div>
                <div style={{color:'#6b5b53'}}>{plagiarismData?.overall_category}</div>
              </div>
            </div>

            <Section name="Title" data={plagiarismData?.sections?.Title} />
            <Section name="Abstract" data={plagiarismData?.sections?.Abstract} />
            <Section name="Methodology" data={plagiarismData?.sections?.Methodology} />
            <Section name="Conclusions" data={plagiarismData?.sections?.Conclusions} />

            {/* Bias Analysis Results */}
            <BiasAnalysisSection data={biasData} loading={false} />
          </>
        )}

        {loading && (
          <BiasAnalysisSection data={null} loading={true} />
        )}
      </div>
    </div>
  )
}
