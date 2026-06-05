# ScanX Web Dialer Backend

## 1. Project Overview

The **ScanX Web Dialer Backend** is a FastAPI-based backend service for the ScanX web-based dialer and call monitoring system.

This backend is responsible for:

* Patient search by name, phone, email, or appointment data.
* Outgoing browser-based calls using Twilio Voice JavaScript SDK.
* Twilio voice token generation.
* Twilio outbound call TwiML generation.
* Incoming call forwarding preservation.
* Missed call tracking.
* Recent call and missed call APIs.
* Patient call history lookup.
* Google Chat missed-call notification placeholder.
* WebSocket live dashboard updates.
* Call notes and call disposition support.
* Dormant IVR foundation for future routing.

This project is part of a new separate application from the earlier Google Chat click-to-call app. The earlier app allowed staff to click a Google Chat card button and start a Twilio call. This new backend is designed for a complete **web dialer dashboard** with manual dialing, patient lookup, call history, and missed call monitoring.

---

# 2. Current Phase

## Phase 1 Backend Scope

The backend currently supports the Phase 1 foundation:

* Health check APIs.
* Database connection with Cloud SQL PostgreSQL.
* Existing appointment/patient/call lookup.
* Patient search using the existing `appointment` table.
* Known/unknown caller matching using phone number.
* Patient call history using existing `call_logs`.
* Recent calls API.
* Missed calls API.
* Call notes API.
* Call disposition API.
* WebSocket live update manager.
* Development broadcast test route.
* Google Chat missed-call notification placeholder.
* Twilio Voice SDK token endpoint.
* Twilio outgoing call TwiML endpoint.
* Twilio incoming call forwarding placeholder.
* Twilio status callback endpoint.

## Not Yet Fully Verified

The backend code is ready for Phase 1 testing, but final production readiness requires end-to-end testing with:

* Twilio Voice SDK frontend.
* ngrok or deployed Cloud Run backend.
* Twilio TwiML App pointing to `/voice/outgoing`.
* Twilio phone number webhook pointing to `/voice/incoming`, only if incoming call tracking is enabled.
* Google Chat webhook URL for missed-call alerts.

---

# 3. High-Level Purpose

The purpose of this backend is to act as the central API and voice orchestration layer between:

```text
React Web Dialer Frontend
        ↓
FastAPI Backend
        ↓
Cloud SQL PostgreSQL
        ↓
Twilio Programmable Voice
        ↓
Patient / Caller Phone
```

It enables clinic staff to:

1. Search for patients.
2. Dial patients from the browser.
3. Dial any manual number from a virtual keypad.
4. View recent calls.
5. View missed calls.
6. Identify missed callers as known patients if possible.
7. See unknown callers if no match is found.
8. View call history by phone number.
9. Receive live dashboard updates using WebSockets.
10. Send missed-call alerts to Google Chat later.

---

# 4. Important Business Context

The client currently has a company phone number where incoming calls are forwarded to the client’s device.

For Phase 1, this must **not be disturbed**.

Therefore, this backend is designed to:

* Preserve the current forwarding behavior.
* Track incoming calls if Twilio is in the incoming call path.
* Detect missed/unanswered calls where Twilio status callbacks are available.
* Notify Google Chat for missed calls when a webhook URL is provided.
* Keep IVR dormant for future use.

The backend does **not** currently make clinic tablets answer incoming calls. That may be added in a future phase.

---

# 5. Technology Stack

## Backend Framework

```text
FastAPI
```

FastAPI is used because it is fast, clean, API-friendly, and supports both REST APIs and WebSockets.

## Server

```text
Uvicorn
```

Uvicorn runs the FastAPI app locally and in Cloud Run.

## Database

```text
Cloud SQL PostgreSQL
```

The backend connects to the existing ScanX PostgreSQL database.

## Database Library

```text
SQLAlchemy
psycopg2-binary
```

SQLAlchemy is used for executing SQL queries and managing database sessions.

## Voice Provider

```text
Twilio Programmable Voice
Twilio Voice JavaScript SDK
```

Twilio handles browser-based calling, call control, status callbacks, and future IVR support.

## Realtime

```text
FastAPI WebSockets
```

WebSockets are used for live dashboard updates.

## Notifications

```text
Google Chat Incoming Webhook
```

A placeholder is included for missed-call alerts.

## Deployment Target

```text
Google Cloud Run
```

The backend is designed to be deployed on Cloud Run using source deployment or container deployment.

---

# 6. Project Structure

```text
web_dailer_backend/

├── app.py
├── config.py
├── database.py
├── requirements.txt
├── Procfile
├── .env
├── .env.example
├── .gitignore
├── .gcloudignore
│
├── routes/
│   ├── __init__.py
│   ├── health.py
│   ├── patients.py
│   ├── calls.py
│   ├── voice.py
│   ├── websocket.py
│   ├── notifications.py
│   └── dev.py
│
├── services/
│   ├── __init__.py
│   ├── patient_service.py
│   ├── call_service.py
│   ├── twilio_service.py
│   ├── websocket_manager.py
│   └── notification_service.py
│
├── schemas/
│   ├── __init__.py
│   ├── patient_schema.py
│   ├── call_schema.py
│   └── websocket_schema.py
│
└── utils/
    ├── __init__.py
    ├── phone.py
    └── security.py
```

