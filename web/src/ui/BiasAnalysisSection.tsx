import React, { useState, useRef, useEffect } from 'react'

// Custom hook for scroll-based animations
function useScrollAnimation(direction: 'up' | 'down' | 'left' | 'right' = 'up', threshold = 0.1) {
  const ref = useRef<HTMLDivElement>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
        }
      },
      { threshold, rootMargin: '0px 0px -30px 0px' }
    )

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current)
      }
    }
  }, [threshold])

  const getAnimationStyle = (): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
    }

    if (!isVisible) {
      switch (direction) {
        case 'up':
          return { ...baseStyle, opacity: 0, transform: 'translateY(30px)' }
        case 'down':
          return { ...baseStyle, opacity: 0, transform: 'translateY(-30px)' }
        case 'left':
          return { ...baseStyle, opacity: 0, transform: 'translateX(30px)' }
        case 'right':
          return { ...baseStyle, opacity: 0, transform: 'translateX(-30px)' }
      }
    }

    return { ...baseStyle, opacity: 1, transform: 'translate(0, 0)' }
  }

  return { ref, isVisible, style: getAnimationStyle() }
}

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

// Severity styling
const severityConfig = {
  low: { 
    color: '#22c55e', 
    bg: 'rgba(34, 197, 94, 0.1)', 
    border: 'rgba(34, 197, 94, 0.3)',
    icon: '✅',
    label: 'Low Bias'
  },
  moderate: { 
    color: '#f59e0b', 
    bg: 'rgba(245, 158, 11, 0.1)', 
    border: 'rgba(245, 158, 11, 0.3)',
    icon: '⚠️',
    label: 'Moderate Bias'
  },
  high: { 
    color: '#ef4444', 
    bg: 'rgba(239, 68, 68, 0.1)', 
    border: 'rgba(239, 68, 68, 0.3)',
    icon: '🚨',
    label: 'High Bias'
  }
}

// Bias type icons
const biasTypeConfig: Record<string, { icon: string; color: string }> = {
  'Confirmation Bias': { icon: '🎯', color: '#f59e0b' },
  'Selection Bias': { icon: '🎲', color: '#8b5cf6' },
  'Publication Bias': { icon: '📰', color: '#3b82f6' },
  'Funding Bias': { icon: '💰', color: '#22c55e' },
  'Citation Bias': { icon: '📚', color: '#ec4899' },
  'Methodology Bias': { icon: '🔬', color: '#06b6d4' },
  'Unknown': { icon: '❓', color: '#64748b' }
}

const styles = {
  card: {
    background: 'var(--bg-card)',
    borderRadius: 'var(--border-radius-lg)',
    border: '1px solid var(--border-color)',
    padding: 24,
    marginBottom: 24,
    animation: 'slideUp 0.5s ease-out',
  } as React.CSSProperties,

  header: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    marginBottom: 24,
  } as React.CSSProperties,

  title: {
    margin: 0,
    fontSize: 20,
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  } as React.CSSProperties,

  scoreContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: 24,
    padding: 24,
    background: 'var(--bg-secondary)',
    borderRadius: 'var(--border-radius)',
    marginBottom: 24,
  } as React.CSSProperties,

  scoreCircle: {
    width: 100,
    height: 100,
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'column' as const,
    position: 'relative' as const,
  } as React.CSSProperties,

  scoreRing: {
    position: 'absolute' as const,
    inset: 0,
    borderRadius: '50%',
    border: '6px solid var(--bg-tertiary)',
  } as React.CSSProperties,

  biasCard: {
    background: 'var(--bg-secondary)',
    borderRadius: 'var(--border-radius)',
    marginBottom: 12,
    overflow: 'hidden',
    border: '1px solid var(--border-color)',
    transition: 'all 0.2s ease',
  } as React.CSSProperties,

  biasHeader: {
    padding: '16px 20px',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    transition: 'background 0.2s ease',
  } as React.CSSProperties,

  biasContent: {
    padding: '0 20px 20px',
    borderTop: '1px solid var(--border-color)',
  } as React.CSSProperties,

  excerpt: {
    background: 'var(--bg-tertiary)',
    padding: '12px 16px',
    borderRadius: 8,
    fontStyle: 'italic',
    borderLeft: '3px solid',
    marginBottom: 16,
    fontSize: 14,
  } as React.CSSProperties,

  suggestion: {
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    padding: '12px 16px',
    borderRadius: 8,
    display: 'flex',
    alignItems: 'flex-start',
    gap: 12,
  } as React.CSSProperties,

  strengthsList: {
    background: 'var(--bg-secondary)',
    borderRadius: 'var(--border-radius)',
    padding: 20,
    marginTop: 24,
  } as React.CSSProperties,

  badge: {
    padding: '4px 10px',
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 600,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  } as React.CSSProperties,

  shimmer: {
    background: 'linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-secondary) 50%, var(--bg-tertiary) 75%)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.5s infinite',
    borderRadius: 8,
  } as React.CSSProperties,
}

