def generate_dockerfile(**env_vars) -> str:
    # ENV-Blöcke erzeugen
    env_lines = []
    for k, v in env_vars.items():
        env_lines.append(f"    {k}={v}")

    env_block = "ENV PYTHONUNBUFFERED=1 \\\n" + " \\\n".join(env_lines)

    return f"""\
# Use a slim Python image
FROM python:3.10-slim AS base

# Set working directory
WORKDIR /usr/src/app

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libpq-dev && \\
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY r.txt ./
RUN pip install -r r.txt

# Copy rest of the project
COPY . .

# Set environment variables
ENV PYTHONPATH=/usr/src/app:$PYTHONPATH
{env_block}

# Copy startup script
COPY startup.sh .
RUN chmod +x startup.sh

# Expose port
EXPOSE 8080

# Start app
CMD ["./startup.sh"]
"""
