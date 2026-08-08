# --- Stage 1: Builder ---
FROM python:3.13-slim AS builder

# Set the working directory
WORKDIR /app

# Install uv (our blazing fast package manager)
RUN pip install uv

# Copy only the dependency file first (to cache this layer)
COPY pyproject.toml .

# Create a virtual environment and install production dependencies
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv -r pyproject.toml

# --- Stage 2: Final Production Image ---
FROM python:3.13-slim

# Prevent Python from writing .pyc files to disk and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Add the virtual environment to the system PATH
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy the dependencies from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the actual application code and database migration files
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]