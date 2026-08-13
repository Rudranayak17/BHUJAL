Real-Time Groundwater Evaluation using DWLR Stations
Overview
Bhujal is a mobile-integrated groundwater intelligence platform that consumes real-time Digital Water Level Recorder (DWLR) data via the India-WRIS APIs and visualizes groundwater trends across 5,260 monitoring stations in India. The system provides farmers, water administrators, and planners with accessible, actionable insights into groundwater storage, recharge trends, and sustainable usage guidance.
________________________________________
Problem Statement
Groundwater supports approximately 40% of India's irrigation demand and a significant portion of drinking water supply. However, traditional manual groundwater monitoring is infrequent and delayed, leading to widespread over-extraction and poor water-resource planning. Under the National Hydrology Project (NHP), the Central Groundwater Board (CGWB) operates 5,260 Digital Water Level Recorder (DWLR) stations with telemetry capabilities that generate near real-time groundwater data. Yet this critical data remains underutilized by non-technical stakeholders due to:
•	Lack of accessible visualization interfaces
•	Absence of intelligent trend analysis and recharge evaluation
•	Limited decision-support systems for farmers and local administrators
Bhujal bridges this gap by translating raw DWLR telemetry into actionable groundwater intelligence.
________________________________________
Objectives
•	Real-time Data Access: Provide a mobile-first interface to access groundwater levels from 5,260 DWLR stations via India-WRIS APIs with minimal latency.
•	Intelligent Trend Analysis: Evaluate groundwater recharge and depletion trends at station, district, and state scales using time-series analytics.
•	Accessible Visualization: Create intuitive, multi-station line charts and status indicators so farmers and officials can make informed irrigation and water-management decisions.
•	Farmer-Centric Design: Deliver decision-support features (safe/caution/critical status, seasonal comparisons, irrigation guidance) tailored to ground-level users.
________________________________________
Key Features
1. Real-Time Data Integration
•	Consumes groundwater level data from India-WRIS API Catalog, pulling near real-time measurements from 5,260 DWLR stations across India.
•	Supports dynamic filtering by state, district, station, and custom date range for localized analysis.
•	Implements intelligent caching and background refresh to minimize API calls while maintaining freshness.
2. Recharge Trend Evaluation
•	Computes net groundwater depth change over configurable time windows (daily, weekly, seasonal).
•	Calculates rate of rise/fall to identify active recharge phases or critical depletion trends.
•	Flags anomalies (sharp drops, unusual spikes) to alert users to potential equipment issues or dramatic hydrological events.
3. Multi-Station Visual Analytics
•	Interactive line charts overlaying multiple stations within a district or state for comparative analysis.
•	Color-coded station buttons and customizable date ranges for intuitive exploration.
•	Export capabilities (CSV) to enable offline analysis and district-level reporting.
4. Farmer-Centric Decision Support
•	Water Level Status Cards: Display current groundwater depth, safe-use indicators, and irrigation guidance based on threshold rules.
•	Seasonal Comparison: Show current water levels vs. last year at the same station to highlight long-term trends.
•	Traffic-Light Indicators: Simple visual cues (green = safe, amber = caution, red = critical) derived from depth thresholds and recent trend direction.
5. Storage Change Calculator
•	Dedicated tool to compute volumetric groundwater storage change across a district.
•	Integrates aquifer area and specific yield to estimate MCM (Million Cubic Meters) change over a period.
•	Generates downloadable reports in CSV format for departmental use and policy planning.
6. Responsive Mobile & Web Interface
•	Fully responsive design optimized for farmer mobile devices and desktop dashboards for administrators.
•	Intuitive navigation with persistent user profiles and saved-location shortcuts.
•	Accessibility-first UI with clear typography, high contrast, and simple controls.
________________________________________
System Architecture
Frontend Layer
•	Framework: React.js (with Next.js for server-side rendering and optimized routing)
•	UI Components: Custom-built responsive components with CSS for rapid, consistent styling
•	Charting Library: Plotly.js for interactive multi-series line charts with legends, legends, and tooltips
•	State Management: WRIS API  for managing station selection, date filters, and API responses
•	Mobile Support: Responsive design via CSS media queries; alternative: React Native for native mobile apps
Backend Layer
•	Runtime: Django
•	Framework: Django for REST API routing and middleware
•	API Gateway: Rate-limiting, authentication, and request logging middleware
•	Data Fetching: Axios for secure HTTPS calls to India-WRIS API endpoints
•	Caching: Redis or in-memory caching to avoid redundant API calls for frequently accessed stations
•	Task Scheduling: Node-cron or Bull for periodic background syncs of DWLR data
Analytics & Data Processing
•	Language: JavaScript (Node.js) / Python (optional, for advanced ML-based trend forecasting)
•	Libraries:
o	simple-statistics or numeric.js for moving averages, linear regression, and anomaly detection
o	papaparse for CSV parsing and generation
o	moment.js or date-fns for time-series date manipulation
Database & Storage
•	Primary: PostgreSQL (for historical DWLR data, user profiles, saved locations)
•	Cache: Redis (for session management and API response caching)
•	File Storage: AWS S3 or local file system for CSV exports and report archives
Deployment & DevOps
•	Containerization: Docker for consistent development, testing, and production environments
•	Orchestration: Docker Compose (for local) or Kubernetes (for scaled production)
•	Hosting: Railway.app, AWS EC2, or Azure App Service for backend; Vercel or Netlify for frontend
•	CI/CD: GitHub Actions for automated testing, linting, and deployment pipelines
________________________________________
Technology Stack Summary
Layer	Technology	Purpose
Frontend	React.js, Next.js	Interactive UI, server-side rendering
Styling	Tailwind CSS	Responsive, utility-first styling
Charting	Plotly.js	Multi-station line charts and analytics
State	Context API / Redux	Client-side state and data management
Runtime	Node.js	Backend server runtime
Framework	Express.js	REST API and middleware
HTTP Client	Axios	India-WRIS API integration
Caching	Redis	Session and API response cache
Database	PostgreSQL	Persistent storage of DWLR history
Analytics	simple-statistics	Trend analysis, moving averages
Data Export	PapaParse	CSV parsing and generation
Scheduling	Node-cron	Background DWLR data synchronization
Container	Docker	Consistent deployment environments
Version Control	Git / GitHub	Collaborative development and CI/CD

