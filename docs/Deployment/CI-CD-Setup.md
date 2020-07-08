# CI/CD Setup

## Configure Secrets

Under your repository Settings > Secrets on GitHub, set the following secrets:

- `GCLOUD_PROJECT_ID`: Google Cloud Project ID
  You can find this by going to your [Google Cloud Platform Dashboard](https://console.cloud.google.com/home/dashboard).

- `GCLOUD_AUTH`: Base64-encoded string representation of your service account JSON key
  e.g. `cat my-key.json | base64`
  More info on [creating and managing service account keys](https://cloud.google.com/iam/docs/creating-managing-service-account-keys).
