FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
        build-essential \
        apt-utils \
        curl \
        ffmpeg \
        sox \
        libcairo2-dev \
        libpango1.0-dev\
        # not enough money to run texlive for resources :D
        # texlive-full \
        # texlive-fonts-extra \
        # texlive-latex-extra \
        # texlive-latex-recommended \
        # texlive-science \
        tipa \
    && rm -rf /var/lib/apt/lists/*
# Install uv
RUN curl -LsSf https://github.com/astral-sh/uv/releases/download/0.1.24/uv-installer.sh | sh && \
    mv /root/.cargo/bin/uv /usr/local/bin/ && \
    chmod +x /usr/local/bin/uv

RUN adduser appuser
RUN echo "appuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER appuser

# Set working directory
WORKDIR /home/appuser

# Copy requirements first for better caching
COPY --chown=appuser:appuser requirements.txt .

# Create and activate virtual environment, then install dependencies
RUN uv venv venv
ENV VIRTUAL_ENV=/home/appuser/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies using uv in the virtual environment
RUN uv pip install -r requirements.txt && rm -rf ~/.cache/pip

# Create important directories
RUN mkdir code_files animations
RUN chown -R appuser:appuser code_files animations

# Copy application code
COPY --chown=appuser:appuser . .
COPY --chown=appuser:appuser run.sh ./

RUN chmod +x run.sh

# Expose Streamlit port
EXPOSE 8000

# Run Streamlit app
ENTRYPOINT ["./run.sh"]