function ScoreGauge({ score, severity }: { score: number; severity: 'low' | 'moderate' | 'high' }) {
  const config = severityConfig[severity]
  const circumference = 2 * Math.PI * 44 // radius = 44
  const strokeDashoffset = circumference - (score / 100) * circumference

  return (
    <div style={styles.scoreContainer}>
      <div style={styles.scoreCircle}>
        <svg width="100" height="100" style={{ position: 'absolute', transform: 'rotate(-90deg)' }}>
          <circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            stroke="var(--bg-tertiary)"
            strokeWidth="8"
          />
          <circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            stroke={config.color}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s ease' }}
          />
        </svg>
        <span style={{ fontSize: 28, fontWeight: 700, color: config.color, zIndex: 1 }}>
          {score}
        </span>
      </div>
      
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Bias Score</div>
        <div style={{ 
          ...styles.badge, 
          background: config.bg, 
          color: config.color,
          border: `1px solid ${config.border}`,
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6
        }}>
          <span>{config.icon}</span>
          {config.label}
        </div>
        <div style={{ 
          color: 'var(--text-secondary)', 
          fontSize: 13, 
          marginTop: 8,
          lineHeight: 1.5
        }}>
          {score <= 25 && 'Excellent objectivity. The paper follows best practices.'}
          {score > 25 && score <= 50 && 'Some concerns detected. Review the flagged items below.'}
          {score > 50 && 'Significant bias detected. Careful review recommended.'}
        </div>
      </div>
    </div>
  )
}