---

# 7. File-by-File Explanation

---

## 7.1 `app.py`

## Purpose

`app.py` is the main entry point of the FastAPI application.

It creates the FastAPI app, configures CORS, and registers all route modules.

## What It Contains

```python
app = FastAPI(title=APP_NAME)
```

This creates the FastAPI application object.

It also includes routers such as:

```python
app.include_router(health_router)
app.include_router(patients_router)
app.include_router(calls_router)
app.include_router(websocket_router)
app.include_router(notifications_router)
app.include_router(dev_router)
app.include_router(voice_router)
```

## Responsibilities

* Initialize the FastAPI app.
* Configure CORS.
* Register all API routes.
* Expose root endpoint `/`.
* Serve as the main Uvicorn application target.

## Data Flow Through This File

All incoming API requests first enter the FastAPI app created in `app.py`.

Then FastAPI routes the request to the appropriate router:

```text
Incoming HTTP Request
        ↓
app.py
        ↓
Matching route module
        ↓
Service layer
        ↓
Database / Twilio / WebSocket / Google Chat
```

## Important Note

Earlier versions of this file called:

```python
create_companion_tables_if_not_exists()
```

on startup.

This was removed because the companion tables were created manually using Cloud Shell. The backend should not try to create those tables locally during startup unless intentionally re-enabled.

---

## 7.2 `config.py`

## Purpose

`config.py` centralizes all environment variable loading.

## What It Contains

It loads `.env` using:

```python
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
```

Then it reads configuration values such as:

```python
APP_NAME
APP_ENV
BASE_URL
API_SECRET
ENABLE_IVR
DB_USER
DB_PASSWORD
DB_NAME
DB_HOST
DB_PORT
INSTANCE_CONNECTION_NAME
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_API_KEY_SID
TWILIO_API_KEY_SECRET
TWILIO_TWIML_APP_SID
TWILIO_PHONE_NUMBER
CLIENT_FORWARD_NUMBER
ENABLE_GCHAT_MISSED_CALL_ALERTS
GCHAT_MISSED_CALL_WEBHOOK_URL
```

## Responsibilities

* Load local `.env`.
* Provide app-level configuration.
* Provide database configuration.
* Provide Twilio configuration.
* Provide Google Chat notification configuration.
* Provide dormant IVR feature flag.

## Why This File Exists

Without this file, environment variables would be scattered across multiple files. That makes configuration hard to maintain and harder to debug.

This file gives the whole backend one source of truth for configuration.

## Local vs Cloud Run Usage

### Local Development

Local `.env` should usually use:

```env
DB_HOST=127.0.0.1
DB_PORT=5432
INSTANCE_CONNECTION_NAME=
```

This works with Cloud SQL Auth Proxy.

### Cloud Run

Cloud Run should use:

```env
INSTANCE_CONNECTION_NAME=project:region:instance
```

and should be deployed with:

```bash
--add-cloudsql-instances project:region:instance
```

---

## 7.3 `database.py`

## Purpose

`database.py` creates the SQLAlchemy database engine and session factory.

## What It Contains

Main function:

```python
build_database_url()
```

This function decides whether the app should connect using:

1. Local TCP connection.
2. Cloud Run `/cloudsql/...` socket connection.

It also creates:

```python
engine = create_engine(...)
SessionLocal = sessionmaker(...)
```

And provides:

```python
test_db_connection()
```

## Responsibilities

* Build safe PostgreSQL connection URL.
* Connect to Cloud SQL PostgreSQL.
* Provide reusable database sessions.
* Test database connectivity.

## Why `URL.create()` Is Used

The database connection is created using SQLAlchemy `URL.create()` instead of string concatenation.

This is important because database passwords can contain special characters like:

```text
@
#
$
%
/
```

If the URL is manually built, a password like `ScanX@2025` can break the host parsing.

Using `URL.create()` prevents those errors.

## Data Flow

```text
Service function
        ↓
SessionLocal()
        ↓
SQLAlchemy engine
        ↓
PostgreSQL database
```

---

## 7.4 `requirements.txt`

## Purpose

Lists all Python dependencies required by the backend.

## Current Dependencies

```text
fastapi
uvicorn
python-dotenv
sqlalchemy
psycopg2-binary
twilio
python-multipart
httpx
pydantic
```

## Dependency Explanation

### `fastapi`

Backend web framework.

### `uvicorn`

ASGI server used to run FastAPI.

### `python-dotenv`

Loads `.env` file locally.

### `sqlalchemy`

Database query and session management.

### `psycopg2-binary`

PostgreSQL driver.

### `twilio`

Twilio SDK for tokens and TwiML.

### `python-multipart`

Required for reading Twilio form POST payloads using:

```python
await request.form()
```

### `httpx`

Used to send Google Chat webhook requests.

### `pydantic`

Used for request validation and schemas.

---

## 7.5 `Procfile`

## Purpose

Used by Cloud Run source deployment/buildpacks to know how to start the application.

