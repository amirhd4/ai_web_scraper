# ⚡ ai web scraper: Enterprise Distributed Scraper & Cron Orchestrator

An enterprise-grade, fully asynchronous web scraping engine and task scheduler built with **FastAPI**, **HTTPX**, and **APScheduler**. This system features real-time telemetry streaming via **WebSockets**, dynamic CSS selector extraction, and stateful deduplication management with a live monitoring dashboard.

---

## 🏗️ Architectural Highlights & Engineering Patterns

This portfolio project demonstrates advanced backend engineering principles and production-ready patterns:

* **Asynchronous I/O Engine:** Built purely on top of `asyncio` and `httpx`, utilizing token-based concurrency controls (`asyncio.Semaphore`) to mitigate rate-limiting and connection throttling.
* **Resilient Cron Orchestration:** Implements an `AsyncIOScheduler` hooked into FastAPI's `lifespan` state, preventing thread loss and ensuring guaranteed task execution even behind local hot-reloader processes (`WatchFiles`).
* **Stateful Deduplication & Dynamic Bypass:** Features an integrated Bloom-filter-inspired memory registry to skip previously visited URLs, coupled with a dynamic UI-controlled `ignore_visited` flag for on-demand crawling.
* **Real-time Event Streaming:** Uses an asynchronous `ConnectionManager` pattern to broadcast engine states, validation errors, and parsed payloads directly to connected clients over WebSockets.
* **Strict Type Validation:** Built using **Pydantic v2** core validators, executing robust data-integrity checks before payloads touch the storage layer.

---

## 📁 System Directory Structure

```text
scraper/
├── config.py           # Application environment configurations & timeouts
├── schemas.py          # Pydantic v2 core data models & API specifications
├── storage.py          # State management registry (visited cache & cron store)
├── worker.py           # Core Async Scraper Engine with BeautifulSoup4 parsing
├── scheduler.py        # APScheduler orchestration layer & cron triggers
├── main.py             # FastAPI routing, WebSocket pipeline & lifecycle management
└── static/
    └── index.html      # High-performance telemetry dashboard (TailwindCSS)
```

---

## 🛠️ Tech Stack & Dependencies

### Backend
* Python 3.12
* FastAPI
* Uvicorn
* Pydantic v2

### Scraping & AI Core
* Official Google GenAI SDK (`google-genai`)
* HTTPX (Async Client)
* BeautifulSoup4
* LXML Parser

### Automation & Storage
* APScheduler (AsyncIO Execution Cluster)
* Redis (Stateful Distributed Cache & Registry Store)

### Frontend Telemetry
* HTML5 / WebSockets API
* TailwindCSS v4
* Dynamic Reactive Dual-Language Engine (EN/FA)

---

## 🚀 Getting Started & Installation

### 1. Prerequisites
Ensure you have **Python 3.10+** and a running **Redis server** instance.

### 2. Clone Repository & Setup Virtual Environment
```bash
# Clone the repository
git clone [https://github.com/amirhd4/ai_web_scraper.git](https://github.com/amirhd4/ai_web_scraper.git)

# Enter project directory
cd ai_web_scraper

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate
```

### 3. Environment Configuration
Create a .env file in the root directory and append your configurations:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
GEMINI_API_KEY=your_api
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python main.py
```

The application will start at:

```text
http://localhost:8000
```

Open the address above in your browser to access the real-time monitoring dashboard.

---

## 📡 API Architecture Overview

### REST Endpoints

#### Create Immediate Scraping Task

```http
POST /api/v1/scrape/batch
```

Dispatches an instant distributed scraping workload to background workers.

---

#### Create Scheduled Cron Job

```http
POST /api/v1/cron
```

Registers a recurring automated scraping task.

---

#### List Active Cron Jobs

```http
GET /api/v1/cron
```

Returns all currently active cron schedules.

---

#### Delete Cron Job

```http
DELETE /api/v1/cron/{job_id}
```

Gracefully removes and terminates a scheduled task.

---

### WebSocket Pipeline

#### Real-Time Monitoring Channel

```http
WS /ws/monitor
```

Streams:

* Scraper execution events
* HTTP status responses
* Validation errors
* Parsing results
* Scheduler lifecycle events
* Network and runtime exceptions

directly to the dashboard in real time.

---

## 🔄 Request Lifecycle

```text
       Client Request (Payload via Dynamic UI Architecture)
                             │
                             ▼
                      FastAPI Endpoint
                             │
                             ▼
                    Pydantic Validation
                             │
                             ▼
                 Async Scheduler / Worker
                             │
         ┌───────────────────┴───────────────────┐
         ▼                                       ▼
 [Strategy: CSS]                          [Strategy: AI]
         │                                       │
         ▼                                       ▼
HTTPX Async Fetch                       HTTPX Async Fetch
         │                                       │
         ▼                                       ▼
BeautifulSoup Parsing                   BeautifulSoup Clean-up
         │                                       │
         ▼                                       ▼
Dynamic CSS Extract                      Official Google GenAI SDK
         │                               (Structured JSON Request)
         └───────────────────┬───────────────────┘
                             │
                             ▼
                    Deduplication Layer
                             │
                             ▼
                    WebSocket Telemetry
                             │
                             ▼
                        Dashboard UI
```

---

## 🛡️ Robust Error Handling

Unlike traditional scraping scripts, this engine isolates all network failures into structured telemetry events.

Handled scenarios include:

* SSL Handshake Failures
* DNS Resolution Errors
* Connection Timeouts
* Read Timeouts
* HTTP Redirect Loops
* 3xx Responses
* 4xx Client Errors
* 5xx Server Errors
* Parsing Failures

Instead of crashing worker processes, exceptions are converted into telemetry packets and streamed to the monitoring dashboard, ensuring scheduler stability and high availability.

---

## ⚙️ Performance Considerations

### Concurrency Control

The scraper uses:

```python
asyncio.Semaphore()
```

to limit simultaneous outbound requests and prevent:

* Server-side throttling
* Local socket exhaustion
* Connection pool saturation

### Memory Optimization

Visited URLs are maintained through an in-memory registry that prevents duplicate processing while keeping lookup complexity near O(1).

### Scheduler Reliability

By integrating APScheduler directly into FastAPI's lifecycle management, scheduled tasks remain synchronized with application startup and shutdown events.

---

## 🔒 Data Validation Strategy

All incoming API payloads are validated using **Pydantic v2** before execution.

Validation covers:

* URL format integrity
* CSS selector correctness
* Cron expression validity
* Request constraints
* Schema consistency

This guarantees predictable runtime behavior and reduces invalid task execution.

---

## 📈 Production-Ready Features

* **Dual-Extraction Runtime:** Seamless toggle between deterministic high-speed CSS Selectors and predictive natural language LLM parsing.
* **Official Google GenAI Integration:** Powered by the cutting-edge `google-genai` SDK using `types.GenerateContentConfig` for structured, safe JSON extraction.
* **Fully Asynchronous Architecture:** Zero-blocking I/O network operations optimized with `asyncio.to_thread` for background worker tasks.
* **Bilingual Telemetry Dashboard:** Completely reactive UI supporting real-time localization switching (English LTR / Persian RTL).
* **WebSocket Telemetry Streaming:** Live node monitoring streaming task states, parsed payloads, and server exceptions.
* **Stateful Distributed Cache:** Deduplication engine backed by Redis registry hashes to manage job idempotency.

---

## 📄 License

This project is licensed under the MIT License.

See the accompanying `LICENSE` file for details.
