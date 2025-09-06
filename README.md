# AI‑Powered Communication Assistant

This repository contains a production‑ready, full‑stack web application that implements an **AI‑Powered Communication Assistant**.  The assistant connects to your email account, extracts information from incoming messages (including attachments such as images, PDFs and audio), performs reasoning using Google’s Gemini models, retrieves relevant knowledge base entries and drafts contextual, empathetic responses.  It also provides analytics, notifications and a gamified coaching experience to help you improve over time.

## Features

**User Management**

- **Registration & Login** with role support (agent, admin).  Passwords are hashed with bcrypt and all forms include CSRF protection.
- **Email verification** is simulated by printing a verification link to the console – production deployments should integrate a real mail service.

**Email Retrieval & Threading**

- Connect to IMAP or Gmail via OAuth and fetch emails in the background using Celery workers.
- Messages are grouped by thread and filtered by subject keywords (support, query, request, help).  Attachments are securely saved.

**Multimodal Understanding**

- Attachments are processed with the appropriate modality:
  - **Images and screenshots** are sent to Gemini Pro Vision and the returned text is extracted.
  - **PDFs** are converted to images via `pdf2image` and then analysed with Gemini Pro Vision.
  - **Audio** files are transcribed locally using the open‑source Whisper model.
- OCR is performed with Tesseract via `pytesseract`.

**Information Extraction & RAG**

- Extract sender names, contact details, keywords, sentiment and urgency using the Gemini API coupled with regular expressions and heuristics.
- Integrate a knowledge base of FAQs and internal documentation.  KB entries are embedded with a sentence transformer and indexed with FAISS.  Top‑N snippets are retrieved to enrich Gemini prompts (retrieval‑augmented generation).

**Automated Drafting**

- Draft replies are generated via Gemini Pro using a structured prompt that incorporates thread history, extracted information, retrieved knowledge snippets, sentiment and urgency.  The AI returns both a reply and a justification along with a confidence score.
- A **trust meter** is computed based on Gemini confidence and heuristic scoring and displayed in the UI.
- Agents can edit the draft; their edits are stored as feedback for future fine‑tuning.

**Analytics & Coaching**

- A real‑time dashboard shows metrics such as total processed emails, average response time, distribution of sentiments and priority levels.
- A gamified coach suggests improvements to replies and assigns a “coach score.”
- Negative sentiment automatically triggers more empathetic and apologetic replies.
- A tone selector lets you choose between empathetic, formal, concise and cheerful replies.

**Notifications & Offline Mode**

- Urgent messages are prioritised; unresolved threads trigger Slack and email notifications after a configurable timeout.
- If the system is offline (e.g. no network), incoming messages are queued for later processing.  You can export and import the queue as JSON for offline batch processing.

**Accessibility & Internationalisation**

- Multilingual support for English and Hindi.  Users can switch the UI language from a dropdown on the dashboard.
- Text‑to‑speech is provided via `pyttsx3` so that drafts can be read aloud.

**Error Handling & Monitoring**

- Global error handlers return friendly error pages and log exceptions.
- A `/healthz` endpoint returns OK for health checks; `/metrics` exposes basic metrics for monitoring.

## Getting Started

### Prerequisites

- **Docker** and **Docker Compose** are required to run the full stack locally.
- You will need a **Google Gemini API key** (`GEMINI_API_KEY`) which you can obtain from [Google AI Studio](https://aistudio.google.com/).  Without an API key the assistant will not be able to call Gemini models.
- For PDF conversion you must have **Poppler** installed in the container.  The provided Dockerfile installs the necessary packages.
- To transcribe audio with Whisper you need the `whisper` Python package which in turn downloads the model when first executed.  Ensure the container has enough memory.

### Running the Demo

1. **Clone the repository**

   ```bash
   git clone <this‑repo>
   cd ai_comm_assistant
   ```

2. **Create a `.env` file** by copying the provided example and filling in the required secrets:

   ```bash
   cp .env.example .env
   # edit .env with your preferred editor
   ```

   At a minimum you must supply a `SECRET_KEY` and your `GEMINI_API_KEY`.  If you plan to connect to a real Gmail account set the IMAP credentials and OAuth tokens as needed.

3. **Build and run** the application with Docker Compose:

   ```bash
   docker‑compose up --build
   ```

   The web application will be available at **http://localhost:5000**.  The first run creates the database schema automatically.  A demo user (`agent@example.com` / `Password123!`) and an admin (`admin@example.com` / `Password123!`) are seeded for convenience.

4. **Access the dashboard** and connect your email account from the settings page.  The Celery worker fetches emails in the background and drafts responses automatically.  You can edit drafts, send them (SMTP simulation) and watch the analytics update in real time.

### Running Tests

To execute unit and integration tests run:

```bash
docker‑compose run --rm web pytest -q
```

This command runs the tests inside the container using the same environment as the application.  All tests should pass.

### Deployment

The repository includes a production‐ready configuration with Gunicorn.  See the `docker‑compose.yml` and `Dockerfile` for details.  To deploy to a VPS you can place Nginx in front of the container stack as a reverse proxy.  Refer to the comments in `nginx.conf` (not included) for guidance.

### Data Retention & Privacy

This project demonstrates how to build an AI‑powered assistant responsibly.  User data is stored in a PostgreSQL database and may include email contents and attachments.  The application supports data export and deletion.  For production use you must implement a data retention policy compliant with your organisation’s requirements.  Pseudonymisation functions are included as examples in `app/utils.py`.

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.