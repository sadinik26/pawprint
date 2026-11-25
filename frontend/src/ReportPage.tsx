
import { Link } from 'react-router-dom'
import ReportForm from './ReportForm'

function ReportPage() {
  return (
    <div className="app report-page">

      <header className="navbar">
        <Link to="/" className="brand">
          <span className="brand-icon">🐾</span>
          <span>pawprint</span>
        </Link>

        <nav className="nav-links">
          <Link to="/">Home</Link>
          <a href="/#how-it-works">How It Works</a>
          <a href="/#about">About</a>
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
        <div className="report-page-intro">
          <Link to="/" className="back-home">
            ← Back to Home
          </Link>

          <span className="section-eyebrow">
            HELP A DOG FIND HOME
          </span>

          <h1>Every report matters.</h1>

          <p>
            Whether you've lost your beloved dog or found one
            looking for its family, share the details with us.
            Together, we can help bring them home.
          </p>
        </div>

        <ReportForm />
      </main>

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

export default ReportPage
