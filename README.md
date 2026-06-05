# ScanX Web Dialer Backend

## 1. Overview

The **ScanX Web Dialer Backend** is a FastAPI service used by the ScanX Web Dialer frontend.

It handles:

* Patient search
* Patient call history
* Recent calls
* Missed calls
* Dashboard summary
* Twilio Voice token generation
* Outgoing Twilio call handling
* Incoming call forwarding placeholder
* Twilio status callback handling
* Call logging
* WebSocket live updates
* Google Chat missed-call notification placeholder
* Unknown caller handling
* Call notes
* Call dispositions

The backend connects to **Cloud SQL PostgreSQL** and is deployed to **Google Cloud Run**.

---

## 2. Tech Stack

| Area              | Technology                |
| ----------------- | ------------------------- |
| Framework         | FastAPI                   |
| Runtime server    | Uvicorn                   |
| WebSocket support | uvicorn[standard]         |
| Database          | Cloud SQL PostgreSQL      |
| DB library        | SQLAlchemy                |
| PostgreSQL driver | psycopg2-binary           |
| Voice provider    | Twilio Programmable Voice |
| Realtime          | FastAPI WebSockets        |
| Notifications     | Google Chat Webhook       |
| Deployment        | Google Cloud Run          |

---

## 3. Project Structure

```text
web_dailer_backend/

├── app.py
├── config.py
├── database.py
├── requirements.txt
├── Procfile
├── .env
├── .env.example
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
│   ├── dashboard.py
│   └── dev.py
│
├── services/
│   ├── __init__.py
│   ├── patient_service.py
│   ├── call_service.py
│   ├── dashboard_service.py
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

## 4. Environment Variables

## Local `.env`

```env
APP_NAME=ScanX Web Dialer Backend
APP_ENV=local
BASE_URL=http://localhost:5000

API_SECRET=change-this-secret
ENABLE_IVR=false

DB_USER=postgres
DB_PASSWORD=your_database_password
DB_NAME=scanx_app
DB_HOST=127.0.0.1
DB_PORT=5432
INSTANCE_CONNECTION_NAME=

TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_API_KEY_SID=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_KEY_SECRET=your_twilio_api_key_secret
TWILIO_TWIML_APP_SID=APxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX

CLIENT_FORWARD_NUMBER=+1XXXXXXXXXX

ENABLE_GCHAT_MISSED_CALL_ALERTS=true
GCHAT_MISSED_CALL_WEBHOOK_URL=
```

## Cloud Run Environment Variables

```env
APP_NAME=ScanX Web Dialer Backend
APP_ENV=production
BASE_URL=https://YOUR_BACKEND_CLOUD_RUN_URL

API_SECRET=change-this-secret
ENABLE_IVR=false

DB_USER=postgres
DB_PASSWORD=your_database_password
DB_NAME=scanx_app
DB_PORT=5432
INSTANCE_CONNECTION_NAME=vernal-maker-473121-k4:us-central1:scanx-postgres-db

TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_API_KEY_SID=SKxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_API_KEY_SECRET=your_twilio_api_key_secret
TWILIO_TWIML_APP_SID=APxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX

CLIENT_FORWARD_NUMBER=+1XXXXXXXXXX

ENABLE_GCHAT_MISSED_CALL_ALERTS=true
GCHAT_MISSED_CALL_WEBHOOK_URL=
```

---

## 5. File Details

## `app.py`

Main FastAPI entry point.

Responsibilities:

* Create FastAPI app
* Configure CORS
* Register routers
* Expose root endpoint

Registered routers:

```python
app.include_router(health_router)
app.include_router(patients_router)
app.include_router(calls_router)
app.include_router(websocket_router)
app.include_router(notifications_router)
app.include_router(dev_router)
app.include_router(voice_router)
app.include_router(dashboard_router)
```

Root endpoint:

```text
GET /
```

Returns:

```json
{
  "service": "ScanX Web Dialer Backend",
  "status": "running"
}
```

---

## `config.py`

Loads all environment variables.

Configuration groups:

* App config
* Security config
* Database config
* Twilio config
* Incoming forwarding config
* Google Chat config

Important production value:

```env
INSTANCE_CONNECTION_NAME=vernal-maker-473121-k4:us-central1:scanx-postgres-db
```

Important local value:

```env
INSTANCE_CONNECTION_NAME=
```

---

## `database.py`

Creates SQLAlchemy database connection.

Responsibilities:

* Build PostgreSQL database URL
* Support local TCP DB connection
* Support Cloud Run `/cloudsql/...` connection
* Create SQLAlchemy engine
* Create `SessionLocal`
* Provide `test_db_connection()`

Used by:

```text
GET /health/db
```

---

## `requirements.txt`

Required packages:

```txt
fastapi
uvicorn[standard]
python-dotenv
sqlalchemy
psycopg2-binary
twilio
python-multipart
httpx
pydantic
```

Important:

`uvicorn[standard]` is required for WebSocket support.

---

## `Procfile`

Used by Cloud Run source deployment.

```Procfile
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