## Content

```Procfile
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

## Why `$PORT` Is Required

Cloud Run dynamically provides the port through the environment variable `PORT`.

The backend must listen on that port.

Do not hardcode `5000` or `8000` in production Cloud Run.

---

## 7.6 `.env`

## Purpose

Local environment variable file containing real secrets and local configuration.

## Important

This file should **not** be committed to Git.

It contains sensitive data such as:

```text
DB_PASSWORD
TWILIO_AUTH_TOKEN
TWILIO_API_KEY_SECRET
GCHAT_MISSED_CALL_WEBHOOK_URL
```

---

## 7.7 `.env.example`

## Purpose

A safe template showing which environment variables are required.

This file should be committed to Git.

Developers copy it:

```bash
copy .env.example .env
```

or:

```bash
cp .env.example .env
```

Then they fill in real values.

---

## 7.8 `.gitignore`

## Purpose

Prevents local secrets, virtual environments, and cache files from being committed.

Recommended content:

```gitignore
.env
env/
venv/
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
```

---

## 7.9 `.gcloudignore`

## Purpose

Controls which files are ignored during Google Cloud source deployment.

Recommended content:

```gitignore
.env
env/
venv/
__pycache__/
*.pyc
.git/
.pytest_cache/
.DS_Store
```

This prevents Cloud Run deployment from uploading local secrets or virtual environments.

---

# 8. Routes Folder

The `routes/` folder contains FastAPI routers. Each router handles a specific area of the application.

---

## 8.1 `routes/health.py`

## Purpose

Provides health check APIs.

## Endpoints

```text
GET /health
GET /health/db
```

## `GET /health`

Returns basic service status.

Example:

```json
{
  "status": "ok",
  "service": "ScanX Web Dialer Backend"
}
```

## `GET /health/db`

Tests database connectivity by calling:

```python
test_db_connection()
```

Example success response:

```json
{
  "status": "ok",
  "database": "connected"
}
```

Example error response:

```json
{
  "status": "error",
  "database": "not_connected",
  "error": "..."
}
```

## Data Flow

```text
GET /health/db
        ↓
routes/health.py
        ↓
database.test_db_connection()
        ↓
PostgreSQL
        ↓
Response
```

---

## 8.2 `routes/patients.py`

## Purpose

Provides patient search, phone lookup, and patient call history APIs.

## Endpoints

```text
GET /patients/search
GET /patients/lookup-by-phone
GET /patients/call-history
```

---

## `GET /patients/search?q=...`

Searches patients using the existing `appointment` table.

Search supports:

* First name.
* Last name.
* Full name.
* Email.
* Phone number.

Example:

```text
GET /patients/search?q=John
```

Response:

```json
{
  "query": "John",
  "count": 2,
  "results": []
}
```

## Why It Uses `appointment`

The existing `patients` table does not visibly contain a phone column.

The `appointment` table contains:

```text
appointment_id
first_name
last_name
phone
email
clinic_id
location
calendar
appointment_datetime
```

So Phase 1 uses `appointment` as the primary patient lookup source.

---

## `GET /patients/lookup-by-phone?phone=...`

Attempts to identify whether a caller is a known patient.

Example:

```text
GET /patients/lookup-by-phone?phone=+15551234567
```

If matched:

```json
{
  "found": true,
  "display_name": "John Smith",
  "phone": "+15551234567",
  "patient": {}
}
```

If not matched:

```json
{
  "found": false,
  "display_name": "Unknown Caller",
  "phone": "+15551234567",
  "patient": null
}
```

This API is important for missed call display.

---

## `GET /patients/call-history?phone=...`

Returns call history for a patient or caller phone number.

Example:

```text
GET /patients/call-history?phone=+15551234567
```

This reads from `call_logs` and joins appointment information where possible.

---

## Data Flow

```text
Patient Search Request
        ↓
routes/patients.py
        ↓
services/patient_service.py
        ↓
appointment / clinics / call_logs tables
        ↓
JSON response
```

---

## 8.3 `routes/calls.py`

## Purpose

Provides APIs for recent calls, missed calls, call details, notes, and dispositions.

## Endpoints

```text
GET  /calls/recent
GET  /calls/missed
GET  /calls/{call_id}
POST /calls/{call_id}/notes
POST /calls/{call_id}/disposition
```

---

## `GET /calls/recent`

Returns recent calls from the existing `call_logs` table.

It tries to match each call to an appointment/patient using:

* `appointment_id`.
* `patient_number`.

Response includes helper fields:

```text
display_name
is_known_patient
is_missed
```

If a patient is matched:

```text
display_name = "John Smith"
is_known_patient = true
```

If not:

```text
display_name = "Unknown Caller"
is_known_patient = false
```

---

## `GET /calls/missed`

Returns missed/unanswered calls.

Missed statuses include:

```text
no-answer
busy
failed
canceled
cancelled
```

These are mapped in `call_service.py` using:

```python
MISSED_STATUSES = {"no-answer", "busy", "failed", "canceled", "cancelled"}
```

---

## `GET /calls/{call_id}`

Returns detailed information for one call.

Used for call detail panel, patient drawer, or history view.

---

## `POST /calls/{call_id}/notes`

Adds a note to a call.

Uses the companion table:

```text
dialer_call_notes
```

Example note:

```text
Patient requested callback tomorrow.
```

---

## `POST /calls/{call_id}/disposition`

Adds a business outcome to a call.

Uses the companion table:

```text
dialer_call_dispositions
```

Example dispositions:

```text
Answered
No Answer
Left Voicemail
Callback Required
Wrong Number
Reschedule Requested
```

---

## Data Flow

```text
Frontend calls /calls/recent
        ↓
