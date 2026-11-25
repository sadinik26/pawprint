
import { Routes, Route, Link } from 'react-router-dom'
import ReportPage from './ReportPage'
import SearchPage from './SearchPage'
import MapPage from './MapPage'
import './App.css'

function HomePage() {
  return (
    <div className="app">
      {/* Navigation */}
      <header className="navbar">
        <Link to="/" className="brand">
          <span className="brand-icon">🐾</span>
          <span>pawprint</span>
        </Link>

        <nav className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/map">District Map</Link>
          <a href="#how-it-works">How It Works</a>
          <a href="#about">About</a>
        </nav>

        <div className="nav-actions">
          <Link to="/search" className="nav-find">
            Find a Dog
          </Link>

          <Link to="/report" className="nav-report">
            Report a Dog
          </Link>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="hero" id="home">
          <div className="hero-content">
            <span className="eyebrow">
              <span className="eyebrow-dot"></span>
              REUNITING PAWS WITH THEIR FAMILIES
            </span>

            <h1>
              Every pawprint
              <br />
              leads <span>home.</span>
            </h1>

            <p className="hero-description">
              Lost a furry friend or found a dog looking for its family?
              Pawprint uses intelligent image matching to help bring
              missing dogs back home.
            </p>

            <div className="hero-buttons">
              <Link to="/search" className="primary-button">
                Find a Missing Dog <span>→</span>
              </Link>

              <Link to="/report" className="secondary-button">
                Report a Dog
              </Link>
            </div>

            <div className="hero-note">
              <span>♡</span>
              Every reunion starts with a little hope.
            </div>
          </div>

          <div className="hero-image-container">
            <div className="hero-image">
              <img
                src="https://images.unsplash.com/photo-1552053831-71594a27632d?w=1000&auto=format&fit=crop"
                alt="Golden retriever dog"
              />
            </div>

            <div className="image-label">
              <span className="label-icon">🐾</span>

              <div>
                <strong>Hope starts here</strong>
                <small>Let's find their way home.</small>
              </div>
            </div>

            <div className="floating-heart">♡</div>
          </div>
        </section>

        {/* Action Cards */}
        <section className="actions-section">
          <div className="section-heading">
            <span className="section-eyebrow">HOW CAN WE HELP?</span>

            <h2>A little help goes a long way.</h2>

            <p>
              Choose how you'd like to help a dog find its way home.
            </p>
          </div>

          <div className="action-cards">
            <article className="action-card lost-card">
              <div className="card-icon">🔎</div>

              <span className="card-tag">
                LOOKING FOR A FRIEND?
              </span>

              <h3>Find a Lost Dog</h3>

              <p>
                Upload a photograph of a missing dog and discover
                visually similar reports.
              </p>

              <Link to="/search" className="card-link">
                Search for a dog <span>→</span>
              </Link>
            </article>

            <article className="action-card found-card">
              <div className="card-icon">🏡</div>

              <span className="card-tag">FOUND A DOG?</span>

              <h3>Report a Dog</h3>

              <p>
                Share a photograph and details of a lost or found
                dog to help connect them with their family.
              </p>

              <Link to="/report" className="card-link">
                Submit a report <span>→</span>
              </Link>
            </article>
          </div>
        </section>

        {/* How It Works */}
        <section className="how-section" id="how-it-works">
          <div className="section-heading">
            <span className="section-eyebrow">
              SIMPLE. SMART. HOPEFUL.
            </span>

            <h2>How Pawprint works</h2>

            <p>
              Technology helping bring lost dogs and their families together.
            </p>
          </div>

          <div className="steps">
            <div className="step">
              <div className="step-number">01</div>
              <div className="step-icon">📷</div>
              <h3>Upload a Photo</h3>
              <p>Upload a clear photograph of the dog.</p>
            </div>

            <div className="step">
              <div className="step-number">02</div>
              <div className="step-icon">🤖</div>
              <h3>Smart Matching</h3>
              <p>Our AI compares images to find visually similar dogs.</p>
            </div>

            <div className="step">
              <div className="step-number">03</div>
              <div className="step-icon">❤️</div>
              <h3>Find a Match</h3>
              <p>Review matching reports and contact the reporter.</p>
            </div>
          </div>
        </section>

        {/* About */}
        <section className="about-section" id="about">
          <div className="about-content">
            <span className="section-eyebrow">OUR PURPOSE</span>

            <h2>
              Because every dog deserves to find its way home.
            </h2>

            <p>
              Pawprint brings together image recognition and community
              reporting to make searching for missing dogs easier.
              One photograph could make all the difference.
            </p>
          </div>

          <div className="about-decoration">🐾</div>
        </section>
      </main>

      {/* Footer */}
      <footer className="footer">
        <Link to="/" className="brand">
          <span className="brand-icon">🐾</span>
          <span>pawprint</span>
        </Link>

        <p>Made with love for every paw looking for home. ♡</p>

        <span>© 2026 Pawprint</span>
      </footer>
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />

      <Route path="/report" element={<ReportPage />} />

      <Route path="/search" element={<SearchPage />} />

      <Route path="/map" element={<MapPage />} />
    </Routes>
  )
}

export default App
