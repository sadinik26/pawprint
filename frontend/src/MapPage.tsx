
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

const VIEW_WIDTH = 920
const VIEW_HEIGHT = 980
const MAP_PADDING = 34

type DistrictSummary = {
  district: string
  lost: number
  found: number
  total: number
}

type DistrictSummaryResponse = {
  status: string
  total_lost: number
  total_found: number
  total_reports: number
  districts: DistrictSummary[]
}

type DogReport = {
  id: number
  dog_name?: string | null
  status?: string | null
  image_path?: string | null
  district?: string | null
  date?: string | null
  size?: string | null
  color?: string | null
}

type ReportsResponse = {
  status?: string
  total_reports?: number
  reports?: DogReport[]
}

type Position = [number, number, ...number[]]
type Ring = Position[]

type GeoFeature = {
  type: 'Feature'
  properties: Record<string, unknown>
  geometry:
    | {
        type: 'Polygon'
        coordinates: Ring[]
      }
    | {
        type: 'MultiPolygon'
        coordinates: Ring[][]
      }
}

type GeoJSONData = {
  type: 'FeatureCollection'
  features: GeoFeature[]
}

type MapFeature = {
  district: string
  path: string
  labelX: number
  labelY: number
}

function cleanDistrictName(value: unknown): string {
  return String(value ?? '')
    .replace(/\s+District$/i, '')
    .trim()
}

function normalizeDistrictName(value: unknown): string {
  return cleanDistrictName(value).toLowerCase()
}

function getFeatureName(feature: GeoFeature): string {
  const props = feature.properties || {}

  return cleanDistrictName(
    props.shapeName ??
      props.shape_name ??
      props.name ??
      props.NAME_2 ??
      props.district,
  )
}

function getAllCoordinates(feature: GeoFeature): Position[] {
  if (feature.geometry.type === 'Polygon') {
    return feature.geometry.coordinates.flat()
  }

  return feature.geometry.coordinates.flat(2)
}

function geometryToRings(feature: GeoFeature): Ring[] {
  if (feature.geometry.type === 'Polygon') {
    return feature.geometry.coordinates
  }

  return feature.geometry.coordinates.flat()
}

function makeMapFeatures(data: GeoJSONData): MapFeature[] {
  const allPoints = data.features.flatMap(getAllCoordinates)

  if (!allPoints.length) {
    return []
  }

  const longitudes = allPoints.map((point) => point[0])
  const latitudes = allPoints.map((point) => point[1])

  const minLon = Math.min(...longitudes)
  const maxLon = Math.max(...longitudes)
  const minLat = Math.min(...latitudes)
  const maxLat = Math.max(...latitudes)

  const usableWidth = VIEW_WIDTH - MAP_PADDING * 2
  const usableHeight = VIEW_HEIGHT - MAP_PADDING * 2

  const scale = Math.min(
    usableWidth / (maxLon - minLon),
    usableHeight / (maxLat - minLat),
  )

  const drawnWidth = (maxLon - minLon) * scale
  const drawnHeight = (maxLat - minLat) * scale

  const offsetX = (VIEW_WIDTH - drawnWidth) / 2
  const offsetY = (VIEW_HEIGHT - drawnHeight) / 2

  const project = (
    position: Position,
  ): [number, number] => [
    offsetX + (position[0] - minLon) * scale,
    VIEW_HEIGHT -
      offsetY -
      (position[1] - minLat) * scale,
  ]

  return data.features.map((feature) => {
    const rings = geometryToRings(feature)

    const path = rings
      .map((ring) => {
        const points = ring.map(project)

        if (!points.length) {
          return ''
        }

        return (
          `M ${points
            .map(([x, y]) => `${x.toFixed(2)} ${y.toFixed(2)}`)
            .join(' L ')} Z`
        )
      })
      .join(' ')

    const points = getAllCoordinates(feature)

    const center = points.reduce(
      (acc, point) => {
        const [x, y] = project(point)

        acc.x += x
        acc.y += y

        return acc
      },
      { x: 0, y: 0 },
    )

    return {
      district: getFeatureName(feature),
      path,
      labelX: center.x / points.length,
      labelY: center.y / points.length,
    }
  })
}