---

## `.gcloudignore`

Recommended content:

```gitignore
.env
venv/
env/
__pycache__/
*.pyc
.git/
.pytest_cache/
.DS_Store
```

---

# 6. Routes

## `routes/health.py`

Endpoints:

```text
GET /health
GET /health/db
```

Purpose:

* Verify backend is running.
* Verify database connection.

---

## `routes/patients.py`

Endpoints:

```text
GET /patients/search
GET /patients/lookup-by-phone
GET /patients/call-history
```

Purpose:

* Search patients.
* Match caller by phone number.
* Fetch patient call history.

Patient search uses the existing `appointment` table.

---

## `routes/calls.py`

Endpoints:

```text
GET /calls/recent
GET /calls/missed
GET /calls/{call_id}
POST /calls/{call_id}/notes
POST /calls/{call_id}/disposition
```

Purpose:

* Fetch recent calls.
* Fetch missed calls.
* Fetch one call detail.
* Add call note.
* Add call disposition.

---

## `routes/dashboard.py`

Endpoint:

```text
GET /dashboard/summary
```

Optional query parameters:

```text
start_date=YYYY-MM-DD
end_date=YYYY-MM-DD
```

Purpose:

* Return business-friendly dashboard summary.
* Support today, single-day, and date-range filters.

Returns:

* Total calls
* Outgoing calls
* Incoming calls
* Missed calls
* Completed calls
* Failed / busy calls
* No-answer calls
* Average call duration
* Recent calls
* Missed calls list

---

## `routes/voice.py`

Endpoints:

```text
GET /voice/token
POST /voice/outgoing
POST /voice/incoming
POST /voice/status
```

Purpose:

* Generate Twilio Voice SDK browser token.
* Handle outgoing browser call TwiML.
* Preserve incoming forwarding behavior.
* Receive Twilio status callbacks.

---

## `routes/websocket.py`

Endpoints:

```text
WS /ws/calls
GET /ws/status
```

Purpose:

* Maintain live frontend connection.
* Broadcast call status updates.
* Show connection status.

---

## `routes/notifications.py`

Endpoint:

```text
POST /notifications/test-gchat
```

Purpose:

* Test Google Chat missed-call webhook.

---

## `routes/dev.py`

Endpoint:

```text
POST /dev/broadcast-test
```

Purpose:

* Development-only WebSocket broadcast testing.

Production note:

Protect or remove this route before production release.

---

# 7. Services

## `services/patient_service.py`

Main functions:

```python
search_patients(query, limit)
find_patient_by_phone(phone)
get_patient_call_history_by_phone(phone, limit)
```

Purpose:

* Search appointment records.
* Match phone numbers.
* Return patient call history.

---

## `services/call_service.py`

Main functions:

```python
create_call_log()
update_call_log_status()
get_call_log_by_sid()
create_call_event()
get_recent_calls()
get_missed_calls()
get_call_by_id()
add_call_note()
add_call_disposition()
```

Important rule:

```text
One row in call_logs = one row in UI.
```

Uses `LEFT JOIN LATERAL` to attach only one best appointment match per call.

Matching priority:

1. Exact `appointment_id`
2. Latest appointment with same phone number
3. Unknown Caller if no match

---

## `services/dashboard_service.py`

Main function:

```python
get_dashboard_summary(start_date=None, end_date=None)
```

Purpose:

* Calculate dashboard metrics.
* Fetch recent calls.
* Fetch missed calls.
* Avoid duplicated appointment joins.
* Show unknown callers when no patient is matched.

---

## `services/twilio_service.py`

Main functions:

```python
generate_voice_token(identity)
build_outgoing_call_twiml(to_number)
build_current_forwarding_twiml()
```

Purpose:

* Generate Twilio Voice SDK token.
* Generate outgoing call TwiML.
* Generate incoming forwarding TwiML.

---

## `services/websocket_manager.py`

Purpose:

* Store active WebSocket clients.
* Broadcast events to frontend.
* Track connection metadata.

Current storage is in-memory.

For multi-instance Cloud Run scaling, use Redis Pub/Sub or Google Pub/Sub.

---

## `services/notification_service.py`

Main functions:

```python
build_missed_call_message()
send_gchat_missed_call_alert()
log_notification_result()
```

Purpose:

* Build Google Chat missed-call alert.
* Send alert if webhook is configured.
* Log notification result.

---

# 8. Utilities

## `utils/phone.py`

Functions:

```python
normalize_phone(phone)
phone_search_pattern(phone)
```

Purpose:

* Normalize phone numbers.
* Support phone matching.

---

## `utils/security.py`

Reserved for future security helpers.

Recommended future use:

* Twilio webhook signature validation.
* API key validation.
* Auth validation.
* Role checks.

---

# 9. Database Tables

## Existing Tables Used

### `appointment`

Used for patient lookup.

Important fields:

