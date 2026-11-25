import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

const DISTRICTS = [
  'Ampara',
  'Anuradhapura',
  'Badulla',
  'Batticaloa',
  'Colombo',
  'Galle',
  'Gampaha',
  'Hambantota',
  'Jaffna',
  'Kalutara',
  'Kandy',
  'Kegalle',
  'Kilinochchi',
  'Kurunegala',
  'Mannar',
  'Matale',
  'Matara',
  'Monaragala',
  'Mullaitivu',
  'Nuwara Eliya',
  'Polonnaruwa',
  'Puttalam',
  'Ratnapura',
  'Trincomalee',
  'Vavuniya',
]

interface DogMatch {
  rank: number
  report_id: number
  dog_name?: string | null
  status: 'lost' | 'found'
  image_path: string
  district?: string | null
  date?: string | null
  size?: string | null
  color?: string | null
  similarity?: number
  similarity_percentage?: number
  same_district?: boolean
}

function displayDogName(name?: string | null): string {
  const cleanedName = name?.trim()

  if (!cleanedName || cleanedName.toLowerCase() === 'no') {
    return 'Unknown'
  }

  return cleanedName
}

function getImageUrl(imagePath?: string | null) {
  if (!imagePath) return ''

  const filename = imagePath.replace(/\\/g, '/').split('/').pop()
  return `${API_URL}/report-images/${encodeURIComponent(filename || '')}`
}

