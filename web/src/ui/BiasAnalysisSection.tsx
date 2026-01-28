import React, { useState } from 'react'

// Types for bias analysis data
interface BiasInstance {
  type: string
  severity: 'low' | 'moderate' | 'high'
  excerpt: string
  explanation: string
  suggestion: string
  section?: string
}

interface BiasAnalysisData {
  overall_score: number
  severity: 'low' | 'moderate' | 'high'
  summary: string
  biases: BiasInstance[]
  strengths: string[]
  error?: string
}

interface BiasAnalysisSectionProps {
  data: BiasAnalysisData | null
  loading?: boolean
}

// Severity color mapping
const severityColors = {
  low: { bg: '#dcfce7', border: '#22c55e', text: '#166534', icon: '🟢' },
  moderate: { bg: '#fef9c3', border: '#eab308', text: '#854d0e', icon: '🟡' },
  high: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b', icon: '🔴' }
}

// Bias type icons
const biasIcons: Record<string, string> = {
  'Confirmation Bias': '🎯',
  'Selection Bias': '🎲',
  'Publication Bias': '📰',
  'Funding Bias': '💰',
  'Citation Bias': '📚',
  'Methodology Bias': '🔬',
  'Unknown': '❓'
}

const panel: React.CSSProperties = {
  background: 'var(--panel)',
  boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
  borderRadius: 8,
  padding: 16,
  border: '1px solid rgba(0,0,0,0.05)'
}

