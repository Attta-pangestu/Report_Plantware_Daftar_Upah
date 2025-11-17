import React, { useState, useEffect } from 'react'

const LoadingScreen = ({
  isLoading = true,
  message = 'Memuat...',
  gangCode = null,
  month = null,
  year = null,
  logoUrl = null,
  bgUrl = '/images/wallpaper_loading_screen.webp',
  steps = [
    { name: 'Connecting to database', duration: 1000 },
    { name: 'Loading report headers', duration: 2000 },
    { name: 'Fetching employee data', duration: 3000 },
    { name: 'Processing calculations', duration: 2000 }
  ]
}) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)
  const [bgLoaded, setBgLoaded] = useState(false)

  useEffect(() => {
    if (!isLoading || !steps.length) return

    let stepIndex = 0
    let progressInterval = null
    let stepTimeout = null

    const moveToNextStep = () => {
      if (stepIndex < steps.length) {
        setCurrentStep(stepIndex)
        setProgress(((stepIndex + 1) / steps.length) * 100)

        const startProgress = (stepIndex / steps.length) * 100
        const endProgress = ((stepIndex + 1) / steps.length) * 100
        const progressDuration = steps[stepIndex].duration

        let progressStartTime = Date.now()

        progressInterval = setInterval(() => {
          const elapsed = Date.now() - progressStartTime
          const stepProgress = Math.min(elapsed / progressDuration, 1)
          const currentProgress = startProgress + (endProgress - startProgress) * stepProgress
          setProgress(currentProgress)
        }, 50)

        stepTimeout = setTimeout(() => {
          clearInterval(progressInterval)
          stepIndex++
          moveToNextStep()
        }, progressDuration)
      }
    }

    moveToNextStep()

    return () => {
      if (progressInterval) clearInterval(progressInterval)
      if (stepTimeout) clearTimeout(stepTimeout)
    }
  }, [isLoading, steps])

  useEffect(() => {
    if (!bgUrl) return
    let alive = true
    const img = new Image()
    img.loading = 'lazy'
    img.onload = () => { if (alive) setBgLoaded(true) }
    img.onerror = () => {
      if (alive) {
        console.warn('Loading screen wallpaper failed to load, using fallback gradient')
        setBgLoaded(false)
      }
    }
    img.src = bgUrl
    return () => { alive = false }
  }, [bgUrl])

  const getMonthName = (m) => {
    const months = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    if (typeof m === 'string' && m.includes('-')) {
      const parts = m.split('-')
      const num = parseInt(parts[1], 10)
      return months[num] || m
    }
    return months[m] || m
  }

  const containerStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: bgLoaded ? `url(${bgUrl}) center/cover no-repeat` : 'linear-gradient(135deg, #1e88e5 0%, #0d47a1 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
  }

  const overlayStyle = {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.4)',
    backdropFilter: 'blur(2px)'
  }

  const cardStyle = {
    background: 'rgba(255, 255, 255, 0.92)',
    borderRadius: '16px',
    padding: '48px',
    boxShadow: '0 25px 50px rgba(0, 0, 0, 0.15)',
    maxWidth: '420px',
    width: '90%',
    textAlign: 'center',
    position: 'relative',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    transition: 'all 0.3s ease'
  }

  return (
    <div style={containerStyle} className="loading-screen">
      <div style={overlayStyle} />
      <div style={cardStyle}>
        {/* Single Loading Circle */}
        <div style={{
          marginBottom: '32px',
          position: 'relative',
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            border: '4px solid ' + (bgLoaded ? 'rgba(255, 255, 255, 0.3)' : 'rgba(255, 255, 255, 0.2)'),
            borderTop: '4px solid #1976d2',
            borderRadius: '50%',
            animation: 'spin 1.2s linear infinite',
            boxShadow: '0 0 20px rgba(25, 118, 210, 0.4)'
          }} />
        </div>

        {/* Company Logo */}
        <div style={{
          marginBottom: '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px'
        }}>
          {logoUrl ? (
            <img
              src={logoUrl}
              alt="logo"
              style={{
                width: 56,
                height: 56,
                objectFit: 'contain',
                borderRadius: '8px',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                padding: '8px'
              }}
              onError={(e)=>{e.currentTarget.style.display='none'}}
            />
          ) : (
            <div style={{
              width: 56,
              height: 56,
              background: 'linear-gradient(135deg, #1976d2 0%, #0d47a1 100%)',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 'bold',
              fontSize: 20,
              boxShadow: '0 4px 12px rgba(25, 118, 210, 0.4)'
            }}>
              RJB
            </div>
          )}
          <div style={{ textAlign: 'left' }}>
            <div style={{
              fontSize: 22,
              fontWeight: 700,
              color: '#1a1a1a',
              margin: 0,
              letterSpacing: '-0.5px'
            }}>
              Rebinmas
            </div>
            <div style={{
              fontSize: 14,
              color: '#666',
              margin: 0,
              fontWeight: 500
            }}>
              Payroll System
            </div>
          </div>
        </div>

        {/* Report Info */}
        {(gangCode || month || year) && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(25, 118, 210, 0.08) 0%, rgba(13, 71, 161, 0.12) 100%)',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '32px',
            border: '1px solid rgba(25, 118, 210, 0.2)'
          }}>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#1a1a1a', marginBottom: 12 }}>
              Informasi Laporan
            </div>
            <div style={{ fontSize: 14, color: '#666', lineHeight: '1.6' }}>
              {gangCode && (
                <div><strong style={{ color: '#1976d2' }}>Gang:</strong> {gangCode}</div>
              )}
              {month && year && (
                <div><strong style={{ color: '#1976d2' }}>Periode:</strong> {getMonthName(month)} {year}</div>
              )}
            </div>
          </div>
        )}

        {/* Current Step */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{
            fontSize: 16,
            fontWeight: 500,
            color: '#1a1a1a',
            marginBottom: '12px',
            minHeight: '20px',
            letterSpacing: '0.3px'
          }}>
            {steps[currentStep]?.name || message}
          </div>

          {/* Progress Bar */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.06)',
            borderRadius: '6px',
            height: '6px',
            overflow: 'hidden',
            marginBottom: '8px'
          }}>
            <div style={{
              background: 'linear-gradient(90deg, #1976d2 0%, #0d47a1 100%)',
              height: '100%',
              borderRadius: '6px',
              width: `${progress}%`,
              transition: 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
              boxShadow: '0 2px 8px rgba(25, 118, 210, 0.4)'
            }} />
          </div>

          {/* Progress Text */}
          <div style={{
            fontSize: 13,
            color: '#666',
            fontWeight: 500
          }}>
            {progress.toFixed(0)}% Complete
          </div>
        </div>

        {/* Professional Note */}
        <div style={{
          background: 'rgba(25, 118, 210, 0.05)',
          borderRadius: '8px',
          padding: '16px',
          fontSize: 13,
          color: '#555',
          lineHeight: '1.5',
          borderLeft: '3px solid #1976d2',
          textAlign: 'left'
        }}>
          <div style={{ fontWeight: 600, color: '#1976d2', marginBottom: '4px' }}>
            📊 System Information
          </div>
          <div>
            Sedang memproses data payroll dengan sistem query yang dioptimalkan untuk performa maksimal.
          </div>
        </div>
      </div>

      {/* CSS Animation */}
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .loading-screen {
          animation: fadeIn 0.5s ease-out;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  )
}

export default LoadingScreen