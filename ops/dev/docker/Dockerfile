FROM python:3.13

# Add Google Cloud SDK apt repository
RUN curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
    | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    > /etc/apt/sources.list.d/google-cloud-sdk.list

# Install Google Cloud SDK
RUN apt-get update && apt-get install -y --no-install-recommends \
    jq \
    google-cloud-cli \
    google-cloud-cli-app-engine-python \
    google-cloud-cli-app-engine-python-extras \
    google-cloud-cli-datastore-emulator \
    && rm -rf /var/lib/apt/lists/*
ENV HTTPLIB2_CA_CERTS="/usr/lib/google-cloud-sdk/platform/google_appengine/lib/httplib2/httplib2/cacerts.txt"

# Install legacy-cgi (removed in Python 3.13, but required by dev_appserver.py)
RUN pip install --no-cache-dir legacy-cgi

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /tba

# Expose GAE admin + module ports
EXPOSE 8000
EXPOSE 8080-8088

ENTRYPOINT ["./ops/dev/scripts/dev_appserver.sh"]