function getTodayLocalDate() {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function SearchPage() {
  const [dogName, setDogName] = useState('')
  const [status, setStatus] = useState<'lost' | 'found'>('lost')
  const [district, setDistrict] = useState('')
  const [date, setDate] = useState(getTodayLocalDate())
  const [size, setSize] = useState('')
  const [color, setColor] = useState('')
  const [photo, setPhoto] = useState<File | null>(null)
  const [numberOfMatches, setNumberOfMatches] = useState('10')

  const [matches, setMatches] = useState<DogMatch[]>([])
  const [hasSearched, setHasSearched] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!photo) {
      setError('Please upload a photograph of the dog. A photograph is required for AI matching.')
      return
    }

    if (!district) {
      setError('Please select the district.')
      return
    }

    try {
      setLoading(true)
      setError('')
      setMatches([])
      setHasSearched(false)

      const formData = new FormData()
      formData.append('file', photo)
      formData.append('status', status)
      formData.append('district', district)
      formData.append('date', date)
      formData.append('dog_name', dogName.trim())
      formData.append('size', size)
      formData.append('color', color.trim())
      formData.append('k', numberOfMatches)

      const response = await fetch(`${API_URL}/search`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Unable to search for potential dog matches.')
      }

      setMatches(Array.isArray(data.matches) ? data.matches : [])
      setHasSearched(true)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to connect to the Pawprint server.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="search-page">
      <nav className="search-navbar">
        <Link to="/" className="search-logo">
          Pawprint<span>.</span>
        </Link>

        <div className="search-nav-links">
          <Link to="/">Home</Link>
          <Link to="/report">Report a Dog</Link>
          <Link to="/search" className="active">
            Find a Dog
          </Link>
        </div>
      </nav>

      <main className="search-container">
        <div className="search-heading">
          <span className="search-eyebrow">REUNITE. RECONNECT. REUNITE.</span>
          <h1>Find Your Missing Friend</h1>
          <p>
            Enter the dog's details and upload a photograph. Pawprint's AI will
            search existing reports and suggest potential matches.
          </p>
        </div>

        <section className="search-form-card">
          <div className="search-section-heading">
            <h2>Search for a Matching Dog</h2>
            <p>A photograph is required for AI image matching.</p>
          </div>

          <form onSubmit={handleSearch}>
            <div className="search-filter-grid">
              <div className="search-field">
                <label htmlFor="dogName">Dog Name (Optional)</label>
                <input
                  id="dogName"
                  type="text"
                  value={dogName}
                  onChange={(event) => setDogName(event.target.value)}
                  placeholder="Enter dog's name"
                />
              </div>

              <div className="search-field">
                <label htmlFor="dogStatus">Dog Status</label>
                <select
                  id="dogStatus"
                  value={status}
                  onChange={(event) => setStatus(event.target.value as 'lost' | 'found')}
                  required
                >
                  <option value="lost">Lost</option>
                  <option value="found">Found</option>
                </select>
              </div>

              <div className="search-field">
                <label htmlFor="searchDistrict">District</label>
                <select
                  id="searchDistrict"
                  value={district}
                  onChange={(event) => setDistrict(event.target.value)}
                  required
                >
                  <option value="">Select District</option>
                  {DISTRICTS.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </div>

              <div className="search-field">
                <label htmlFor="searchDate">Date Lost / Found</label>
                <input
                  id="searchDate"
                  type="date"
                  value={date}
                  onChange={(event) => setDate(event.target.value)}
                  required
                />
              </div>

              <div className="search-field">
                <label htmlFor="dogSize">Dog Size (Optional)</label>
                <select
                  id="dogSize"
                  value={size}
                  onChange={(event) => setSize(event.target.value)}
                >
                  <option value="">Any Size</option>
                  <option value="small">Small</option>
                  <option value="medium">Medium</option>
                  <option value="large">Large</option>
                </select>
              </div>

              <div className="search-field">
                <label htmlFor="dogColor">Dog Colour (Optional)</label>
                <input
                  id="dogColor"
                  type="text"
                  value={color}
                  onChange={(event) => setColor(event.target.value)}
                  placeholder="e.g. black, white, brown"
                />
              </div>

              <div className="search-field">
                <label htmlFor="numberOfMatches">Number of Potential Matches</label>
                <select
                  id="numberOfMatches"
                  value={numberOfMatches}
                  onChange={(event) => setNumberOfMatches(event.target.value)}
                >
                  <option value="5">5 matches</option>
                  <option value="10">10 matches</option>
                  <option value="20">20 matches</option>
                  <option value="50">50 matches</option>
                </select>
              </div>
            </div>

            <div className="search-field search-photo-field">
              <label htmlFor="dogPhoto">Dog Photograph (Required)</label>
              <input
                id="dogPhoto"
                type="file"
                accept="image/jpeg,image/png,image/jpg"
                onChange={(event) => setPhoto(event.target.files?.[0] || null)}
                required
              />
              {photo && <p className="search-photo-name">Selected: {photo.name}</p>}
            </div>

            <button
              type="submit"
              className="search-submit-button"
              disabled={loading}
            >
              {loading ? 'Searching with AI...' : 'Search for Matching Dogs'}
            </button>
          </form>
        </section>

        {error && <div className="search-error">{error}</div>}

        {loading && (
          <section className="search-results-section">
            <div className="search-no-results">Analyzing photograph and searching existing dog reports...</div>
          </section>
        )}

        {hasSearched && !loading && (
          <section className="search-results-section">
            <div className="search-results-heading">
              <span className="search-eyebrow">AI SEARCH RESULTS</span>
              <h2>Potential Matching Dogs</h2>
              <p>{matches.length} potential match(es) found.</p>
            </div>

            {matches.length === 0 ? (
              <div className="search-no-results">
                <h3>No potential matches found</h3>
                <p>Try searching again with another photograph or different details.</p>
              </div>
            ) : (
              <div className="search-results-grid">
                {matches.map((match, index) => {
                  const similarity = Number(match.similarity_percentage ?? (Number(match.similarity) * 100))

                  return (
                    <article className="search-result-card" key={`${match.report_id}-${index}`}>
                      <div className="search-result-image-placeholder">
                        {match.image_path ? (
                          <img
                            src={getImageUrl(match.image_path)}
                            alt={displayDogName(match.dog_name)}
                            onError={(event) => {
                              event.currentTarget.style.display = 'none'
                            }}
                          />
                        ) : null}
                      </div>

                      <div className="search-result-content">
                        <span className="search-result-rank">
                          MATCH #{match.rank || index + 1} · {match.status.toUpperCase()} REPORT
                        </span>
                        <h3>{displayDogName(match.dog_name)}</h3>

                        <div className="search-result-details">
                          <p><strong>District:</strong> {match.district || 'Unknown'}</p>
                          {match.date && <p><strong>Date:</strong> {match.date}</p>}
                          {match.size && <p><strong>Size:</strong> {match.size}</p>}
                          {match.color && <p><strong>Colour:</strong> {match.color}</p>}
                          <p>
                            <strong>Image similarity:</strong>{' '}
                            {Number.isFinite(similarity) ? `${similarity.toFixed(2)}%` : 'Unavailable'}
                          </p>
                          {match.same_district && <p><strong>District:</strong> Same district as your search</p>}
                        </div>
                      </div>
                    </article>
                  )
                })}
              </div>
            )}
          </section>
        )}
      </main>

      <footer className="search-footer">
        Made with love for every furry friend. © Pawprint
      </footer>
    </div>
  )
}

export default SearchPage
