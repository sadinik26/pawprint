import { useState, type FormEvent } from 'react'

interface PotentialMatch {
  report_id: number
  dog_name: string | null
  district: string | null
  date: string | null
  size: string | null
  color: string | null
  similarity: number
  same_district: boolean
}

const districts = [
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

function displayDogName(name?: string | null): string {
  const cleanedName = String(name ?? '').trim()
  const normalizedName = cleanedName.toLowerCase()

  const unknownNames = [
    '',
    'no',
    'no name',
    'unknown',
    'unknown dog',
    'none',
    'null',
    'n/a',
    'na',
    '-',
  ]

  return unknownNames.includes(normalizedName) ? 'Unknown' : cleanedName
}

function ReportForm() {
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [success, setSuccess] = useState(false)
  const [matches, setMatches] = useState<PotentialMatch[]>([])
  const [reportId, setReportId] = useState<number | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setMessage('')
    setSuccess(false)
    setMatches([])
    setReportId(null)

    const form = event.currentTarget
    const formData = new FormData(form)

    const optionalFields = ['dog_name', 'size', 'color']

    optionalFields.forEach((field) => {
      if (!formData.get(field)?.toString().trim()) {
        formData.delete(field)
      }
    })

    try {
      setLoading(true)

      const response = await fetch('http://127.0.0.1:8000/report', {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(
          typeof result.detail === 'string'
            ? result.detail
            : JSON.stringify(result.detail || result)
        )
      }

      setSuccess(true)
      setReportId(result.report_id)
      setMatches(result.potential_matches || [])

      setMessage(
        `Your ${result.report_status} dog report was submitted successfully!`
      )

      form.reset()
    } catch (error) {
      setSuccess(false)

      setMessage(
        error instanceof Error
          ? error.message
          : 'Something went wrong. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="report-section" id="report-form">
      <div className="report-heading">
        <span className="section-eyebrow">HELP A DOG FIND HOME</span>
        <h2>Submit a Dog Report</h2>
        <p>
          Share a few details and a photograph. Your report could help reunite a
          dog with its family.
        </p>
      </div>

      <form className="report-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="file">Dog Photograph *</label>
          <input
            id="file"
            type="file"
            name="file"
            accept="image/*"
            required
          />
          <small>Upload one clear photograph of the dog.</small>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="dog_name">Dog's Name</label>
            <input
              id="dog_name"
              name="dog_name"
              type="text"
              placeholder="Enter the dog's name (optional)"
            />
          </div>

          <div className="form-group">
            <label htmlFor="status">Report Type *</label>
            <select id="status" name="status" required defaultValue="">
              <option value="" disabled>
                Select report type
              </option>
              <option value="lost">Lost Dog</option>
              <option value="found">Found Dog</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="date">Date *</label>
            <input id="date" name="date" type="date" required />
          </div>

          <div className="form-group">
            <label htmlFor="size">Dog Size</label>
            <select id="size" name="size" defaultValue="">
              <option value="">Select size</option>
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="color">Dog Colour</label>
          <input
            id="color"
            name="color"
            type="text"
            placeholder="e.g. Brown, black, white"
          />
        </div>

        <div className="form-divider">
          <h3>Location Details</h3>
          <p>Select the district where the dog was lost or found.</p>
        </div>

        <div className="form-group">
          <label htmlFor="district">District *</label>
          <select id="district" name="district" required defaultValue="">
            <option value="" disabled>
              Select district
            </option>
            {districts.map((district) => (
              <option key={district} value={district}>
                {district}
              </option>
            ))}
          </select>
        </div>

        <div className="form-divider">
          <h3>Contact Information</h3>
          <p>How can someone contact you about this dog?</p>
        </div>

        <div className="form-group">
          <label htmlFor="reporter_name">Your Name *</label>
          <input
            id="reporter_name"
            name="reporter_name"
            type="text"
            placeholder="Enter your name"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="contact">Contact Number or Email *</label>
          <input
            id="contact"
            name="contact"
            type="text"
            placeholder="Enter your contact information"
            required
          />
        </div>

        {message && (
          <div className={`form-message ${success ? 'success' : 'error'}`}>
            {message}
            {success && reportId !== null && <p>Report ID: {reportId}</p>}
          </div>
        )}

        <button
          type="submit"
          className="submit-report-button"
          disabled={loading}
        >
          {loading ? 'Submitting report...' : 'Submit Dog Report →'}
        </button>

        <p className="form-disclaimer">
          Please make sure the information you provide is accurate.
        </p>
      </form>

      {success && (
        <div className="potential-matches">
          <h3>Potential Matches</h3>

          {matches.length === 0 ? (
            <p>
              No potential matches were found yet. Your report has been saved,
              and it can be compared with future reports.
            </p>
          ) : (
            <>
              <p>
                We found {matches.length} potential matching
                {matches.length === 1 ? '' : 's'}.
              </p>

              {matches.map((match) => (
                <div
                  className="potential-match-card"
                  key={match.report_id}
                >
                  <h4>{displayDogName(match.dog_name)}</h4>

                  <p>Report ID: {match.report_id}</p>
                  <p>District: {match.district || 'Unknown'}</p>
                  <p>Date: {match.date || 'Not provided'}</p>
                  <p>Size: {match.size || 'Not provided'}</p>
                  <p>Colour: {match.color || 'Not provided'}</p>

                  <p>
                    Image similarity: {(match.similarity * 100).toFixed(1)}%
                  </p>

                  {match.same_district && (
                    <p>Both reports are from the same district.</p>
                  )}
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </section>
  )
}

export default ReportForm
