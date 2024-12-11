### README

# GEMINIAIAPP

This repository contains a **FastAPI-based application** for extracting, storing, and interacting with PDF content using AI-generated responses. It is built to handle PDF processing, AI-powered question answering, and robust database interactions.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [License](#license)

---

## Features

- Upload and process PDF files.
- Generate AI-based responses using **Google Generative AI**.
- Store and retrieve conversation history.
- Robust error handling and transaction management.
- Fully configurable with `.env` file.
- Logging support for debugging and monitoring.

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ZekDaniels/GeminiAIApp.git
   cd GeminiAIApp
   ```

2. Create a virtual environment and activate it:

   ```bash
   (Python 3.13.1)
   python -m venv venv
   source venv/bin/activate  # For Linux/Mac
   source venv/Scripts/activate     # For Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Apply database migrations:

   ```bash
   alembic upgrade head
   ```

5. Run the application:

   ```bash
   uvicorn app.main:app --reload
   ```

---

## Configuration

1. Create a `.env` file by copying the `.env.example`:

   ```bash
   cp .env.example .env
   ```

2. Update the following keys in your `.env` file:

   ```plaintext
   GEMINI_API_KEY=<your_google_ai_api_key>
   AI_MODEL_NAME=gemini-1.5-flash
   RETRY_ATTEMPTS=3
   TIMEOUT_SECONDS=10
   DATABASE_URL=sqlite+aiosqlite:///./pdf_chat.db
   UPLOAD_DIR=uploads/pdf_files
   MAX_FILE_SIZE_MB=20
   DEBUG=True
   LOG_LEVEL=INFO
   ```

3. Ensure the upload directory exists:

   ```bash
   mkdir -p uploads/pdf_files
   ```

---

## Usage

1. Access the interactive API documentation at:
   - **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

2. Key endpoints:
   - `POST /v1/integration/upload` - Upload a PDF file.
   - `GET /v1/integration/{id}` - Retrieve integration details.
   - `POST /v1/chat/chat_normal` - Generate an AI-powered response.

---

## Project Structure

```plaintext
.
├── .env                   # Configuration file
├── alembic                # Database migrations
├── app                    # Application core
│   ├── core               # Configuration and settings
│   ├── db                 # Database session setup
│   ├── decorators         # Common decorators
│   ├── errors             # Custom exceptions
│   ├── models             # ORM models
│   ├── routes             # API routes
│   ├── schemas            # Pydantic models for request/response
│   ├── services           # Business logic and utilities
│   ├── utils              # Helper utilities
├── logs                   # Application logs
├── uploads/pdf_files      # Directory for uploaded PDF files
├── tests                  # Test cases
```

---

## Development

1. Install additional dependencies for development:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the application with hot reload:

   ```bash
   uvicorn app.main:app --reload
   ```
---

## Testing

Run the test suite using `pytest`:

```bash
pytest
```
---

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

Feel free to contribute or raise issues in the repository for further enhancements.

