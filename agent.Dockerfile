# Base Image for OMC Lab Agents
# Strict dependency list: scikit-learn, xgboost, pandas, numpy, matplotlib, ta-lib, shap

FROM python:3.11-slim

# Install system dependencies for TA-Lib and others
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib/ ta-lib-0.4.0-src.tar.gz

# Install Python dependencies
RUN pip install --no-cache-dir \
    scikit-learn \
    xgboost \
    pandas \
    numpy \
    matplotlib \
    ta-lib \
    shap \
    pyarrow

# Create workspace directory
WORKDIR /workspace

# Create output directory for artifacts
RUN mkdir -p /workspace/out

# Default command (can be overridden by Dagger)
CMD ["python3"]
