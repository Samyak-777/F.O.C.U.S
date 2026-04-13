import { useState, useRef, useCallback, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

const REQUIRED_PHOTOS = 3
const MAX_PHOTOS = 7

export default function EnrollmentPage() {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const [photos, setPhotos] = useState([])
  const [streaming, setStreaming] = useState(false)
  const [enrollStatus, setEnrollStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [enrollmentCheck, setEnrollmentCheck] = useState(null)
  const { authFetch } = useAuth()

  // Check enrollment status on mount
  useEffect(() => {
    authFetch('/api/enrollment/status')
      .then(r => r.json())
      .then(setEnrollmentCheck)
      .catch(() => {})
  }, [])

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' }
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        setStreaming(true)
      }
    } catch (err) {
      alert('Camera access denied. Please allow camera permission.')
    }
  }, [])

  const stopCamera = useCallback(() => {
    if (videoRef.current?.srcObject) {
      videoRef.current.srcObject.getTracks().forEach(t => t.stop())
      videoRef.current.srcObject = null
      setStreaming(false)
    }
  }, [])

  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return
    if (photos.length >= MAX_PHOTOS) {
      alert(`Maximum ${MAX_PHOTOS} photos allowed`)
      return
    }

    const canvas = canvasRef.current
    const video = videoRef.current
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0)

    canvas.toBlob((blob) => {
      if (blob) {
        const url = URL.createObjectURL(blob)
        setPhotos(prev => [...prev, { blob, url, id: Date.now() }])
      }
    }, 'image/jpeg', 0.92)
  }, [photos.length])

  const removePhoto = (id) => {
    setPhotos(prev => {
      const updated = prev.filter(p => p.id !== id)
      prev.filter(p => p.id === id).forEach(p => URL.revokeObjectURL(p.url))
      return updated
    })
  }

  const handleEnroll = async () => {
    if (photos.length < REQUIRED_PHOTOS) {
      alert(`Please capture at least ${REQUIRED_PHOTOS} photos`)
      return
    }

    setLoading(true)
    setEnrollStatus(null)

    try {
      const formData = new FormData()
      photos.forEach((photo, i) => {
        formData.append('images', photo.blob, `face_${i + 1}.jpg`)
      })

      const res = await authFetch('/api/enrollment/face', {
        method: 'POST',
        body: formData
      })

      const data = await res.json()
      if (res.ok) {
        setEnrollStatus({ success: true, message: data.message })
        stopCamera()
        // Refresh enrollment status
        authFetch('/api/enrollment/status')
          .then(r => r.json())
          .then(setEnrollmentCheck)
          .catch(() => {})
      } else {
        setEnrollStatus({ success: false, message: data.detail || 'Enrollment failed' })
      }
    } catch (err) {
      setEnrollStatus({ success: false, message: 'Network error. Please try again.' })
    } finally {
      setLoading(false)
    }
  }

  const isEnrolled = enrollmentCheck?.is_enrolled
  const hasConsent = enrollmentCheck?.has_consent

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto', padding: '24px' }}>
      <h2 style={{ fontSize: '22px', fontWeight: 700, marginBottom: '8px' }}>
        📸 Face Enrollment
      </h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '24px', lineHeight: 1.6 }}>
        Your face will be converted into a mathematical embedding (512 numbers) and encrypted.
        <strong> No raw images are ever stored.</strong> You can delete your data at any time.
      </p>

      {/* Status Banner */}
      {enrollmentCheck && (
        <div className="glass-card" style={{
          marginBottom: '20px',
          borderLeft: `4px solid ${isEnrolled ? '#22c55e' : hasConsent ? '#eab308' : '#ef4444'}`
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: 600 }}>
                {isEnrolled ? '✅ Face Enrolled' : hasConsent ? '⚠️ Consent Given — Not Yet Enrolled' : '❌ No Consent'}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                {isEnrolled
                  ? 'Your face is registered. Attendance will be marked automatically.'
                  : hasConsent
                    ? 'Please capture your face photos below to complete enrollment.'
                    : 'Go to Privacy & Consent tab to give consent before enrolling.'}
              </div>
            </div>
            {isEnrolled && (
              <span style={{
                background: '#22c55e20', color: '#22c55e', padding: '4px 14px',
                borderRadius: '20px', fontSize: '12px', fontWeight: 600
              }}>Active</span>
            )}
          </div>
        </div>
      )}

      {!hasConsent && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔒</div>
          <p>You need to give consent before enrolling your face.</p>
          <p style={{ fontSize: '13px', marginTop: '8px' }}>
            Go to the <strong>Privacy & Consent</strong> tab to give your biometric consent.
          </p>
        </div>
      )}

      {hasConsent && !isEnrolled && (
        <>
          {/* Camera Section */}
          <div className="glass-card" style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600 }}>📷 Camera Capture</h3>
              {!streaming ? (
                <button className="btn btn-primary" onClick={startCamera}>Start Camera</button>
              ) : (
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn btn-success" onClick={capturePhoto}
                    disabled={photos.length >= MAX_PHOTOS}>
                    📸 Capture ({photos.length}/{MAX_PHOTOS})
                  </button>
                  <button className="btn btn-outline" onClick={stopCamera}>Stop</button>
                </div>
              )}
            </div>

            <div style={{
              position: 'relative', borderRadius: '12px', overflow: 'hidden',
              background: '#0f172a', aspectRatio: '4/3', maxHeight: '360px'
            }}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={{ width: '100%', height: '100%', objectFit: 'cover', display: streaming ? 'block' : 'none' }}
              />
              {!streaming && (
                <div style={{
                  position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center', color: '#64748b'
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '12px' }}>🎥</div>
                  <p>Click "Start Camera" to begin</p>
                </div>
              )}
              {/* Face guide overlay */}
              {streaming && (
                <div style={{
                  position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  pointerEvents: 'none'
                }}>
                  <div style={{
                    width: '200px', height: '260px', border: '2px dashed rgba(99,102,241,0.6)',
                    borderRadius: '50%'
                  }} />
                </div>
              )}
            </div>
            <canvas ref={canvasRef} style={{ display: 'none' }} />

            <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-muted)' }}>
              💡 <strong>Tips:</strong> Face the camera directly • Good lighting • Remove sunglasses •
              Capture from slightly different angles for best results
            </div>
          </div>

          {/* Captured Photos Grid */}
          {photos.length > 0 && (
            <div className="glass-card" style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
                Captured Photos ({photos.length}/{REQUIRED_PHOTOS} minimum)
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '12px' }}>
                {photos.map((photo, i) => (
                  <div key={photo.id} style={{ position: 'relative', borderRadius: '10px', overflow: 'hidden' }}>
                    <img src={photo.url} alt={`Face ${i + 1}`}
                      style={{ width: '100%', aspectRatio: '1', objectFit: 'cover', borderRadius: '10px' }} />
                    <button
                      onClick={() => removePhoto(photo.id)}
                      style={{
                        position: 'absolute', top: '4px', right: '4px',
                        background: 'rgba(239,68,68,0.9)', color: '#fff', border: 'none',
                        borderRadius: '50%', width: '24px', height: '24px',
                        cursor: 'pointer', fontSize: '12px', lineHeight: '24px'
                      }}
                    >✕</button>
                    <div style={{
                      position: 'absolute', bottom: '4px', left: '4px',
                      background: 'rgba(0,0,0,0.7)', color: '#fff', padding: '2px 8px',
                      borderRadius: '8px', fontSize: '11px'
                    }}>#{i + 1}</div>
                  </div>
                ))}
              </div>

              <button
                className="btn btn-primary"
                onClick={handleEnroll}
                disabled={photos.length < REQUIRED_PHOTOS || loading}
                style={{ marginTop: '16px', width: '100%', padding: '12px' }}
              >
                {loading
                  ? '⏳ Processing embeddings...'
                  : `🚀 Enroll Face (${photos.length} photos)`}
              </button>

              {photos.length < REQUIRED_PHOTOS && (
                <p style={{ textAlign: 'center', color: '#eab308', fontSize: '13px', marginTop: '8px' }}>
                  ⚠️ {REQUIRED_PHOTOS - photos.length} more photo(s) needed
                </p>
              )}
            </div>
          )}

          {/* Enrollment Result */}
          {enrollStatus && (
            <div className="glass-card" style={{
              borderLeft: `4px solid ${enrollStatus.success ? '#22c55e' : '#ef4444'}`,
              marginBottom: '20px'
            }}>
              <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '4px' }}>
                {enrollStatus.success ? '✅ Enrollment Successful!' : '❌ Enrollment Failed'}
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                {enrollStatus.message}
              </p>
            </div>
          )}
        </>
      )}

      {/* How It Works */}
      <div className="glass-card">
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>🔬 How It Works</h3>
        <div style={{ display: 'grid', gap: '12px' }}>
          {[
            { step: '1', icon: '📸', title: 'Capture', desc: 'You take 3-7 face photos from slightly different angles' },
            { step: '2', icon: '🧠', title: 'Extract', desc: 'InsightFace AI converts each photo into a 512-number mathematical fingerprint' },
            { step: '3', icon: '🔐', title: 'Encrypt', desc: 'The fingerprint is AES-encrypted and saved. Raw photos are immediately discarded' },
            { step: '4', icon: '✅', title: 'Recognize', desc: 'During class, the camera compares live faces against stored fingerprints to mark attendance' },
          ].map(({ step, icon, title, desc }) => (
            <div key={step} style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
              <div style={{
                width: '36px', height: '36px', borderRadius: '10px',
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '16px', flexShrink: 0
              }}>{icon}</div>
              <div>
                <div style={{ fontWeight: 600, fontSize: '14px' }}>{title}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
