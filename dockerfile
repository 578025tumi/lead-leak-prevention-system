# Stage 1: Build the Python application and install dependencies
FROM python:3.12-slim-bookworm AS builder

# Set working directory inside the builder container
WORKDIR /app

# Ensure pip is up-to-date and install build essentials (if any dependencies need compiling)
# We don't strictly need build-essential for FastAPI/Uvicorn, but it's good practice
# if you expect packages with C extensions (like psycopg2, numpy, etc.)
RUN pip install --no-cache-dir --upgrade pip

# Copy dependency file
COPY requirements.txt .

# Install Python dependencies into the builder's environment
# pip installs executables (like 'uvicorn') into the bin/Scripts directory
# within the Python installation (e.g., /usr/local/bin)
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Create the final lean image for runtime
FROM python:3.12-slim-bookworm

# Set working directory for the final container
WORKDIR /app

# Copy only the necessary installed Python packages from the builder stage
# This copies everything from the python site-packages (where actual libraries are)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# CRUCIAL: Copy the Python executables/scripts from the builder's bin directory
# This ensures 'uvicorn' (and any other scripts installed by pip) is in the PATH
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application source code
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the application using Uvicorn
# 'uvicorn' should now be found in /usr/local/bin
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]