routes/calls.py
        ↓
services/call_service.py
        ↓
call_logs + appointment + clinics
        ↓
Formatted response
        ↓
Frontend dashboard
```

---

## 8.4 `routes/websocket.py`

## Purpose

Provides WebSocket connection for live call dashboard updates.

## Endpoints

```text
WS  /ws/calls
GET /ws/status
```

---

## `WS /ws/calls`

Frontend connects to this endpoint for realtime events.

Example frontend URL:

```text
ws://localhost:5000/ws/calls?client_id=dashboard_1&clinic_id=1
```

On connection, backend sends:

```json
{
  "type": "connection_established",
  "message": "Connected to ScanX Web Dialer live updates.",
  "meta": {
    "client_id": "dashboard_1",
    "clinic_id": "1"
  }
}
```

The frontend can send:

```text
ping
```

Backend responds:

```json
{
  "type": "pong",
  "message": "alive"
}
```

---

## `GET /ws/status`

Returns currently connected WebSocket clients.

Example:

```json
{
  "active_connections": 1,
  "clients": [
    {
      "client_id": "dashboard_1",
      "clinic_id": "1"
    }
  ]
}
```

## Current Limitation

The WebSocket connection manager is in-memory.

This is fine for:

```text
Local development
Cloud Run single-instance MVP
```

If Cloud Run scales to multiple instances, events may reach one instance while WebSocket clients are connected to another instance.

Future solution:

```text
Redis Pub/Sub or Google Pub/Sub + WebSocket broadcaster
```

---

## 8.5 `routes/notifications.py`

## Purpose

Provides a test endpoint for Google Chat missed-call notifications.

## Endpoint

```text
POST /notifications/test-gchat
```

This sends a sample missed-call payload to the configured Google Chat webhook.

If webhook URL is not configured, it returns:

```json
{
  "sent": false,
  "reason": "GCHAT_MISSED_CALL_WEBHOOK_URL not configured"
}
```

---

## 8.6 `routes/dev.py`

## Purpose

Development-only helper routes.

## Endpoint

```text
POST /dev/broadcast-test
```

This broadcasts a test WebSocket event to all connected clients.

Used to verify WebSocket integration before frontend is ready.

## Important

This route should be removed or disabled before production.

---

## 8.7 `routes/voice.py`

## Purpose

Handles Twilio Voice SDK and Twilio webhook routes.

## Endpoints

```text
GET  /voice/token
POST /voice/outgoing
POST /voice/incoming
POST /voice/status
```

---

## `GET /voice/token`

Generates a temporary Twilio Voice SDK token for the browser.

Frontend will call this before initializing Twilio Device.

Example:

```text
GET /voice/token?identity=scanx_web_dialer
```

Response:

```json
{
  "identity": "scanx_web_dialer",
  "token": "eyJ..."
}
```

## Why This Is Needed

The frontend cannot use permanent Twilio credentials.

The backend securely generates a temporary access token using:

```text
TWILIO_ACCOUNT_SID
TWILIO_API_KEY_SID
TWILIO_API_KEY_SECRET
TWILIO_TWIML_APP_SID
```

---

## `POST /voice/outgoing`

This is called by Twilio when the browser starts an outgoing call through Twilio Voice SDK.

Expected form parameters:

```text
to
staff_phone
appointment_id
CallSid
```

Flow:

```text
Browser Twilio SDK starts call
        ↓
Twilio calls /voice/outgoing
        ↓
Backend creates call_logs row
        ↓
Backend stores event in dialer_call_events
        ↓
Backend broadcasts outgoing_call_started over WebSocket
        ↓
Backend returns TwiML Dial response
        ↓
Twilio dials patient/manual number
```

Returned TwiML instructs Twilio to dial the destination number using the ScanX Twilio caller ID.

---

## `POST /voice/incoming`

This is for incoming calls to the ScanX company number.

Current Phase 1 behavior:

* Do not ring tablets.
* Do not activate IVR.
* Preserve current forwarding to `CLIENT_FORWARD_NUMBER`.
* Log inbound call if Twilio is in the incoming call path.
* Match caller to known patient if possible.
* Broadcast incoming call started event over WebSocket.

Flow:

```text
Caller calls ScanX number
        ↓
Twilio calls /voice/incoming
        ↓
Backend logs inbound call
        ↓
Backend tries to identify patient by phone
        ↓
