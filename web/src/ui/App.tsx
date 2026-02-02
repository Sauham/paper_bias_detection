import React, { useState, useCallback, useRef, useEffect } from 'react'
import axios from 'axios'
import BiasAnalysisSection from './BiasAnalysisSection'

// Custom hook for scroll-based animations
function useScrollAnimation(direction: 'up' | 'down' | 'left' | 'right' = 'up', threshold = 0.1) {
  const ref = useRef<HTMLDivElement>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        // Only trigger animation once when element comes into view
        if (entry.isIntersecting) {
          setIsVisible(true)
        }
      },
      { threshold, rootMargin: '0px 0px -50px 0px' }
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
      transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
    }

    if (!isVisible) {
      switch (direction) {
        case 'up':
          return { ...baseStyle, opacity: 0, transform: 'translateY(40px)' }
        case 'down':
          return { ...baseStyle, opacity: 0, transform: 'translateY(-40px)' }
        case 'left':
          return { ...baseStyle, opacity: 0, transform: 'translateX(40px)' }
        case 'right':
          return { ...baseStyle, opacity: 0, transform: 'translateX(-40px)' }
      }
    }

    return { ...baseStyle, opacity: 1, transform: 'translate(0, 0)' }
  }

  return { ref, isVisible, style: getAnimationStyle() }
}

// Styles
const styles = {
  container: {
    maxWidth: 1200,
    margin: '0 auto',
    padding: '32px 24px',
    minHeight: '100vh',
  } as React.CSSProperties,

  header: {
    textAlign: 'center' as const,
    marginBottom: 48,
    animation: 'fadeInDown 0.8s ease-out',
  } as React.CSSProperties,

  logo: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  } as React.CSSProperties,

  logoIcon: {
    width: 48,
    height: 48,
    background: 'var(--accent-gradient)',
    borderRadius: 12,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 24,
    boxShadow: 'var(--shadow-glow)',
  } as React.CSSProperties,

  title: {
    fontSize: 36,
    fontWeight: 700,
    background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%)',
    backgroundSize: '200% 200%',
    animation: 'gradientShift 4s ease infinite',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  } as React.CSSProperties,

  subtitle: {
    color: 'var(--text-secondary)',
    fontSize: 16,
    maxWidth: 600,
    margin: '16px auto 0',
    animation: 'fadeInUp 0.8s ease-out 0.2s both',
  } as React.CSSProperties,

  card: {
    background: 'var(--bg-card)',
    borderRadius: 'var(--border-radius-lg)',
    border: '1px solid var(--border-color)',
    padding: 24,
    marginBottom: 24,
    transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
    animation: 'fadeInUp 0.6s ease-out both',
  } as React.CSSProperties,

  cardHover: {
    background: 'var(--bg-card-hover)',
    borderColor: 'var(--accent-primary)',
    boxShadow: 'var(--shadow-lg)',
  } as React.CSSProperties,

  uploadZone: {
    border: '2px dashed var(--border-color)',
    borderRadius: 'var(--border-radius)',
    padding: 40,
    textAlign: 'center' as const,
    transition: 'all 0.3s ease',
    cursor: 'pointer',
  } as React.CSSProperties,

  uploadZoneActive: {
    borderColor: 'var(--accent-primary)',
    background: 'rgba(59, 130, 246, 0.1)',
  } as React.CSSProperties,

  uploadIcon: {
    fontSize: 48,
    marginBottom: 16,
    display: 'block',
  } as React.CSSProperties,

  button: {
    background: 'var(--accent-gradient)',
    color: 'white',
    border: 'none',
    padding: '14px 32px',
    borderRadius: 'var(--border-radius)',
    fontSize: 16,
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    boxShadow: 'var(--shadow-md)',
  } as React.CSSProperties,

  buttonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  } as React.CSSProperties,

  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: 16,
    marginBottom: 32,
  } as React.CSSProperties,

  statCard: {
    background: 'var(--bg-secondary)',
    borderRadius: 'var(--border-radius)',
    padding: 20,
    textAlign: 'center' as const,
    border: '1px solid var(--border-color)',
  } as React.CSSProperties,

  progressBar: {
    width: '100%',
    height: 8,
    background: 'var(--bg-tertiary)',
    borderRadius: 4,
    overflow: 'hidden',
    marginTop: 8,
  } as React.CSSProperties,

  progressFill: {
    height: '100%',
    borderRadius: 4,
    transition: 'width 0.5s ease',
  } as React.CSSProperties,

  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    cursor: 'pointer',
    padding: '12px 0',
  } as React.CSSProperties,

  badge: {
    padding: '4px 12px',
    borderRadius: 20,
    fontSize: 12,
    fontWeight: 600,
    textTransform: 'uppercase' as const,
  } as React.CSSProperties,

  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    marginTop: 16,
  } as React.CSSProperties,

  th: {
    textAlign: 'left' as const,
    padding: '12px 16px',
    background: 'var(--bg-tertiary)',
    color: 'var(--text-secondary)',
    fontSize: 12,
    fontWeight: 600,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  } as React.CSSProperties,

  td: {
    padding: '12px 16px',
    borderBottom: '1px solid var(--border-color)',
  } as React.CSSProperties,

  link: {
    color: 'var(--accent-primary)',
    textDecoration: 'none',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    transition: 'color 0.2s',
  } as React.CSSProperties,

  error: {
    background: 'var(--error-bg)',
    border: '1px solid var(--error)',
    color: 'var(--error)',
    padding: 16,
    borderRadius: 'var(--border-radius)',
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  } as React.CSSProperties,

  loadingOverlay: {
    position: 'fixed' as const,
    inset: 0,
    background: 'rgba(15, 23, 42, 0.9)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    backdropFilter: 'blur(4px)',
  } as React.CSSProperties,

  spinner: {
    width: 48,
    height: 48,
    border: '3px solid var(--bg-tertiary)',
    borderTopColor: 'var(--accent-primary)',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  } as React.CSSProperties,
}

