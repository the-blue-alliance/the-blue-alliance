FROM google/cloud-sdk:latest

# Install App Engine components and jq (for config parsing)
RUN apt-get update && apt-get install -y jq \
    && gcloud components install \
        app-engine-python \
        app-engine-python-extras \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv for generating requirements.txt
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV HTTPLIB2_CA_CERTS="/usr/lib/google-cloud-sdk/platform/google_appengine/lib/httplib2/httplib2/cacerts.txt"

WORKDIR /tba

# Expose GAE admin + module ports
EXPOSE 8000
EXPOSE 8080-8088

ENTRYPOINT ["./ops/dev/scripts/dev_appserver.sh"]
