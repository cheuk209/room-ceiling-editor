# Custom Airflow image with UV pre-installed
FROM apache/airflow:2.8.1-python3.11

# Switch to root to install UV and dependencies
USER root

# Install UV (modern Python package installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

# Install Python dependencies using UV
# Copy requirements first for better Docker layer caching
COPY requirements.txt /tmp/requirements.txt
RUN uv pip install --system -r /tmp/requirements.txt

# Switch back to airflow user
USER airflow

# Set working directory
WORKDIR /opt/airflow