Backend returns TwiML to forward call to CLIENT_FORWARD_NUMBER
```

Important:

This only works if the incoming ScanX number is controlled by Twilio or routes through Twilio.

If incoming forwarding is outside Twilio, this backend cannot know call status unless the external phone system provides webhooks.

---

## `POST /voice/status`

This receives Twilio call status callbacks.

It handles statuses such as:

```text
initiated
ringing
in-progress
completed
busy
failed
no-answer
canceled
```

Responsibilities:

1. Parse Twilio form payload.
2. Update `call_logs.status`.
3. Update `call_logs.duration`.
4. Insert raw event into `dialer_call_events`.
5. Broadcast `call_status_changed` over WebSocket.
6. If missed/unanswered, broadcast `missed_call`.
7. If missed/unanswered, send Google Chat alert if configured.
8. Log notification attempt into `dialer_call_notifications`.

---

# 9. Services Folder

The `services/` folder contains business logic. Routes should stay thin and call services for actual work.

---

## 9.1 `services/patient_service.py`

## Purpose

Handles patient search, patient lookup by phone, and patient call history.

## Important Functions

### `search_patients(query, limit)`

Searches the `appointment` table by:

* First name.
* Last name.
* Full name.
* Email.
* Phone.

Joins with `clinics` for clinic display.

### `find_patient_by_phone(phone)`

Attempts to match a caller phone number to the most relevant appointment.

Used by:

* Missed call matching.
* Incoming caller identification.
* Known/unknown caller logic.

### `get_patient_call_history_by_phone(phone, limit)`

Gets calls from `call_logs` for the given phone number.

Joins with appointment and clinic data when available.

---

## 9.2 `services/call_service.py`

## Purpose

Handles all database operations related to calls.

It uses the existing `call_logs` table and the new `dialer_*` companion tables.

## Important Constants

```python
MISSED_STATUSES = {"no-answer", "busy", "failed", "canceled", "cancelled"}
```

## Important Functions

### `create_call_log(...)`

Creates a new row in the existing `call_logs` table.

Used for:

* Outgoing calls.
* Incoming calls.

### `update_call_log_status(call_sid, status, duration)`

Updates a call log based on Twilio `CallSid`.

Used by `/voice/status`.

### `get_call_log_by_sid(call_sid)`

Fetches a call log using Twilio `CallSid`.

### `create_call_event(...)`

Inserts raw Twilio webhook event into:

```text
dialer_call_events
```

### `get_recent_calls(limit)`

Returns recent calls with patient matching.

### `get_missed_calls(limit)`

Returns missed calls using `MISSED_STATUSES`.

### `get_call_by_id(call_id)`

Returns detailed call information.

### `add_call_note(call_log_id, note, created_by)`

Adds note to `dialer_call_notes`.

### `add_call_disposition(call_log_id, disposition, created_by)`

Adds disposition to `dialer_call_dispositions`.

### `_format_call_row(row)`

Adds helper frontend fields:

```text
display_name
is_known_patient
is_missed
```

---

## 9.3 `services/twilio_service.py`

## Purpose

Handles Twilio token generation and TwiML generation.

## Important Functions

### `generate_voice_token(identity)`

Creates a Twilio Voice SDK access token for the browser.

Uses:

```text
TWILIO_ACCOUNT_SID
TWILIO_API_KEY_SID
TWILIO_API_KEY_SECRET
TWILIO_TWIML_APP_SID
```

### `build_outgoing_call_twiml(to_number)`

Builds TwiML for outbound calls.

Returns XML like:

```xml
<Response>
  <Dial callerId="+1SCANXNUMBER">
    <Number>+15551234567</Number>
  </Dial>
</Response>
```

### `build_current_forwarding_twiml()`

Builds TwiML to preserve the current incoming forwarding behavior.

If `ENABLE_IVR=false`, it forwards to:

```text
CLIENT_FORWARD_NUMBER
```

If `ENABLE_IVR=true`, it currently returns dormant placeholder behavior.

---

## 9.4 `services/websocket_manager.py`

## Purpose

Manages active WebSocket clients.

## Important Functions

### `connect(websocket, meta)`

Accepts and stores a WebSocket connection.

### `disconnect(websocket)`

Removes connection from memory.

### `send_personal_message(websocket, message)`

Sends a message to one client.

### `broadcast(message)`

Sends a message to all connected clients.

### `broadcast_call_event(event_type, payload)`

Standard helper for broadcasting call events.

### `get_connection_count()`

Returns active WebSocket count.

### `get_connections_meta()`

Returns client metadata.

---

## 9.5 `services/notification_service.py`

## Purpose

Handles Google Chat missed-call notifications.

## Important Functions

### `build_missed_call_message(call_data)`

Builds a Google Chat text payload.

Known patient example:

```text
📞 Missed Call Alert

Caller: John Smith
Phone: +15551234567
Status: no-answer
Time: 2026-06-05 10:30
```

Unknown caller example:

```text
📞 Missed Call Alert

