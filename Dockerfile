# Use a slim Python base image
FROM python:3.11-slim

# Use nonroot user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Install dependencies
COPY --chown=appuser:appuser requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . .

# Expose inference port
EXPOSE 8000

# Run app
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