// Helper functions
const getSimilarityColor = (percent: number): string => {
  if (percent <= 10) return 'var(--success)'
  if (percent <= 25) return 'var(--warning)'
  return 'var(--error)'
}

const getSimilarityBg = (percent: number): string => {
  if (percent <= 10) return 'var(--success-bg)'
  if (percent <= 25) return 'var(--warning-bg)'
  return 'var(--error-bg)'
}

const getSimilarityLabel = (percent: number): string => {
  if (percent <= 10) return 'Low'
  if (percent <= 25) return 'Moderate'
  return 'High'
}

// Components
function FileUpload({ 
  file, 
  onFileChange, 
  onAnalyze, 
  loading 
}: { 
  file: File | null
  onFileChange: (file: File | null) => void
  onAnalyze: () => void
  loading: boolean 
}) {
  const [isDragging, setIsDragging] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const [buttonHovered, setButtonHovered] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    
    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      const droppedFile = files[0]
      if (droppedFile.type === 'application/pdf') {
        onFileChange(droppedFile)
      }
    }
  }, [onFileChange])

  return (
    <div style={{ 
      ...styles.card, 
      animationDelay: '0.1s',
      transform: isHovered ? 'translateY(-4px)' : 'translateY(0)',
      boxShadow: isHovered ? 'var(--shadow-lg)' : 'var(--shadow-sm)',
    }}
    onMouseEnter={() => setIsHovered(true)}
    onMouseLeave={() => setIsHovered(false)}
    >
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 12, 
        marginBottom: 20,
        animation: 'fadeInLeft 0.6s ease-out 0.2s both',
      }}>
        <span style={{ 
          fontSize: 24,
          animation: 'float 3s ease-in-out infinite',
        }}>📄</span>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>Upload Research Paper</h2>
      </div>

      <div
        style={{
          ...styles.uploadZone,
          ...(isDragging ? styles.uploadZoneActive : {}),
          ...(file ? { borderColor: 'var(--success)', background: 'var(--success-bg)' } : {}),
          transform: isDragging ? 'scale(1.02)' : 'scale(1)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          onChange={(e) => onFileChange(e.target.files?.[0] || null)}
          style={{ display: 'none' }}
        />
        
        {file ? (
          <>
            <span style={{ 
              ...styles.uploadIcon,
              animation: 'bounceIn 0.6s ease-out',
            }}>✅</span>
            <div style={{ 
              fontSize: 18, 
              fontWeight: 600, 
              color: 'var(--success)', 
              marginBottom: 8,
              animation: 'fadeInUp 0.5s ease-out 0.2s both',
            }}>
              {file.name}
            </div>
            <div style={{ 
              color: 'var(--text-secondary)', 
              fontSize: 14,
              animation: 'fadeInUp 0.5s ease-out 0.3s both',
            }}>
              {(file.size / 1024 / 1024).toFixed(2)} MB - Click to change
            </div>
          </>
        ) : (
          <>
            <span style={{ 
              ...styles.uploadIcon,
              animation: isDragging ? 'bounceIn 0.3s ease-out' : 'float 3s ease-in-out infinite',
            }}>📤</span>
            <div style={{ fontSize: 18, fontWeight: 500, marginBottom: 8 }}>
              Drag & drop your PDF here
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
              or click to browse files
            </div>
          </>
        )}
      </div>

      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <button
          onClick={onAnalyze}
          disabled={!file || loading}
          onMouseEnter={() => setButtonHovered(true)}
          onMouseLeave={() => setButtonHovered(false)}
          style={{
            ...styles.button,
            ...(!file || loading ? styles.buttonDisabled : {}),
            transform: buttonHovered && file && !loading ? 'translateY(-2px) scale(1.05)' : 'translateY(0) scale(1)',
            boxShadow: buttonHovered && file && !loading ? 'var(--shadow-glow)' : 'var(--shadow-md)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            animation: 'fadeInUp 0.6s ease-out 0.3s both',
          }}
        >
          {loading ? (
            <>
              <span style={{ ...styles.spinner, width: 20, height: 20, borderWidth: 2 }} />
              Analyzing...
            </>
          ) : (
            <>
              <span style={{ 
                display: 'inline-block',
                animation: buttonHovered && file ? 'pulse 1s ease-in-out infinite' : 'none',
              }}>🔍</span>
              Analyze Paper
            </>
          )}
        </button>
      </div>
    </div>
  )
}