________________________________________
Project Structure
bhujal-prototype/
├── frontend/
│ ├── public/
│ ├── src/
│ │ ├── components/
│ │ │ ├── Dashboard.js
│ │ │ ├── StationChart.js
│ │ │ ├── StatusCard.js
│ │ │ ├── StorageCalculator.js
│ │ │ └── ...
│ │ ├── pages/
│ │ │ ├── index.js (home)
│ │ │ ├── dashboard.js
│ │ │ ├── reports.js
│ │ │ └── ...
│ │ ├── styles/
│ │ │ └── globals.css (Tailwind)
│ │ ├── hooks/
│ │ │ ├── useGroundwater.js
│ │ │ ├── useStations.js
│ │ │ └── ...
│ │ └── App.js
│ ├── package.json
│ └── next.config.js
├── backend/
│ ├── routes/
│ │ ├── stations.js
│ │ ├── groundwater.js
│ │ ├── analytics.js
│ │ └── auth.js
│ ├── controllers/
│ │ ├── groundwaterController.js
│ │ ├── analyticsController.js
│ │ └── ...
│ ├── middleware/
│ │ ├── auth.js
│ │ ├── errorHandler.js
│ │ └── ...
│ ├── services/
│ │ ├── wrisAPIService.js (India-WRIS integration)
│ │ ├── trendAnalysis.js (recharge evaluation)
│ │ ├── cacheService.js (Redis)
│ │ └── ...
│ ├── models/
│ │ ├── Station.js
│ │ ├── GroundwaterReading.js
│ │ ├── User.js
│ │ └── ...
│ ├── config/
│ │ ├── database.js
│ │ ├── redis.js
│ │ └── wrisConfig.js
│ ├── server.js
│ ├── package.json
│ └── .env (environment variables)
├── docker-compose.yml
├── Dockerfile
├── .gitignore
└── README.md
________________________________________
Core Workflows
1. User Authentication & Profile Setup
•	User creates account (farmer/planner/admin role) or logs in via credentials stored in PostgreSQL.
•	Backend authenticates via JWT tokens and maintains session in Redis.
•	User selects default state–district and saves up to 5 favorite DWLR stations for quick access.
2. Station & Time-Range Selection
•	Frontend displays dropdown filters for state → district → available DWLR stations.
•	User selects one or more stations and specifies start/end date range.
•	Date validation ensures requests do not exceed available India-WRIS data window (typically last 2 years).
3. Real-Time Data Fetch & Preprocessing
•	Backend calls India-WRIS groundwater-level API endpoint with selected station IDs and date range.
•	Response data (6-hourly or daily readings in meters below ground level) is parsed by wrisAPIService.
•	Missing points are interpolated, outliers flagged, and time series aligned to common timestamps.
•	Processed data cached in Redis for 1 hour to avoid redundant API hits.
4. Recharge Trend Evaluation
•	trendAnalysis service computes:
o	Net Change: Depth difference between end and start dates (m).
o	Rate of Change: Daily or weekly rise/fall (m/day, m/week).
o	Moving Averages: 7-day and 30-day smoothed trends to filter noise.
o	Anomaly Flags: Sudden drops > 1 m/day or rises > 0.5 m/day marked as potential equipment error or extreme event.
o	Recharge/Depletion Classification: Positive rate = recharge phase; negative = depletion; near-zero = stable.
•	Results (indicators) stored temporarily in Redis and returned to frontend.
5. Visualization & Interactive Charts
•	Frontend receives processed time series and indicators via API.
•	Recharts renders multi-series line chart with:
o	One line per selected station, color-coded and labeled.
o	X-axis: dates across the selected range.
o	Y-axis: groundwater depth (meters below surface).
o	Tooltip: on hover, shows date, depth, and rate-of-change for that point.
o	Legend: clickable to toggle station visibility.
•	Status cards below chart display current depth, seasonal delta, and safe/caution/critical indicator for each station.
6. Storage Change Calculation (Optional Module)
•	User selects district, date range, and enters area and specific-yield estimates for the aquifer.
•	Backend API endpoint /api/analytics/storage-change aggregates all DWLR data across district, computes average net change, and multiplies by area and specific yield to estimate MCM delta.
•	Result displayed in summary card and exported as CSV with per-station breakdown.
7. Report Generation & Export
•	User clicks "Download CSV" on dashboard or reports page.
•	Backend generates CSV file with columns: Station Name, Start Depth (m), End Depth (m), Change (m), Rate (m/day), Recharge Phase (Y/N).
•	File streamed to browser for download; copy also archived in AWS S3 for audit trail.
________________________________________
Installation & Setup
Prerequisites
•	Node.js v16+ and npm/yarn
•	PostgreSQL v12+ (or cloud-hosted instance)
•	Redis v6+ (or cloud-hosted instance)
•	Docker & Docker Compose (for containerized deployment)
•	Git
Backend Setup
1.	Clone repository and navigate to backend directory:
git clone https://github.com/yourorg/bhujal-prototype.git
cd bhujal-prototype/backend
2.	Install dependencies:
npm install
3.	Configure environment variables (create .env file):
NODE_ENV=development
PORT=5000
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bhujal_db
DB_USER=postgres
DB_PASSWORD=your_password
REDIS_URL=redis://localhost:6379
WRIS_API_URL=https://indiawris.gov.in/api/v1
WRIS_API_KEY=your_api_key
JWT_SECRET=your_jwt_secret
4.	Initialize database:
npm run migrate
5.	Start backend server:
npm run dev
Server runs on http://localhost:5000
Frontend Setup
1.	Navigate to frontend directory:
cd ../frontend
2.	Install dependencies:
npm install
3.	Configure environment variables (create .env.local file):
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_APP_NAME=Bhujal
4.	Start development server:
npm run dev
App runs on http://localhost:3000
Docker Deployment
1.	Build and run with Docker Compose:
docker-compose up -d
This starts both backend (port 5000) and frontend (port 3000) in isolated containers.
2.	Verify containers:
docker ps
________________________________________
API Endpoints
Authentication
•	POST /api/auth/register – User registration
•	POST /api/auth/login – User login (returns JWT)
•	POST /api/auth/logout – User logout
Groundwater Data
•	GET /api/groundwater/stations – List all 5,260 DWLR stations (with filters)
•	GET /api/groundwater/:stationId – Fetch time-series data for a station (query params: startDate, endDate)
•	GET /api/groundwater/district/:districtId – Fetch data for all stations in a district
Analytics
•	POST /api/analytics/recharge-trend – Compute trend indicators for selected stations
•	GET /api/analytics/storage-change – Calculate volumetric storage change (district-level)
•	POST /api/analytics/export – Generate and download CSV report
User Profile
•	GET /api/user/profile – Retrieve user profile
•	PATCH /api/user/profile – Update user preferences and saved stations
•	GET /api/user/saved-locations – List user's favorite stations
________________________________________
Key Dependencies
Backend:
{
"express": "^4.18.0",
"axios": "^1.4.0",
"pg": "^8.9.0",
"redis": "^4.6.0",
"jsonwebtoken": "^9.0.0",
"dotenv": "^16.0.3",
"node-cron": "^3.0.2",
"simple-statistics": "^7.7.0",
"papaparse": "^5.4.1"
}
Frontend:
{
"react": "^18.2.0",
"next": "^13.4.0",
"recharts": "^2.8.0",
"tailwindcss": "^3.3.0",
"axios": "^1.4.0",
"date-fns": "^2.30.0",
"react-toastify": "^9.1.2"
}
________________________________________
Testing
Backend Tests
cd backend
npm run test
Uses Jest and Supertest for unit and integration tests.
Frontend Tests
cd frontend
npm run test
Uses Jest and React Testing Library for component and hook tests.
________________________________________
Contributing
1.	Fork the repository
2.	Create a feature branch (git checkout -b feature/your-feature)
3.	Commit changes (git commit -m 'Add your feature')
4.	Push to branch (git push origin feature/your-feature)
5.	Open a Pull Request with a clear description
________________________________________
Performance Optimization
•	API Response Caching: Redis caches DWLR data for 1 hour to minimize India-WRIS API load.
•	Frontend Code Splitting: Next.js dynamic imports and lazy-loading of chart components reduce initial bundle size.
•	Database Indexing: Indexes on (stationId, date) for fast historical queries.
•	Data Pagination: API returns paginated results; frontend implements infinite scroll for station lists.
•	Compression: gzip compression on API responses and static assets.
________________________________________
Security & Privacy
•	JWT Authentication: Tokens expire in 24 hours; refresh tokens rotate on each use.
•	HTTPS Only: All API communication encrypted; production enforces HSTS headers.
•	Data Validation: Server-side validation of all input (date ranges, station IDs, area estimates).
•	Rate Limiting: 100 requests per minute per user to prevent abuse.
•	Audit Logging: All data exports logged with user ID and timestamp for governance.
________________________________________
Known Limitations & Future Work
Current Limitations
•	Data freshness: DWLR readings from India-WRIS may have 6–12 hour lag depending on station telemetry.
•	Spatial granularity: Analysis at station level; district-level aggregates use simple averaging.
•	Offline support: Mobile app requires active internet; offline caching planned for v2.
Planned Enhancements
v2.0 (Q1 2025)
•	ML-Based Forecasting: Train LSTM models to predict groundwater levels 1–3 months ahead.
•	Rainfall Integration: Merge rainfall data from India-WRIS to estimate recharge contribution from monsoon.
•	Soil Moisture Layer: Integrate ISMN (International Soil Moisture Network) to correlate soil moisture with recharge rates.
•	Push Notifications: Alert farmers when water levels drop below critical thresholds.
v2.5 (Q2 2025)
•	Offline Syncing: Progressive Web App (PWA) for offline access to cached station data.
•	Mobile Native App: React Native version for iOS with enhanced geolocation features.
•	Groundwater Quality: Integrate water-quality parameters (EC, pH, nitrate) from CGWB if available.
v3.0 (Q3 2025)
•	District Dashboard: Aggregated reports for block and district administrators with policy-relevant metrics.
•	Farmer Cooperatives: Collective dashboards allowing farmer groups to share and compare nearby station data.
•	Sustainability Index: Compute local Water Exploitation Index (WEI) based on extraction vs. recharge.
•	Open Data: Expose anonymized district-level aggregates via open APIs for research and third-party apps.
________________________________________
License
This prototype is developed under the Smart India Hackathon 2025 initiative. Intellectual property and usage rights are governed by SIH terms and the sponsoring ministry (Ministry of Jal Shakti, Department of Water Resources).
________________________________________
Support & Contact
•	Documentation: See /docs folder for API reference and deployment guides.
•	Issue Tracking: GitHub Issues for bug reports and feature requests.
•	Email: contact@bhujal-prototype.com
•	Slack: Join our community channel for real-time discussion and support.
________________________________________
Acknowledgments
•	India-WRIS: For providing open access to DWLR and hydrological data via APIs.
•	CGWB (Central Groundwater Board): For operating the 5,260 DWLR station network.
•	Smart India Hackathon 2025: For the problem statement and platform.
•	Community Contributors: All developers and testers who contributed to this prototype.
________________________________________
Last Updated: December 09, 2025
Version: 1.0.0