/**
 * Load GeoJSON from the frontend public folder.
 * This avoids fetching district boundaries from GitHub.
 */
async function fetchDistrictGeoJSON(): Promise<GeoJSONData> {
  const response = await fetch('/districts.geojson')

  if (!response.ok) {
    throw new Error(
      `Could not load district map: HTTP ${response.status}. Check that public/districts.geojson exists.`,
    )
  }

  const text = await response.text()

  if (
    text.startsWith(
      'version https://git-lfs.github.com/spec/v1',
    )
  ) {
    throw new Error(
      'districts.geojson is a Git LFS pointer, not actual GeoJSON. Please download the real district boundary file.',
    )
  }

  let data: GeoJSONData

  try {
    data = JSON.parse(text) as GeoJSONData
  } catch {
    throw new Error(
      'districts.geojson is not valid JSON.',
    )
  }

  if (
    data.type !== 'FeatureCollection' ||
    !Array.isArray(data.features)
  ) {
    throw new Error(
      'The district map file has an invalid GeoJSON format.',
    )
  }

  return data
}

/**
 * Convert the report image path to the existing backend image route.
 */
function getImageUrl(imagePath: string): string {
  const filename = imagePath
    .replace(/\\/g, '/')
    .split('/')
    .pop()

  return `${API_URL}/report-images/${encodeURIComponent(
    filename || '',
  )}`
}

/**
 * Reports API may return either:
 *   [report, report, ...]
 * or:
 *   { reports: [report, report, ...] }
 */
function extractReports(data: unknown): DogReport[] {
  if ( Array.isArray(data) ) {
    return data as DogReport[]
  }

  if (
    data &&
    typeof data === 'object' &&
    'reports' in data &&
    Array.isArray((data as ReportsResponse).reports)
  ) {
    return (data as ReportsResponse).reports || []
  }

  return []
}