function StatCard({ children, delay = 0, highlight = false }: { children: React.ReactNode; delay?: number; highlight?: boolean }) {
  const [isHovered, setIsHovered] = useState(false)
  
  return (
    <div 
      style={{ 
        ...styles.statCard,
        animation: `fadeInUp 0.6s ease-out ${delay}s both`,
        transform: isHovered ? 'translateY(-6px) scale(1.02)' : 'translateY(0) scale(1)',
        boxShadow: isHovered ? 'var(--shadow-lg)' : 'var(--shadow-sm)',
        borderColor: isHovered ? 'var(--accent-primary)' : highlight ? 'var(--accent-primary)' : 'var(--border-color)',
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {children}
    </div>
  )
}

function OverviewStats({ plagiarism }: { plagiarism: any }) {
  const percent = plagiarism?.overall_percent || 0
  const color = getSimilarityColor(percent)
  const bg = getSimilarityBg(percent)
  const label = getSimilarityLabel(percent)

  return (
    <div style={styles.statsGrid}>
      <StatCard delay={0.1} highlight>
        <div style={{ 
          fontSize: 42, 
          fontWeight: 700, 
          color,
          animation: 'bounceIn 0.8s ease-out 0.3s both',
        }}>{percent.toFixed(1)}%</div>
        <div style={{ color: 'var(--text-secondary)', marginTop: 4 }}>Overall Similarity</div>
        <div style={styles.progressBar}>
          <div style={{ 
            ...styles.progressFill, 
            width: `${percent}%`, 
            background: `linear-gradient(90deg, ${color}, ${color}dd)`,
            animation: 'slideRight 1s ease-out 0.5s both',
          }} />
        </div>
      </StatCard>
      
      <StatCard delay={0.2}>
        <div style={{ 
          ...styles.badge, 
          background: bg, 
          color, 
          display: 'inline-block', 
          fontSize: 14, 
          marginBottom: 8,
          animation: 'scaleIn 0.5s ease-out 0.4s both',
        }}>
          {label} Similarity
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 8 }}>
          {plagiarism?.overall_category || 'Analysis complete'}
        </div>
      </StatCard>

      <StatCard delay={0.3}>
        <div style={{ 
          fontSize: 28, 
          marginBottom: 8,
          animation: 'float 3s ease-in-out infinite',
        }}>📊</div>
        <div style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
          4 Sections Analyzed
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 4 }}>
          Title, Abstract, Methodology, Conclusions
        </div>
      </StatCard>
    </div>
  )
}

