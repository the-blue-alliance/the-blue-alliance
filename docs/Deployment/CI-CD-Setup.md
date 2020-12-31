## Configure Secrets

Under your repository Settings > Secrets on GitHub, set the following secrets:

- `FIREBASE_API_KEY`: The API key from a Firebase config for a web project.

  You can find this key by going to your [Firebase Project](https://console.firebase.google.com/) Settings -> General -> Your project -> Web API Key.

- `FIREBASE_APP_ID`: The App ID for a Firebase web project.

  You can find this key by going to your [Firebase Project](https://console.firebase.google.com/) Settings -> General -> Your apps -> App ID

  If an app does not already exist, click "Add app" and setup a Web app.

- `FIREBASE_MESSAGING_SENDER_ID`: The App ID for a Firebase web project.

  You can find this key by going to your [Firebase Project](https://console.firebase.google.com/) Settings -> Cloud Messaging -> Project credentials -> Sender ID

- `GCLOUD_PROJECT_ID`: Google Cloud Project ID

  You can find this by going to your [Google Cloud Platform Dashboard](https://console.cloud.google.com/home/dashboard).

- `GCLOUD_AUTH`: Base64-encoded string representation of your service account JSON key

  e.g. `cat my-key.json | base64`

  More info on [creating and managing service account keys](https://cloud.google.com/iam/docs/creating-managing-service-account-keys).


- `REDIS_CACHE_URL`: A url pointing to a redis instance running in [Cloud Memorystore](https://cloud.google.com/memorystore).

  You'll need to have created an instance and VPC Network Connector (see the [[Prod Setup Guide|Prod-Setup]]). The redis URL will look something like: `redis://<REDIS IP>:<REDIS PORT>`.

- `VPC_CONNECTOR_NAME`: This is the name of the [VPC Access Connector](https://cloud.google.com/appengine/docs/standard/python/connecting-vpc) that allows App Engine to connect to the redis instance.

  This will be of the format `projects/<PROJECT_ID>/locations/<REGION>/connectors/<CONNECTOR_NAME>`
