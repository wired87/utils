def d_content():
    return"""
FROM python:3.10

# Set working directory
WORKDIR /app

# Create virtual environment
RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files
COPY . .

# Set the entry point to run the service
CMD ["python", "deploy_model.py"]

"""