function SectionResult({ name, data, icon, delay = 0, direction = 'left' }: { name: string; data: any; icon: string; delay?: number; direction?: 'left' | 'right' }) {
  const [expanded, setExpanded] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const scrollAnim = useScrollAnimation(direction)
  const percent = data?.best_similarity_percent || 0
  const color = getSimilarityColor(percent)
  const bg = getSimilarityBg(percent)
  const matches = data?.matches || []

  return (
    <div 
      ref={scrollAnim.ref}
      style={{ 
        ...styles.card, 
        ...scrollAnim.style,
        transitionDelay: `${delay}s`,
        transform: scrollAnim.isVisible 
          ? (isHovered ? 'translateY(-4px) scale(1.01)' : 'translateY(0) scale(1)')
          : scrollAnim.style.transform,
        boxShadow: isHovered ? 'var(--shadow-lg)' : 'var(--shadow-sm)',
        borderColor: isHovered ? 'var(--accent-primary)' : 'var(--border-color)',
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div 
        style={styles.sectionHeader}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ 
            fontSize: 24,
            transition: 'transform 0.3s ease',
            transform: isHovered ? 'scale(1.2) rotate(5deg)' : 'scale(1) rotate(0deg)',
          }}>{icon}</span>
          <div>
            <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{name}</h3>
            <div style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
              {matches.length} sources found
            </div>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ 
              fontSize: 24, 
              fontWeight: 700, 
              color,
              transition: 'transform 0.3s ease',
              transform: isHovered ? 'scale(1.1)' : 'scale(1)',
            }}>{percent.toFixed(1)}%</div>
            <span style={{ ...styles.badge, background: bg, color }}>
              {getSimilarityLabel(percent)}
            </span>
          </div>
          <span style={{ 
            fontSize: 20, 
            color: 'var(--text-muted)',
            transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
          }}>
            ▼
          </span>
        </div>
      </div>

      {expanded && (
        <div style={{ 
          marginTop: 16, 
          paddingTop: 16, 
          borderTop: '1px solid var(--border-color)',
          animation: 'fadeInUp 0.4s ease-out'
        }}>
          {matches.length > 0 ? (
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={{ ...styles.th, borderRadius: '8px 0 0 0' }}>Match %</th>
                  <th style={styles.th}>Source Title</th>
                  <th style={{ ...styles.th, borderRadius: '0 8px 0 0' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {matches.map((m: any, i: number) => (
                  <tr key={i}>
                    <td style={styles.td}>
                      <span style={{ 
                        fontWeight: 600, 
                        fontFamily: "'JetBrains Mono', monospace",
                        color: getSimilarityColor(m.percent)
                      }}>
                        {m.percent.toFixed(1)}%
                      </span>
                    </td>
                    <td style={styles.td}>
                      <div style={{ maxWidth: 400 }}>{m.title}</div>
                    </td>
                    <td style={styles.td}>
                      <a 
                        href={m.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={styles.link}
                      >
                        View Source →
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ 
              textAlign: 'center', 
              padding: 32, 
              color: 'var(--text-muted)' 
            }}>
              <span style={{ fontSize: 32, display: 'block', marginBottom: 8 }}>✨</span>
              No significant matches found for this section
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Scroll animation wrapper component for main sections
function ScrollSection({ 
  children, 
  direction = 'up',
  delay = 0 
}: { 
  children: React.ReactNode
  direction?: 'up' | 'down' | 'left' | 'right'
  delay?: number 
}) {
  const scrollAnim = useScrollAnimation(direction)
  
  return (
    <div 
      ref={scrollAnim.ref}
      style={{ 
        ...scrollAnim.style,
        transitionDelay: `${delay}s`,
      }}
    >
      {children}
    </div>
  )
}

function LoadingOverlay({ message }: { message: string }) {
  return (
    <div style={{ ...styles.loadingOverlay, animation: 'fadeIn 0.3s ease-out' }}>
      <div style={{ 
        textAlign: 'center',
        animation: 'scaleIn 0.5s ease-out',
      }}>
        <div style={{ 
          ...styles.spinner, 
          margin: '0 auto 24px',
          width: 56,
          height: 56,
          borderWidth: 4,
        }} />
        <div style={{ 
          fontSize: 22, 
          fontWeight: 600, 
          marginBottom: 8,
          background: 'var(--accent-gradient)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>{message}</div>
        <div style={{ 
          color: 'var(--text-secondary)',
          animation: 'pulse 2s ease-in-out infinite',
        }}>
          This may take a moment...
        </div>
        <div style={{
          marginTop: 24,
          display: 'flex',
          justifyContent: 'center',
          gap: 8,
        }}>
          {[0, 1, 2].map(i => (
            <div key={i} style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              background: 'var(--accent-primary)',
              animation: `pulse 1.5s ease-in-out infinite ${i * 0.2}s`,
            }} />
          ))}
        </div>
      </div>
    </div>
  )
}

// Main App
export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [report, setReport] = useState<any>(null)
  const [loadingMessage, setLoadingMessage] = useState('')

  const onAnalyze = async () => {
    if (!file) return
    
    setLoading(true)
    setError(null)
    setReport(null)
    setLoadingMessage('Extracting text from PDF...')

    try {
      const form = new FormData()
      form.append('file', file)
      
      setLoadingMessage('Analyzing for plagiarism...')
      
      const resp = await axios.post('/analyze', form, {
        baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000 // 2 minute timeout
      })
      
      setLoadingMessage('Processing results...')
      setReport(resp.data)
      
    } catch (e: any) {
      setError(e?.response?.data?.error || e.message || 'Analysis failed')
    } finally {
      setLoading(false)
      setLoadingMessage('')
    }
  }

  const plagiarismData = report?.plagiarism || report
  const biasData = report?.bias_analysis || null

  return (
    <div style={styles.container}>
      {loading && <LoadingOverlay message={loadingMessage} />}
      
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.logo}>
          <h1 style={styles.title}>Research Paper Analyzer</h1>
        </div>
        <p style={styles.subtitle}>
          AI-powered plagiarism detection and bias analysis for academic papers. 
          Upload your PDF and get comprehensive insights.
        </p>
      </header>

      {/* Upload Section */}
      <FileUpload
        file={file}
        onFileChange={setFile}
        onAnalyze={onAnalyze}
        loading={loading}
      />

      {/* Error Display */}
      {error && (
        <div style={{ 
          ...styles.error, 
          marginBottom: 24,
          animation: 'fadeInUp 0.5s ease-out',
        }}>
          <span style={{ 
            fontSize: 24,
            animation: 'bounceIn 0.6s ease-out',
          }}>⚠️</span>
          <div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Analysis Failed</div>
            <div style={{ fontSize: 14 }}>{error}</div>
          </div>
        </div>
      )}

      {/* Results */}
      {report && (
        <>
          {/* Overview Stats */}
          <ScrollSection direction="down">
            <div style={{ 
              ...styles.card, 
              background: 'transparent', 
              border: 'none', 
              padding: 0,
            }}>
              <h2 style={{ 
                fontSize: 24, 
                fontWeight: 600, 
                marginBottom: 20,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
              }}>
                <span>📋</span> 
                <span>Plagiarism Analysis Results</span>
              </h2>
              <OverviewStats plagiarism={plagiarismData} />
            </div>
          </ScrollSection>

          {/* Section Results - alternating left/right scroll animations */}
          <SectionResult name="Title" data={plagiarismData?.sections?.Title} icon="📝" delay={0} direction="left" />
          <SectionResult name="Abstract" data={plagiarismData?.sections?.Abstract} icon="📄" delay={0.1} direction="right" />
          <SectionResult name="Methodology" data={plagiarismData?.sections?.Methodology} icon="🔬" delay={0.2} direction="left" />
          <SectionResult name="Conclusions" data={plagiarismData?.sections?.Conclusions} icon="✅" delay={0.3} direction="right" />

          {/* Bias Analysis - scroll up animation */}
          <ScrollSection direction="up" delay={0.2}>
            <BiasAnalysisSection data={biasData} loading={false} />
          </ScrollSection>
        </>
      )}
    </div>
  )
}