Caller: Unknown Caller
Phone: +15551234567
Status: no-answer
Time: 2026-06-05 10:30
```

### `send_gchat_missed_call_alert(call_data)`

Sends missed call alert to Google Chat webhook if enabled and configured.

### `log_notification_result(...)`

Logs notification send attempt in:

```text
dialer_call_notifications
```

---

# 10. Utils Folder

---

## 10.1 `utils/phone.py`

## Purpose

Contains phone number normalization helpers.

## Important Functions

### `normalize_phone(phone)`

Basic cleaning:

* Trims spaces.
* Keeps leading `+`.
* Removes non-digits.
* Returns `None` for empty values.

Example:

```text
(555) 123-4567 → 5551234567
+1 555-123-4567 → +15551234567
```

### `phone_search_pattern(phone)`

Creates a loose phone search value by removing the plus sign.

Used for matching database values that may be stored in different formats.

## Future Improvement

Use the `phonenumbers` Python package for stricter E.164 validation.

---

## 10.2 `utils/security.py`

## Purpose

Reserved for future security helpers.

Potential future use:

* API secret validation.
* Twilio webhook signature validation.
* JWT validation.
* Role checks.
* Request authentication.

---

# 11. Schemas Folder

The `schemas/` folder is reserved for Pydantic request/response models.

Current route files use inline Pydantic models for simple payloads.

Future recommended schemas:

```text
patient_schema.py
call_schema.py
websocket_schema.py
```

This will improve type safety and frontend integration later.

---

# 12. Database Tables

---

## 12.1 Existing Tables Used

This backend reads and writes to some existing ScanX tables.

---

## `appointment`

Used as the primary patient lookup source.

Important columns:

```text
appointment_id
first_name
last_name
phone
email
appointment_type
category
appointment_datetime
date
time
clinic_id
location
calendar
status_label
created_at
updated_at
```

Why used:

The existing `patients` table does not visibly contain `phone`, but `appointment` does.

---

## `clinics`

Used for clinic metadata.

Important columns:

```text
id
name
address
city
latitude
longitude
phone
map_link
timezone
```

---

## `call_logs`

Used as the main call log table.

Important columns:

```text
id
appointment_id
staff_phone
patient_number
direction
call_sid
status
duration
created_at
updated_at
```

This table stores:

* Incoming call logs.
* Outgoing call logs.
* Status.
* Duration.
* Twilio Call SID.

---

# 13. New Companion Tables

These were created manually using Cloud Shell.

The backend should not modify existing tables directly.

---

## `dialer_call_events`

Stores raw Twilio webhook events.

Purpose:

* Debugging.
* Auditing.
* Full call lifecycle history.

---

## `dialer_call_notifications`

Stores Google Chat notification attempts.

Purpose:

* Track whether missed-call alert was sent.
* Store errors if notification failed.

---

## `dialer_call_notes`

Stores staff notes against calls.

Purpose:

* Operational follow-up.
* Comments like “patient requested callback.”

---

## `dialer_call_dispositions`

Stores business outcomes selected by staff.

Purpose:

* Track operational result beyond Twilio technical status.

---

## `dialer_ivr_config`

Stores dormant IVR configuration.

Purpose:

* Keep future IVR support planned but inactive.

---

# 14. Backend Data Flow

---

## 14.1 Patient Search Flow

```text
Frontend search input
        ↓
GET /patients/search?q=...
        ↓
routes/patients.py
        ↓
services/patient_service.search_patients()
        ↓
appointment table
        ↓
clinics table
        ↓
JSON response
        ↓
Frontend patient list
```

---

## 14.2 Patient Lookup by Phone Flow

```text
Phone number
        ↓
GET /patients/lookup-by-phone?phone=...
        ↓
normalize phone
        ↓
search appointment.phone
        ↓
match latest/upcoming appointment
        ↓
return known patient or Unknown Caller
```

---

## 14.3 Patient Call History Flow

```text
Phone number
        ↓
GET /patients/call-history?phone=...
        ↓
search call_logs.patient_number
        ↓
join appointment by appointment_id or phone
        ↓
return call list
```

---

## 14.4 Recent Calls Flow

```text
Frontend opens dashboard
        ↓
GET /calls/recent
        ↓
services/call_service.get_recent_calls()
        ↓
call_logs
        ↓
appointment
        ↓
clinics
        ↓
formatted call rows
        ↓
Frontend recent call list
```

---

## 14.5 Missed Calls Flow

```text
Frontend opens missed calls
        ↓
GET /calls/missed
        ↓
filter call_logs.status in missed statuses
        ↓
join appointment to identify patient
        ↓
return known patient or Unknown Caller
```

---

## 14.6 Outgoing Call Flow

```text
Frontend Twilio Voice SDK
        ↓
Gets token from /voice/token
        ↓
device.connect({ to: "+15551234567" })
        ↓
Twilio calls POST /voice/outgoing
        ↓
Backend creates call_logs row
        ↓
Backend creates dialer_call_events row
        ↓
Backend broadcasts outgoing_call_started over WebSocket
        ↓
Backend returns TwiML Dial
        ↓
Twilio calls patient
        ↓
Twilio sends status updates to /voice/status
```

---

## 14.7 Incoming Call Flow

```text
Caller calls ScanX company number
        ↓
Twilio calls POST /voice/incoming
        ↓
Backend logs inbound call
        ↓
Backend tries to identify caller from appointment.phone
        ↓
Backend broadcasts incoming_call_started
        ↓
