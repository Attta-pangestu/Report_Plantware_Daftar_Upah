import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'

const LoginPage = () => {
  const { login, loading, error, isAuthenticated } = useAuth()
  const TEST_MODE = (import.meta.env?.VITE_DEV_MODE === 'true') || (import.meta.env?.DEV_MODE === 'true')
  const autoRef = useRef(false)
  const [isLoginMode, setIsLoginMode] = useState(true)
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    fullName: '',
    divisions: [],
    rememberMe: true // Default checked
  })
  const [availableDivisions, setAvailableDivisions] = useState(['PG1A','PG1B','PG2A','PG2B','DME','ARA','ARB1','ARB2','INFRA','AREC','IJL','STF-OFFICE','SECURITY'])
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  // Auto-login removed - menggunakan cookies untuk session management
  // useEffect(() => {
  //   // Auto-login dinonaktifkan, user harus login manual
  // }, [])

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleDivisionToggle = (division) => {
    setFormData(prev => ({
      ...prev,
      divisions: prev.divisions.includes(division)
        ? prev.divisions.filter(d => d !== division)
        : [...prev.divisions, division]
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setSubmitError('')

    try {
      if (isLoginMode) {
        // Login
        const success = await login(formData.username, formData.password, formData.rememberMe)
        if (!success) {
          setSubmitError('Login failed. Please check your credentials.')
        }
      } else {
        // Register
        const response = await fetch('/auth/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            username: formData.username,
            email: formData.email,
            password: formData.password,
            full_name: formData.fullName,
            divisions: formData.divisions
          })
        })

        if (response.ok) {
          // Auto-login after successful registration
          const loginSuccess = await login(formData.username, formData.password)
          if (!loginSuccess) {
            setSubmitError('Registration successful but login failed. Please try logging in.')
          }
        } else {
          const errorData = await response.json()
          setSubmitError(errorData.detail || 'Registration failed')
        }
      }
    } catch (error) {
      console.error('Authentication error:', error)
      setSubmitError('An error occurred. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const isFormValid = () => {
    if (isLoginMode) {
      return formData.username && formData.password
    } else {
      return formData.username && formData.password && formData.email && formData.fullName && formData.divisions.length > 0
    }
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: '#f5f5f5',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '2rem',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        width: '100%',
        maxWidth: '400px'
      }}>
        <h1 style={{
          textAlign: 'center',
          marginBottom: '2rem',
          color: '#333',
          fontSize: '1.8rem'
        }}>
          {isLoginMode ? 'Login' : 'Register'}
        </h1>

        {error && (
          <div style={{
            backgroundColor: '#fee',
            border: '1px solid #fcc',
            borderRadius: '4px',
            padding: '1rem',
            marginBottom: '1rem',
            color: '#c33'
          }}>
            {error}
          </div>
        )}

        {submitError && (
          <div style={{
            backgroundColor: '#fee',
            border: '1px solid #fcc',
            borderRadius: '4px',
            padding: '1rem',
            marginBottom: '1rem',
            color: '#c33'
          }}>
            {submitError}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Username
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '1rem'
              }}
              required
              disabled={submitting}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '1rem'
              }}
              required
              disabled={submitting}
            />
          </div>

          {!isLoginMode && (
            <>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '1rem'
                  }}
                  required
                  disabled={submitting}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                  Full Name
                </label>
                <input
                  type="text"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleInputChange}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '1rem'
                  }}
                  required
                  disabled={submitting}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                  Divisions Access
                </label>
                <div style={{
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  padding: '0.5rem',
                  maxHeight: '150px',
                  overflowY: 'auto'
                }}>
                  {availableDivisions.map(division => (
                    <label key={division} style={{
                      display: 'block',
                      marginBottom: '0.25rem',
                      cursor: 'pointer',
                      padding: '0.25rem',
                      borderRadius: '2px',
                      backgroundColor: formData.divisions.includes(division) ? '#e3f2fd' : 'transparent'
                    }}>
                      <input
                        type="checkbox"
                        checked={formData.divisions.includes(division)}
                        onChange={() => handleDivisionToggle(division)}
                        style={{ marginRight: '0.5rem' }}
                        disabled={submitting}
                      />
                      {division}
                    </label>
                  ))}
                </div>
                {formData.divisions.length === 0 && (
                  <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.25rem' }}>
                    Please select at least one division
                  </div>
                )}
              </div>

              {isLoginMode && (
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{
                    display: 'flex',
                    alignItems: 'center',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    color: '#666'
                  }}>
                    <input
                      type="checkbox"
                      name="rememberMe"
                      checked={formData.rememberMe}
                      onChange={(e) => setFormData(prev => ({
                        ...prev,
                        rememberMe: e.target.checked
                      }))}
                      style={{
                        marginRight: '0.5rem',
                        transform: 'scale(1.1)'
                      }}
                      disabled={submitting}
                    />
                    Ingat saya (tetap masuk)
                  </label>
                </div>
              )}
            </>
          )}

          <button
            type="submit"
            disabled={!isFormValid() || submitting || loading}
            style={{
              width: '100%',
              padding: '0.75rem',
              backgroundColor: isFormValid() && !submitting && !loading ? '#007bff' : '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '1rem',
              cursor: isFormValid() && !submitting && !loading ? 'pointer' : 'not-allowed'
            }}
          >
            {submitting ? 'Processing...' : (isLoginMode ? 'Login' : 'Register')}
          </button>
        </form>

        <div style={{
          textAlign: 'center',
          marginTop: '1.5rem',
          paddingTop: '1rem',
          borderTop: '1px solid #eee'
        }}>
          <span style={{ color: '#666' }}>
            {isLoginMode ? "Don't have an account?" : "Already have an account?"}
          </span>
          <button
            onClick={() => {
              setIsLoginMode(!isLoginMode)
              setSubmitError('')
              setFormData({
                username: '',
                password: '',
                email: '',
                fullName: '',
                divisions: [],
                rememberMe: true
              })
            }}
            style={{
              background: 'none',
              border: 'none',
              color: '#007bff',
              textDecoration: 'underline',
              cursor: 'pointer',
              marginLeft: '0.5rem',
              fontSize: '1rem'
            }}
          >
            {isLoginMode ? 'Register' : 'Login'}
          </button>
        </div>

        <div style={{
          textAlign: 'center',
          marginTop: '1rem',
          fontSize: '0.8rem',
          color: '#666'
        }}>
          Default admin account: admin / admin (access to all divisions)
        </div>
      </div>
    </div>
  )
}

export default LoginPage
  const TEST_MODE = (import.meta.env?.VITE_DEV_MODE === 'true') || (import.meta.env?.DEV_MODE === 'true')
