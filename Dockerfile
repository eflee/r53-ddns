FROM python:3.11-slim

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash ddns

WORKDIR /usr/src/app

# Copy and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ddns.py ./

# Set ownership
RUN chown -R ddns:ddns /usr/src/app

# Switch to non-root user
USER ddns

# Add health check (checks if script can run)
HEALTHCHECK --interval=5m --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import ddns; import boto3" || exit 1

# Run the script
CMD ["python", "./ddns.py"]