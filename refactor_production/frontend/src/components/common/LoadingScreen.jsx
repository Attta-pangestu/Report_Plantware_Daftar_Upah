import React, { useState, useEffect } from 'react'

const LoadingScreen = ({
  isLoading = true,
  message = 'Loading...',
  gangCode = null,
  month = null,
  year = null,
  steps = [
    { name: 'Connecting to database', duration: 1000 },
    { name: 'Loading report headers', duration: 2000 },
    { name: 'Fetching employee data', duration: 3000 },
    { name: 'Processing calculations', duration: 2000 }
  ]
}) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (!isLoading || !steps.length) return

    let stepIndex = 0
    let progressInterval = null
    let stepTimeout = null

    const moveToNextStep = () => {
      if (stepIndex < steps.length) {
        setCurrentStep(stepIndex)
        setProgress(((stepIndex + 1) / steps.length) * 100)

        // Set up progress animation within current step
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

  const getMonthName = (monthNum) => {
    const months = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    return months[monthNum] || monthNum
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <div style={{
        background: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '20px',
        padding: '40px',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
        maxWidth: '500px',
        width: '90%',
        textAlign: 'center',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.3)'
      }}>
        {/* Logo/Header */}
        <div style={{
          marginBottom: '30px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '15px'
        }}>
          <div style={{
            width: '50px',
            height: '50px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '20px'
          }}>
            PR
          </div>
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontSize: '20px', fontWeight: '600', color: '#333', margin: 0 }}>
              Payroll Report System
            </div>
            <div style={{ fontSize: '14px', color: '#666', margin: 0 }}>
              PT Rebinmas Indonesia
            </div>
          </div>
        </div>

        {/* Loading Animation */}
        <div style={{
          marginBottom: '25px',
          position: 'relative',
          height: '60px'
        }}>
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '50px',
            height: '50px'
          }}>
            <div style={{
              width: '100%',
              height: '100%',
              border: '4px solid #f3f3f3',
              borderTop: '4px solid #667eea',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '24px',
              height: '24px',
              border: '3px solid #f3f3f3',
              borderLeft: '3px solid #764ba2',
              borderRadius: '50%',
              animation: 'spin 1.5s linear infinite reverse'
            }} />
          </div>
        </div>

        {/* Report Info */}
        {(gangCode || month || year) && (
          <div style={{
            background: 'linear-gradient(135deg, #667eea15 0%, #764ba215 100%)',
            borderRadius: '12px',
            padding: '15px',
            marginBottom: '25px',
            border: '1px solid #667eea30'
          }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#333', marginBottom: '8px' }}>
              Report Details
            </div>
            <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.5' }}>
              {gangCode && (
                <div><strong>Gang:</strong> {gangCode}</div>
              )}
              {month && year && (
                <div><strong>Periode:</strong> {getMonthName(month)} {year}</div>
              )}
            </div>
          </div>
        )}

        {/* Current Step */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{
            fontSize: '16px',
            fontWeight: '500',
            color: '#333',
            marginBottom: '8px',
            minHeight: '24px'
          }}>
            {steps[currentStep]?.name || message}
          </div>

          {/* Progress Bar */}
          <div style={{
            background: '#f0f0f0',
            borderRadius: '10px',
            height: '8px',
            overflow: 'hidden',
            marginBottom: '10px'
          }}>
            <div style={{
              background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
              height: '100%',
              borderRadius: '10px',
              width: `${progress}%`,
              transition: 'width 0.3s ease',
              boxShadow: '0 0 10px rgba(102, 126, 234, 0.3)'
            }} />
          </div>

          {/* Step Counter */}
          <div style={{ fontSize: '12px', color: '#666' }}>
            Step {currentStep + 1} of {steps.length}
          </div>
        </div>

        {/* Tips */}
        <div style={{
          background: '#f8f9fa',
          borderRadius: '8px',
          padding: '12px',
          fontSize: '11px',
          color: '#666',
          lineHeight: '1.4',
          borderLeft: '3px solid #667eea'
        }}>
          💡 <strong>Tip:</strong> Report generation is optimized with parallel processing for maximum performance.
        </div>
      </div>

      {/* CSS Animation */}
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

export default LoadingScreen