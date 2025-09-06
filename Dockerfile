FROM python:3.10-slim

# Install system dependencies needed for Tesseract, Poppler (pdf2image) and Whisper
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        tesseract-ocr \
        libtesseract-dev \
        poppler-utils \
        ffmpeg \
        espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source code
COPY . .

# Expose port for the Flask app
EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--workers=4", "--bind", "0.0.0.0:5000", "wsgi:app"]