function ScoreGauge({ score }: { score: number }) {
  // Score is 0-100 where lower is better (less biased)
  const getSeverity = (s: number): 'low' | 'moderate' | 'high' => {
    if (s <= 25) return 'low'
    if (s <= 50) return 'moderate'
    return 'high'
  }
  
  const severity = getSeverity(score)
  const colors = severityColors[severity]
  
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <div style={{
        width: 80,
        height: 80,
        borderRadius: '50%',
        border: `4px solid ${colors.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: colors.bg
      }}>
        <span style={{ fontSize: 24, fontWeight: 700, color: colors.text }}>
          {score}
        </span>
      </div>
      <div>
        <div style={{ fontWeight: 600, fontSize: 18 }}>Bias Score</div>
        <div style={{ 
          color: colors.text, 
          background: colors.bg, 
          padding: '2px 8px', 
          borderRadius: 4,
          display: 'inline-block',
          marginTop: 4
        }}>
          {severity.charAt(0).toUpperCase() + severity.slice(1)} Bias Level
        </div>
      </div>
    </div>
  )
}

function BiasCard({ bias, isExpanded, onToggle }: { 
  bias: BiasInstance
  isExpanded: boolean
  onToggle: () => void 
}) {
  const colors = severityColors[bias.severity]
  const icon = biasIcons[bias.type] || biasIcons['Unknown']
  
  return (
    <div style={{
      border: `1px solid ${colors.border}`,
      borderRadius: 8,
      marginBottom: 12,
      overflow: 'hidden',
      background: '#fff'
    }}>
      <div 
        onClick={onToggle}
        style={{
          padding: '12px 16px',
          background: colors.bg,
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 20 }}>{icon}</span>
          <span style={{ fontWeight: 600 }}>{bias.type}</span>
          <span style={{
            background: colors.border,
            color: '#fff',
            padding: '2px 8px',
            borderRadius: 12,
            fontSize: 12,
            fontWeight: 500
          }}>
            {bias.severity}
          </span>
        </div>
        <span style={{ 
          transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.2s'
        }}>
          ▼
        </span>
      </div>
      
      {isExpanded && (
        <div style={{ padding: 16 }}>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 4, color: '#666' }}>
              Excerpt:
            </div>
            <div style={{
              background: '#f5f5f5',
              padding: '8px 12px',
              borderRadius: 4,
              fontStyle: 'italic',
              borderLeft: `3px solid ${colors.border}`
            }}>
              "{bias.excerpt}"
            </div>
          </div>
          
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 4, color: '#666' }}>
              Why it's biased:
            </div>
            <div>{bias.explanation}</div>
          </div>
          
          <div style={{
            background: '#e0f2fe',
            padding: '8px 12px',
            borderRadius: 4,
            display: 'flex',
            alignItems: 'flex-start',
            gap: 8
          }}>
            <span style={{ fontSize: 18 }}>💡</span>
            <div>
              <div style={{ fontWeight: 600, marginBottom: 2 }}>Suggestion:</div>
              <div>{bias.suggestion}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div style={{ ...panel, marginBottom: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <div style={{
          width: 80,
          height: 80,
          borderRadius: '50%',
          background: 'linear-gradient(90deg, #e5e1d5 25%, #f0ede5 50%, #e5e1d5 75%)',
          backgroundSize: '200% 100%',
          animation: 'shimmer 1.5s infinite'
        }} />
        <div>
          <div style={{
            width: 100,
            height: 20,
            borderRadius: 4,
            background: '#e5e1d5',
            marginBottom: 8
          }} />
          <div style={{
            width: 150,
            height: 16,
            borderRadius: 4,
            background: '#e5e1d5'
          }} />
        </div>
      </div>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 8,
        color: 'var(--accent)'
      }}>
        <div className="spinner" style={{
          width: 20,
          height: 20,
          border: '2px solid var(--accent)',
          borderTopColor: 'transparent',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
        <span>Analyzing with AI...</span>
      </div>
      <style>{`
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

export default function BiasAnalysisSection({ data, loading }: BiasAnalysisSectionProps) {
  const [expandedBiases, setExpandedBiases] = useState<Set<number>>(new Set())
  const [showStrengths, setShowStrengths] = useState(false)
  
  if (loading) {
    return <LoadingSkeleton />
  }
  
  if (!data) {
    return null
  }
  
  if (data.error && !data.biases.length) {
    return (
      <div style={{ ...panel, marginBottom: 16, borderColor: '#fbbf24' }}>
        <h2 style={{ margin: '0 0 8px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
          ⚠️ Bias Analysis Unavailable
        </h2>
        <p style={{ margin: 0, color: '#666' }}>
          {data.error === 'Bias analysis disabled - no API key' 
            ? 'Bias analysis requires a Gemini API key. Please configure GEMINI_API_KEY in the backend.'
            : data.summary || 'Unable to perform bias analysis at this time.'}
        </p>
      </div>
    )
  }
  
  const toggleBias = (index: number) => {
    const newExpanded = new Set(expandedBiases)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedBiases(newExpanded)
  }
  
  return (
    <div style={{ ...panel, marginBottom: 16 }}>
      <h2 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
        📊 AI Bias Analysis
      </h2>
      
      {/* Score and Summary */}
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        gap: 16,
        marginBottom: 20,
        paddingBottom: 20,
        borderBottom: '1px solid rgba(0,0,0,0.1)'
      }}>
        <ScoreGauge score={data.overall_score} />
        <div style={{ 
          background: '#f8f7f4', 
          padding: 12, 
          borderRadius: 6,
          lineHeight: 1.5
        }}>
          {data.summary}
        </div>
      </div>
      
      {/* Detected Biases */}
      {data.biases.length > 0 ? (
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ margin: '0 0 12px 0' }}>
            Detected Biases ({data.biases.length})
          </h3>
          {data.biases.map((bias, index) => (
            <BiasCard
              key={index}
              bias={bias}
              isExpanded={expandedBiases.has(index)}
              onToggle={() => toggleBias(index)}
            />
          ))}
        </div>
      ) : (
        <div style={{ 
          background: severityColors.low.bg, 
          padding: 16, 
          borderRadius: 8,
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 12
        }}>
          <span style={{ fontSize: 32 }}>✅</span>
          <div>
            <div style={{ fontWeight: 600, color: severityColors.low.text }}>
              No Significant Biases Detected
            </div>
            <div style={{ color: '#666' }}>
              The paper appears to follow good practices for objectivity.
            </div>
          </div>
        </div>
      )}
      
      {/* Strengths */}
      {data.strengths.length > 0 && (
        <div>
          <div 
            onClick={() => setShowStrengths(!showStrengths)}
            style={{ 
              cursor: 'pointer',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '8px 0'
            }}
          >
            <h3 style={{ margin: 0, color: severityColors.low.text }}>
              ✅ Strengths ({data.strengths.length})
            </h3>
            <span style={{ 
              transform: showStrengths ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s'
            }}>
              ▼
            </span>
          </div>
          
          {showStrengths && (
            <ul style={{ 
              margin: '8px 0 0 0', 
              paddingLeft: 24,
              background: severityColors.low.bg,
              padding: '12px 12px 12px 32px',
              borderRadius: 8
            }}>
              {data.strengths.map((strength, index) => (
                <li key={index} style={{ marginBottom: 4, color: severityColors.low.text }}>
                  {strength}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
