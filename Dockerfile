# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the environment files
COPY . .

# Install the package itself in editable mode so imports resolve correctly
RUN pip install --no-cache-dir -e .

# Expose the port the validator will probe
EXPOSE 7860

# Bug Fix: Run the actual server (not tail -f /dev/null)
# The validator probes /health, /reset, /step, /schema endpoints
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]