function MapPage() {
  const [summary, setSummary] =
    useState<DistrictSummaryResponse | null>(null)

  const [geojson, setGeojson] =
    useState<GeoJSONData | null>(null)

  const [selectedDistrict, setSelectedDistrict] =
    useState('')

  const [dogReports, setDogReports] =
    useState<DogReport[]>([])

  const [reportsLoading, setReportsLoading] =
    useState(false)

  const [reportsError, setReportsError] =
    useState('')

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  /**
   * Load district summary and GeoJSON map boundaries.
   */
  useEffect(() => {
    let isMounted = true

    async function loadMapData() {
      try {
        setLoading(true)
        setError('')

        const [summaryResponse, geoData] =
          await Promise.all([
            fetch(`${API_URL}/district-summary`),
            fetchDistrictGeoJSON(),
          ])

        if (!summaryResponse.ok) {
          throw new Error(
            'Could not load district report counts. Check that the backend is running and /district-summary is available.',
          )
        }

        const summaryData =
          (await summaryResponse.json()) as DistrictSummaryResponse

        if (isMounted) {
          setSummary(summaryData)
          setGeojson(geoData)
        }
      } catch (err) {
        if (isMounted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Unable to load the district map.',
          )
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadMapData()

    return () => {
      isMounted = false
    }
  }, [])

  /**
   * Load both lost and found reports.
   * Do not pass ?status=lost here.
   */
  useEffect(() => {
    let isMounted = true

    async function loadDogReports() {
      try {
        setReportsLoading(true)
        setReportsError('')

        const response = await fetch(
          `${API_URL}/reports`,
        )

        if (!response.ok) {
          throw new Error(
            `Unable to load dog reports. HTTP ${response.status}`,
          )
        }

        const data: unknown = await response.json()
        const reports = extractReports(data)

        if (isMounted) {
          setDogReports(reports)
        }
      } catch (err) {
        if (isMounted) {
          setReportsError(
            err instanceof Error
              ? err.message
              : 'Unable to load dog reports.',
          )
        }
      } finally {
        if (isMounted) {
          setReportsLoading(false)
        }
      }
    }

    loadDogReports()

    return () => {
      isMounted = false
    }
  }, [])

  const mapFeatures = useMemo(
    () => (geojson ? makeMapFeatures(geojson) : []),
    [geojson],
  )

  /**
   * Normalize district names to match map names and API names.
   */
  const summaryByDistrict = useMemo(() => {
    const map = new Map<string, DistrictSummary>()

    summary?.districts.forEach((item) => {
      map.set(
        normalizeDistrictName(item.district),
        item,
      )
    })

    return map
  }, [summary])

  const selectedCounts = selectedDistrict
    ? summaryByDistrict.get(
        normalizeDistrictName(selectedDistrict),
      )
    : undefined

  /**
   * Filter both lost and found reports by the selected district.
   */
  const selectedDogReports = useMemo(() => {
    if (!selectedDistrict) {
      return []
    }

    const selectedName =
      normalizeDistrictName(selectedDistrict)

    return dogReports.filter((report) => {
      return (
        normalizeDistrictName(report.district) ===
        selectedName
      )
    })
  }, [dogReports, selectedDistrict])

  return (
    <div className="district-map-page">
      <nav className="district-map-navbar">
        <Link to="/" className="district-map-logo">
          Pawprint<span>.</span>
        </Link>

        <div className="district-map-nav-links">
          <Link to="/">Home</Link>
          <Link to="/report">Report a Dog</Link>
          <Link to="/search">Find a Dog</Link>
          <Link to="/map" className="active">
            District Map
          </Link>
        </div>
      </nav>

      <main className="district-map-container">
        <header className="district-map-heading">
          <span className="district-map-eyebrow">
            PAWPRINT COMMUNITY MAP
          </span>

          <h1>
            Find hope, <em>district by district.</em>
          </h1>

          <p>
            Explore lost and found dog reports across Sri Lanka.
            Select a district on the map to see its report counts
            and dog reports.
          </p>
        </header>

        {loading && (
          <div className="district-map-message">
            Loading Sri Lanka's district map…
          </div>
        )}

        {error && (
          <div className="district-map-error" role="alert">
            {error}
          </div>
        )}

        {!loading && !error && summary && (
          <>
            <section
              className="district-map-stats"
              aria-label="Report totals"
            >
              <article>
                <span>Total reports</span>
                <strong>{summary.total_reports}</strong>
              </article>

              <article>
                <span>Lost dogs</span>
                <strong>{summary.total_lost}</strong>
              </article>

              <article>
                <span>Found dogs</span>
                <strong>{summary.total_found}</strong>
              </article>
            </section>

            <section className="district-map-layout">
              <div className="district-map-visual-card">
                <div className="district-map-legend">
                  <span>
                    <i className="lost-legend" />
                    Lost reports
                  </span>

                  <span>
                    <i className="found-legend" />
                    Found reports
                  </span>
                </div>

                <svg
                  className="district-map-svg"
                  viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`}
                  role="img"
                  aria-label="Clickable map of Sri Lanka's districts"
                >
                  {mapFeatures.map((feature) => {
                    const counts = summaryByDistrict.get(
                      normalizeDistrictName(feature.district),
                    )

                    const isSelected =
                      selectedDistrict === feature.district

                    const isEmpty =
                      !counts || counts.total === 0

                    return (
                      <g key={feature.district}>
                        <path
                          d={feature.path}
                          className={[
                            'district-map-shape',
                            isSelected ? 'selected' : '',
                            isEmpty ? 'no-reports' : '',
                          ].join(' ')}
                          onClick={() =>
                            setSelectedDistrict(feature.district)
                          }
                          onKeyDown={(event) => {
                            if (
                              event.key === 'Enter' ||
                              event.key === ' '
                            ) {
                              event.preventDefault()

                              setSelectedDistrict(
                                feature.district,
                              )
                            }
                          }}
                          tabIndex={0}
                          role="button"
                          aria-label={`${feature.district}: ${counts?.lost ?? 0} lost, ${counts?.found ?? 0} found reports`}
                        />

                        <text
                          x={feature.labelX}
                          y={feature.labelY}
                          className="district-map-label"
                          pointerEvents="none"
                        >
                          {feature.district}
                        </text>
                      </g>
                    )
                  })}
                </svg>

                <p className="district-map-source">
                  District boundaries: geoBoundaries / Survey
                  Department of Sri Lanka, via OCHA COD-AB.
                  Map outlines are simplified.
                </p>
              </div>

              <aside className="district-map-detail-card">
                {selectedDistrict && selectedCounts ? (
                  <>
                    <span className="district-map-detail-eyebrow">
                      SELECTED DISTRICT
                    </span>

                    <h2>{selectedDistrict}</h2>

                    <div className="district-map-detail-total">
                      <strong>{selectedCounts.total}</strong>
                      <span>reports</span>
                    </div>

                    <div className="district-map-count-row">
                      <span>
                        <i className="lost-legend" />
                        Lost dogs
                      </span>

                      <strong>{selectedCounts.lost}</strong>
                    </div>

                    <div className="district-map-count-row">
                      <span>
                        <i className="found-legend" />
                        Found dogs
                      </span>

                      <strong>{selectedCounts.found}</strong>
                    </div>

                    <div className="district-map-dogs-section">
                      <h3>
                        Dog reports ({selectedDogReports.length})
                      </h3>

                      {reportsLoading && (
                        <p className="district-map-dogs-message">
                          Loading dog reports...
                        </p>
                      )}

                      {reportsError && (
                        <p
                          className="district-map-dogs-error"
                          role="alert"
                        >
                          {reportsError}
                        </p>
                      )}

                      {!reportsLoading &&
                        !reportsError &&
                        selectedDogReports.length === 0 && (
                          <p className="district-map-dogs-message">
                            No dog reports in this district.
                          </p>
                        )}

                      {!reportsLoading &&
                        !reportsError &&
                        selectedDogReports.map((dog) => {
                          const status = String(
                            dog.status ?? '',
                          ).toLowerCase()

                          const isFound =
                            status === 'found'

                          return (
                            <article
                              className="district-map-dog-card"
                              key={dog.id}
                            >
                              {dog.image_path ? (
                                <img
                                  src={getImageUrl(dog.image_path)}
                                  alt={
                                    dog.dog_name || 'Dog report'
                                  }
                                  onError={(event) => {
                                    event.currentTarget.style.display =
                                      'none'
                                  }}
                                />
                              ) : (
                                <div className="district-map-dog-image-placeholder">
                                  No photo
                                </div>
                              )}

                              <div className="district-map-dog-info">
                                <h4>
                                  {dog.dog_name ||
                                    'Name not provided'}
                                </h4>

                                <span
                                  className={`district-map-dog-status ${
                                    isFound ? 'found' : 'lost'
                                  }`}
                                >
                                  {isFound
                                    ? 'Found dog'
                                    : 'Lost dog'}
                                </span>

                                {dog.date && (
                                  <p>
                                    <strong>
                                      {isFound
                                        ? 'Found on:'
                                        : 'Last seen:'}
                                    </strong>{' '}
                                    {dog.date}
                                  </p>
                                )}

                                {dog.color && (
                                  <p>
                                    <strong>Color:</strong>{' '}
                                    {dog.color}
                                  </p>
                                )}

                                {dog.size && (
                                  <p>
                                    <strong>Size:</strong>{' '}
                                    {dog.size}
                                  </p>
                                )}
                              </div>
                            </article>
                          )
                        })}
                    </div>
                  </>
                ) : (
                  <div className="district-map-select-prompt">
                    <div className="district-map-paw">♡</div>

                    <h2>Select a district</h2>

                    <p>
                      Click any district on the map to see how
                      many lost and found dog reports have been
                      submitted.
                    </p>
                  </div>
                )}

                <Link
                  to="/report"
                  className="district-map-report-link"
                >
                  Report a Dog <span>→</span>
                </Link>
              </aside>
            </section>
          </>
        )}
      </main>

      <footer className="district-map-footer">
        Made with love for every furry friend. © Pawprint
      </footer>
    </div>
  )
}

export default MapPage
