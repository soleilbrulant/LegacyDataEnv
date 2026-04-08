# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the environment files
COPY . .

# The environment needs to be importable, no default CMD is strictly required for OpenEnv base images,
# but we set a fallback to keep the container alive if tested manually.
CMD ["tail", "-f", "/dev/null"]