function BiasCard({ 
  bias, 
  isExpanded, 
  onToggle,
  direction = 'left',
  delay = 0
}: { 
  bias: BiasInstance
  isExpanded: boolean
  onToggle: () => void
  direction?: 'left' | 'right'
  delay?: number
}) {
  const severityStyle = severityConfig[bias.severity]
  const typeConfig = biasTypeConfig[bias.type] || biasTypeConfig['Unknown']
  const scrollAnim = useScrollAnimation(direction)
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div 
      ref={scrollAnim.ref}
      style={{
        ...styles.biasCard,
        ...scrollAnim.style,
        transitionDelay: `${delay}s`,
        borderColor: isExpanded ? severityStyle.color : (isHovered ? 'var(--accent-primary)' : 'var(--border-color)'),
        transform: scrollAnim.isVisible 
          ? (isHovered ? 'translateX(4px)' : 'translateX(0)')
          : scrollAnim.style.transform,
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div 
        style={{
          ...styles.biasHeader,
          background: isExpanded ? severityStyle.bg : 'transparent'
        }}
        onClick={onToggle}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ 
            fontSize: 24, 
            width: 40, 
            height: 40, 
            background: 'var(--bg-tertiary)',
            borderRadius: 8,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {typeConfig.icon}
          </span>
          <div>
            <div style={{ fontWeight: 600, marginBottom: 2 }}>{bias.type}</div>
            <span style={{ 
              ...styles.badge, 
              background: severityStyle.bg, 
              color: severityStyle.color,
              border: `1px solid ${severityStyle.border}`
            }}>
              {bias.severity}
            </span>
          </div>
        </div>
        <span style={{ 
          fontSize: 16, 
          color: 'var(--text-muted)',
          transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.2s ease'
        }}>
          ▼
        </span>
      </div>
      
      {isExpanded && (
        <div style={styles.biasContent}>
          <div style={{ paddingTop: 16 }}>
            <div style={{ 
              color: 'var(--text-secondary)', 
              fontSize: 12, 
              fontWeight: 600, 
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: 8 
            }}>
              Problematic Excerpt
            </div>
            <div style={{ ...styles.excerpt, borderLeftColor: severityStyle.color }}>
              "{bias.excerpt}"
            </div>
            
            <div style={{ 
              color: 'var(--text-secondary)', 
              fontSize: 12, 
              fontWeight: 600, 
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: 8 
            }}>
              Why It's Biased
            </div>
            <p style={{ marginBottom: 16, lineHeight: 1.6 }}>{bias.explanation}</p>
            
            <div style={styles.suggestion}>
              <span style={{ fontSize: 20 }}>💡</span>
              <div>
                <div style={{ fontWeight: 600, marginBottom: 4, color: 'var(--accent-primary)' }}>
                  Suggestion
                </div>
                <div style={{ lineHeight: 1.6 }}>{bias.suggestion}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <span style={{ fontSize: 24 }}>🤖</span>
        <h2 style={styles.title}>AI Bias Analysis</h2>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: 24, marginBottom: 24 }}>
        <div style={{ ...styles.shimmer, width: 100, height: 100, borderRadius: '50%' }} />
        <div style={{ flex: 1 }}>
          <div style={{ ...styles.shimmer, height: 24, width: '40%', marginBottom: 12 }} />
          <div style={{ ...styles.shimmer, height: 16, width: '60%' }} />
        </div>
      </div>
      
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 12,
        color: 'var(--accent-primary)',
        justifyContent: 'center',
        padding: 24
      }}>
        <div style={{
          width: 24,
          height: 24,
          border: '2px solid var(--accent-primary)',
          borderTopColor: 'transparent',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
        <span>Analyzing for bias...</span>
      </div>
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
  
  // Handle error state
  if (data.error && !data.biases?.length) {
    // Determine user-friendly error message
    let errorMessage = 'Unable to perform bias analysis at this time.'
    let errorIcon = '⚠️'
    
    if (data.error === 'Bias analysis disabled - no API key') {
      errorMessage = 'Please configure GEMINI_API_KEY in the backend .env file.'
    } else if (data.error.includes('429') || data.error.includes('quota') || data.error.includes('rate')) {
      errorMessage = 'AI service is temporarily unavailable due to rate limits. Please try again in a few minutes.'
      errorIcon = '⏳'
    } else if (data.error.includes('API') || data.error.includes('key')) {
      errorMessage = 'API configuration issue. Please check your API key settings.'
    }
    
    return (
      <div style={{ 
        ...styles.card, 
        borderColor: 'var(--warning)',
        background: 'rgba(245, 158, 11, 0.05)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 40 }}>{errorIcon}</span>
          <div>
            <h3 style={{ margin: '0 0 8px 0', fontSize: 18 }}>Bias Analysis Unavailable</h3>
            <p style={{ margin: 0, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {errorMessage}
            </p>
          </div>
        </div>
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
  
  const severity = data.severity || (data.overall_score <= 25 ? 'low' : data.overall_score <= 50 ? 'moderate' : 'high')
  
  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <span style={{ fontSize: 24 }}>🤖</span>
        <h2 style={styles.title}>AI Bias Analysis</h2>
      </div>
      
      {/* Score Display */}
      <ScoreGauge score={data.overall_score} severity={severity} />
      
      {/* Summary */}
      <div style={{ 
        background: 'var(--bg-secondary)', 
        padding: 16, 
        borderRadius: 'var(--border-radius)',
        marginBottom: 24,
        borderLeft: '3px solid var(--accent-primary)'
      }}>
        <div style={{ 
          color: 'var(--text-secondary)', 
          fontSize: 12, 
          fontWeight: 600, 
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginBottom: 8 
        }}>
          Summary
        </div>
        <p style={{ margin: 0, lineHeight: 1.6 }}>{data.summary}</p>
      </div>
      
      {/* Detected Biases */}
      {data.biases && data.biases.length > 0 ? (
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ 
            fontSize: 16, 
            fontWeight: 600, 
            marginBottom: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <span>🔍</span>
            Detected Biases ({data.biases.length})
          </h3>
          {data.biases.map((bias, index) => (
            <BiasCard
              key={index}
              bias={bias}
              isExpanded={expandedBiases.has(index)}
              onToggle={() => toggleBias(index)}
              direction={index % 2 === 0 ? 'left' : 'right'}
              delay={index * 0.1}
            />
          ))}
        </div>
      ) : (
        <div style={{ 
          background: severityConfig.low.bg, 
          border: `1px solid ${severityConfig.low.border}`,
          padding: 24, 
          borderRadius: 'var(--border-radius)',
          marginBottom: 24,
          textAlign: 'center'
        }}>
          <span style={{ fontSize: 48, display: 'block', marginBottom: 12 }}>✨</span>
          <div style={{ fontWeight: 600, color: severityConfig.low.color, marginBottom: 4 }}>
            No Significant Biases Detected
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
            The paper appears to follow good practices for objectivity and balanced reporting.
          </div>
        </div>
      )}
      
      {/* Strengths */}
      {data.strengths && data.strengths.length > 0 && (
        <StrengthsSection 
          strengths={data.strengths}
          showStrengths={showStrengths}
          setShowStrengths={setShowStrengths}
        />
      )}
    </div>
  )
}

// Separate component for strengths with scroll animation
function StrengthsSection({ 
  strengths, 
  showStrengths, 
  setShowStrengths 
}: { 
  strengths: string[]
  showStrengths: boolean
  setShowStrengths: (show: boolean) => void
}) {
  const scrollAnim = useScrollAnimation('up')
  
  return (
    <div ref={scrollAnim.ref} style={{ ...styles.strengthsList, ...scrollAnim.style }}>
      <div 
        style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          cursor: 'pointer'
        }}
        onClick={() => setShowStrengths(!showStrengths)}
      >
        <h3 style={{ 
          margin: 0, 
          fontSize: 16, 
          fontWeight: 600,
          color: severityConfig.low.color,
          display: 'flex',
          alignItems: 'center',
          gap: 8
        }}>
          <span>✅</span>
          Identified Strengths ({strengths.length})
        </h3>
        <span style={{ 
          color: 'var(--text-muted)',
          transform: showStrengths ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.2s ease'
        }}>
          ▼
        </span>
      </div>
      
      {showStrengths && (
        <ul style={{ 
          margin: '16px 0 0 0', 
          paddingLeft: 24,
          listStyle: 'none',
          animation: 'fadeInUp 0.4s ease-out'
        }}>
          {strengths.map((strength, index) => (
            <li key={index} style={{ 
              marginBottom: 8, 
              display: 'flex',
              alignItems: 'flex-start',
              gap: 8,
              animation: `fadeInUp 0.4s ease-out ${index * 0.05}s both`
            }}>
              <span style={{ color: severityConfig.low.color }}>•</span>
              <span>{strength}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