Backend returns TwiML to forward to CLIENT_FORWARD_NUMBER
        ↓
Call proceeds as current forwarding flow
```

Important:

This only works if Twilio is actually in the incoming call path.

---

## 14.8 Call Status Flow

```text
Twilio sends POST /voice/status
        ↓
Backend reads CallSid, CallStatus, Duration
        ↓
Backend updates call_logs
        ↓
Backend inserts dialer_call_events
        ↓
Backend broadcasts call_status_changed
        ↓
If status is missed:
            ↓
        broadcast missed_call
            ↓
        send Google Chat alert
            ↓
        log notification result
            ↓
        broadcast missed_call_notification_sent
```

---

## 14.9 WebSocket Flow

```text
Frontend connects to /ws/calls
        ↓
Backend stores connection
        ↓
Backend sends connection_established
        ↓
Twilio/status/event happens
        ↓
Backend broadcasts event
        ↓
Frontend dashboard updates instantly
```

---

# 15. Environment Variables

Example `.env.example`:

```env
# App
APP_NAME=ScanX Web Dialer Backend
APP_ENV=local
BASE_URL=http://localhost:5000

# Security
API_SECRET=change-this-secret
ENABLE_IVR=false

# Database
DB_USER=postgres
DB_PASSWORD=your_database_password
DB_NAME=scanx_app
DB_HOST=127.0.0.1
DB_PORT=5432
INSTANCE_CONNECTION_NAME=

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_API_KEY_SID=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_KEY_SECRET=your_twilio_api_key_secret
TWILIO_TWIML_APP_SID=APxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX

# Current incoming forwarding number
CLIENT_FORWARD_NUMBER=+1XXXXXXXXXX

# Google Chat missed call alerts
ENABLE_GCHAT_MISSED_CALL_ALERTS=true
GCHAT_MISSED_CALL_WEBHOOK_URL=
```

---

# 16. Local Development Setup

---

## 16.1 Create Virtual Environment

```bash
python -m venv venv
```

Activate on Windows:

```bash
venv\Scripts\activate
```

---

## 16.2 Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 16.3 Configure `.env`

Copy:

```bash
copy .env.example .env
```

Then update real values.

For local Cloud SQL Auth Proxy:

```env
DB_HOST=127.0.0.1
DB_PORT=5432
INSTANCE_CONNECTION_NAME=
```

---

## 16.4 Start Cloud SQL Auth Proxy

In a separate terminal:

```bash
cloud-sql-proxy vernal-maker-473121-k4:us-central1:scanx-postgres-db --port 5432
```

---

## 16.5 Run Backend

```bash
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

---

## 16.6 Test Health

```text
http://localhost:5000/health
```

```text
http://localhost:5000/health/db
```

---

# 17. API Testing

---

## Root

```text
GET /
```

---

## Health

```text
GET /health
GET /health/db
```

---

## Patient Search

```text
GET /patients/search?q=John
GET /patients/search?q=555
```

---

## Lookup by Phone

```text
GET /patients/lookup-by-phone?phone=+15551234567
```

---

## Patient Call History

```text
GET /patients/call-history?phone=+15551234567
```

---

## Recent Calls

```text
GET /calls/recent
```

---

## Missed Calls

```text
GET /calls/missed
```

---

## Call Detail

```text
GET /calls/{call_id}
```

---

## Add Note

```text
POST /calls/{call_id}/notes
```

Body:

```json
{
  "note": "Patient requested callback tomorrow.",
  "created_by": "admin"
}
```

---

## Add Disposition

```text
POST /calls/{call_id}/disposition
```

Body:

```json
{
  "disposition": "Callback Required",
  "created_by": "admin"
}
```

---

## WebSocket Status

```text
GET /ws/status
```

---

## Twilio Token

```text
GET /voice/token?identity=test_dialer
```

---

## Incoming Call Test

Use Postman or Thunder Client:

```text
POST /voice/incoming
```

Form data:

```text
From=+15551234567
CallSid=TEST_INBOUND_123
```

---

## Status Callback Test

```text
POST /voice/status
```

Form data:

```text
CallSid=TEST_INBOUND_123
CallStatus=no-answer
CallDuration=0
```

---

## Notification Test

```text
POST /notifications/test-gchat
```

---

## WebSocket Broadcast Test

```text
POST /dev/broadcast-test
```

---

# 18. Twilio Setup

---

## 18.1 Twilio Voice SDK

Frontend will use Twilio Voice JavaScript SDK.

The backend provides token at:

```text
GET /voice/token
```

---

## 18.2 TwiML App

In Twilio Console:

```text
Voice → TwiML Apps
```

Set Voice Request URL:

```text
https://YOUR_BACKEND_URL/voice/outgoing
```

Method:

```text
POST
```

---

## 18.3 Incoming Number Webhook

Only if incoming call tracking should be enabled and the current forwarding is Twilio-based:

```text
Phone Numbers → Active Numbers → Your ScanX Number
```

Set incoming webhook:

```text
https://YOUR_BACKEND_URL/voice/incoming
```

Method:

```text
POST
```

Important:

This must preserve the current forwarding behavior to `CLIENT_FORWARD_NUMBER`.