```text
appointment_id
first_name
last_name
phone
email
appointment_type
clinic_id
location
calendar
appointment_datetime
date
time
created_at
updated_at
```

### `clinics`

Used for clinic metadata.

### `call_logs`

Main call log table.

Important fields:

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

---

## Companion Tables

### `dialer_call_events`

Stores raw Twilio events.

### `dialer_call_notifications`

Stores Google Chat notification attempts.

### `dialer_call_notes`

Stores call notes.

### `dialer_call_dispositions`

Stores call outcomes.

### `dialer_ivr_config`

Stores dormant IVR configuration.

---

# 10. Data Flow

## Outgoing Call Flow

```text
Frontend user clicks Call
    ↓
Frontend requests /voice/token
    ↓
Twilio Device starts browser call
    ↓
Twilio calls /voice/outgoing
    ↓
Backend creates call_logs row
    ↓
Backend returns TwiML
    ↓
Twilio calls patient/number
    ↓
Twilio sends /voice/status callbacks
    ↓
Backend updates call_logs
```

---

## Status Callback Flow

```text
Twilio sends call status
    ↓
POST /voice/status
    ↓
Backend updates call_logs
    ↓
Backend creates dialer_call_events row
    ↓
Backend broadcasts WebSocket event
    ↓
If missed, backend triggers missed-call notification logic
```

---

## Dashboard Flow

```text
Frontend calls /dashboard/summary
    ↓
Backend reads call_logs
    ↓
Backend calculates counts
    ↓
Backend attaches best appointment match
    ↓
Frontend displays dashboard
```

---

## Unknown Caller Flow

```text
Staff calls unknown number
    ↓
Backend logs call
    ↓
No appointment match found
    ↓
display_name = Unknown Caller
    ↓
Frontend shows call in Recent Calls
```

---

# 11. Local Development

Create virtual environment:

```cmd
python -m venv venv
```

Activate:

```cmd
venv\Scripts\activate
```

Install requirements:

```cmd
pip install -r requirements.txt
```

Start Cloud SQL Auth Proxy:

```cmd
cloud-sql-proxy vernal-maker-473121-k4:us-central1:scanx-postgres-db --port 5432
```

Run backend:

```cmd
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

Test:

```text
http://localhost:5000/
http://localhost:5000/health
http://localhost:5000/health/db
http://localhost:5000/dashboard/summary
```

---

# 12. Twilio Setup

## TwiML App

Set Voice Request URL:

```text
https://YOUR_BACKEND_URL/voice/outgoing
```

Method:

```text
POST
```

## Status Callback

The backend uses:

```text
/voice/status
```

for Twilio call status updates.

## Incoming Webhook

If incoming call tracking is enabled:

```text
https://YOUR_BACKEND_URL/voice/incoming
```

Method:

```text
POST
```

---

# 13. Cloud Run Deployment

## Required Files

```text
app.py
config.py
database.py
requirements.txt
Procfile
.gcloudignore
routes/
services/
schemas/
utils/
```

## Deploy Command

Run from backend project root:

```cmd
gcloud run deploy scanx-web-dialer-backend --source . --region us-central1 --allow-unauthenticated --add-cloudsql-instances vernal-maker-473121-k4:us-central1:scanx-postgres-db
```

## Add Environment Variables

In Cloud Run:

```text
Cloud Run → scanx-web-dialer-backend → Edit & deploy new revision → Variables & Secrets
```

Add the production variables listed in this README.

## Test Deployment

```text
https://YOUR_BACKEND_CLOUD_RUN_URL/
https://YOUR_BACKEND_CLOUD_RUN_URL/health
https://YOUR_BACKEND_CLOUD_RUN_URL/health/db
https://YOUR_BACKEND_CLOUD_RUN_URL/dashboard/summary
```

Expected DB response:

```json
{
  "status": "ok",
  "database": "connected"
}
```

---

# 14. Production Notes

* Use Secret Manager for production secrets.
* Restrict CORS to frontend Cloud Run URL.
* Remove or protect `/dev/broadcast-test`.
* Add authentication.
* Add Twilio webhook signature validation.
* Keep `ENABLE_IVR=false` until IVR is approved.
* Use `uvicorn[standard]` for WebSockets.
* Use `wss://` for frontend WebSocket URL.
* Consider max instances = 1 for WebSocket MVP.
* For multi-instance WebSocket scaling, add Redis Pub/Sub or Google Pub/Sub.

---

# 15. Current Backend Capabilities

The backend currently supports:

* Patient search
* Patient lookup by phone
* Patient call history
* Recent calls
* Missed calls
* Dashboard summary
* Today, single-day, and date-range dashboard filtering
* Twilio Voice SDK token generation
* Outgoing browser call handling
* Incoming forwarding placeholder
* Twilio status callback handling
* Missed-call detection
* Google Chat missed-call notification placeholder
* WebSocket live updates
* Unknown caller handling
* Call notes
* Call dispositions
* Cloud SQL connection
* Cloud Run source deployment