---

## 18.4 Status Callback

The backend uses:

```text
/voice/status
```

for call status updates.

---

# 19. Google Chat Notification Setup

When client provides Google Chat webhook URL, set:

```env
GCHAT_MISSED_CALL_WEBHOOK_URL=https://chat.googleapis.com/...
ENABLE_GCHAT_MISSED_CALL_ALERTS=true
```

Missed call statuses trigger notifications:

```text
no-answer
busy
failed
canceled
cancelled
```

Notification result is stored in:

```text
dialer_call_notifications
```

---

# 20. Cloud Run Deployment Notes

---

## 20.1 Required APIs

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com
```

---

## 20.2 Deploy from Source

```bash
gcloud run deploy scanx-web-dialer-backend --source . --region us-central1 --allow-unauthenticated --add-cloudsql-instances vernal-maker-473121-k4:us-central1:scanx-postgres-db
```

Windows CMD single line:

```cmd
gcloud run deploy scanx-web-dialer-backend --source . --region us-central1 --allow-unauthenticated --add-cloudsql-instances vernal-maker-473121-k4:us-central1:scanx-postgres-db
```

---

## 20.3 Cloud Run Environment Variables

For Cloud Run:

```env
DB_USER=postgres
DB_PASSWORD=...
DB_NAME=scanx_app
DB_PORT=5432
INSTANCE_CONNECTION_NAME=vernal-maker-473121-k4:us-central1:scanx-postgres-db
```

Do not use local proxy values in Cloud Run.

---

## 20.4 Cloud Run WebSocket Note

For Phase 1, if WebSockets are used in-memory, keep Cloud Run max instances low, ideally:

```bash
gcloud run services update scanx-web-dialer-backend --region us-central1 --max-instances 1
```

Future scalable approach:

```text
Google Pub/Sub / Redis Pub/Sub
        ↓
WebSocket broadcaster
```

---

# 21. Known Limitations

## 21.1 WebSocket In-Memory State

Current WebSocket clients are stored in process memory.

This works for a single backend instance.

It does not work reliably across multiple Cloud Run instances.

## 21.2 Incoming Missed Call Tracking Requires Twilio Path

The backend can only know incoming missed calls if Twilio receives and controls the incoming call.

If the current company number forwards outside Twilio, this backend cannot detect missed calls unless that provider exposes webhooks.

## 21.3 Phone Matching Is Basic

Phone matching uses simple normalization.

Future improvement:

```text
python-phonenumbers
```

## 21.4 No Authentication Yet

Currently, APIs are not protected by login.

Production must add authentication before public use.

## 21.5 Google Chat Webhook Placeholder

Google Chat notification is implemented as a placeholder and will work once webhook URL is provided.

---

# 22. Production Hardening TODO

Before production:

1. Add authentication.
2. Add role-based access control.
3. Add Twilio webhook signature validation.
4. Add Secret Manager for secrets.
5. Restrict CORS.
6. Remove or disable `/dev/broadcast-test`.
7. Protect `/docs` if needed.
8. Add structured logs.
9. Add PHI-safe logging rules.
10. Add rate limiting.
11. Add monitoring and alerts.
12. Add WebSocket scaling strategy.
13. Add stricter phone validation.
14. Confirm incoming call provider path.
15. Confirm Twilio number configuration.
16. Confirm Google Chat webhook.

---

# 23. Development Roadmap

## Phase 1

Backend foundation:

* Patient search.
* Call history.
* Recent/missed calls.
* Twilio token.
* Outgoing call.
* Incoming forwarding placeholder.
* Status callback.
* Missed-call notification placeholder.
* WebSocket updates.

Frontend will be built next.

## Phase 2

Frontend:

* Dialer UI.
* Virtual keypad.
* Patient search UI.
* Recent calls UI.
* Missed calls UI.
* Patient call history UI.
* WebSocket client.
* Twilio Voice SDK integration.

## Phase 3

Incoming call improvement:

* Confirm Twilio incoming number behavior.
* Preserve forwarding.
* Improve missed-call detection.
* Google Chat alert testing.

## Phase 4

Dormant IVR preparation:

* IVR service module.
* Existing patient detection.
* Unknown caller detection.
* Sales agent routing placeholder.

## Phase 5

Production hardening:

* Auth.
* RBAC.
* Secret Manager.
* Signature validation.
* Monitoring.
* Scaling.

---

# 24. Summary

The ScanX Web Dialer Backend is the foundation for a web-based calling and call monitoring application.

It connects:

```text
Frontend Dialer
        ↓
FastAPI Backend
        ↓
Cloud SQL PostgreSQL
        ↓
Twilio Voice
        ↓
Google Chat Notifications
        ↓
WebSocket Dashboard
```

It currently supports the core Phase 1 backend features:

* Patient search.
* Known/unknown caller matching.
* Call history.
* Recent calls.
* Missed calls.
* Twilio voice token generation.
* Outgoing call TwiML.
* Incoming forwarding placeholder.
* Twilio status callback handling.
* Missed call Google Chat notification placeholder.
* WebSocket live updates.

The next major step is to build the React frontend and connect it to these backend APIs.
