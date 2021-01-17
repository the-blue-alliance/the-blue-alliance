The Blue Alliance is hosted on [Google's App Engine platform](https://cloud.google.com/appengine) and leverages several Google technologies. Both the website and mobile applications leverage [Google's Firebase](https://firebase.google.com/) and Firebase technologies. **It is not necessary for a contributor to setup an upstream Google App Engine instance or Firebase project in order to work on The Blue Alliance's codebase.** Most technologies have local alternatives or workarounds to allow a completely local development experience.

A Google App Engine instance or a Firebase project can be setup without needing to setup the other one. It is not necessary to setup both. Only setting up the bits and pieces needed to test a feature or code is the suggested route, as attempting to replicate the EXACT state of production is near impossible.

This is not meant to be a step-by-step guide to reproduce a production environment. It is a collection of notes for contributors who either have or need an upstream Google App Engine instance or Firebase project to refer to when other contributors add or make changes to upstream configurations. These notes may be incomplete or missing information about a specific technology.

These notes are offered as-is and without support. Since deploying and testing against upstream Google technologies should not be necessary for the average contributor, getting help with cryptic Google error messages is outside the scope of what is expected from other contributors.

As a final note - **you may incur charges when deploying code to an upstream Google App Engine instance.** The Blue Alliance makes use of several Google technologies which require billing to be enabled for a project, and the codebase does not work to optimize staying in the free tier for these technologies. Be careful when developing/testing with an upstream Google App Engine instance.

# Google App Engine Setup

1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) locally.

2. Follow the [Setting up your Google Cloud project for App Engine](https://cloud.google.com/appengine/docs/standard/python3/console) to create a new project in Google App Engine.

3. Set your default `gcloud` project to the name of your newly created project.

```bash
$ gcloud config set project {project-name}
```

## Deploying

[NOTE: These steps should move to the `Manual Deployment` page and should go in to more detail. They're here now as a stop-gap.]

The [`push.yml` GitHub Action](https://github.com/the-blue-alliance/the-blue-alliance/blob/py3/.github/workflows/push.yml) contains the commands CI uses to deploy to production and can be used as a reference.

1. Deploy the default service and any other necessary services for testing.

```bash
$ gcloud app deploy src/default.yaml -v 1
$ gcloud app deploy src/{service}.yaml -v 1
```

2. (Optional) Deploy `dispatch.yaml` for routing

```bash
$ gcloud app deploy src/dispatch.yaml
```

`dispatch.yaml` will fail to deploy if not all services defined in `dispatch.yaml` are deployed upstream. The best workaround here is to modify `dispatch.yaml` locally to remove services not deployed upstream and then attempt to re-deploy `dispatch.yaml` with only the necessary routes.

[TODO: Notes on deploying `cron.yaml`]

## Configuring Flask Secrets

The [`SECRET_KEY`](https://flask.palletsprojects.com/en/1.1.x/config/#SECRET_KEY) for Flask apps is in the `flask.secrets` sitevar and configured for Flask apps during runtime. The default `secret_key` value must be changed when deploying to an upstream Google App Engine instance - there is validation in place to ensure the default key checked in to code/used for development is not the same key used in production. At the time of writing, the Admin interface is not supported in the py3 codebase, so there is no GUI for editing sitevars. Sitevars can be edited directly [in the Datastore interface](https://console.cloud.google.com/datastore/entities;kind=Sitevar) online when selecing `Sitevar` from the `Kind` dropdown, editing the `flask.secrets`, and updating the JSON accordingly.

## Task Queues

The `deploy_queues.py` script can be run to create/update queues via the `gcloud` command based on the `queue.yaml` configuration.

```bash
$ python3 ops/deploy/deploy_queues.py src/queue.yaml
```

Queues can be created in Google App Engine [using the gcloud command](https://cloud.google.com/tasks/docs/creating-queues). The linked document should be the source of truth for creating queues.

## Memorystore (redis)

Roughly, the setup is outlined in [this page](https://cloud.google.com/appengine/docs/standard/python/migrate-to-python3/migrate-to-cloud-ndb#caching). We need the following steps:
 1. Create a [VPC Network](https://cloud.google.com/vpc/docs/vpc)
 2. Create a [VPC Access Connector](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access#creating_a_connector)
 3. Create a [Redis Instance](https://cloud.google.com/memorystore/docs/redis/creating-managing-instances#creating_redis_instances) using the network
 4. Make note of the `REDIS_CACHE_URL` and VPC Connector name to set as deploy secrets, or locally in the `env_variables` and `vpc_access_connector` section of [a service's yaml configuration](https://cloud.google.com/appengine/docs/standard/python3/config/appref) when deploying.

# Firebase Setup

1. Navigate to the [Firebase Console](https://console.firebase.google.com/)
2. Click `Add Project`
3. Enter a project name to work with - preferably something namespace'd to yourself (ex: `tba-dev-zach`)
4. Finish setting up your project. You should be redirected to the project's overview page. If not, you can access the project's overview by clicking on the project in the [Firebase Console](https://console.firebase.google.com/).
5. On the overview page, start the flow to setup a new Web app to your project. This can also be found in Gear -> Project Settings -> General -> Your apps and clicking Web.
6. Enter any required information for your app and click `Register App`

## Configure Development Container

### Setup Firebase Keys

After setting up your app, you should see a set of keys. It's only necessary to setup the configuration keys locally. Keys are referenced from a `tba_keys.js` file. This file is not checked in to source control, but a template of the file is. You can copy the template and add your own keys to the file.

```
$ cp src/backend/web/static/javascript/tba_js/tba_keys_template.js src/backend/web/static/javascript/tba_js/tba_keys.js
```

Edit the fields specified in the file and save. If you're using the development container, make sure to sync this file to the container. Finally, [rebuild web resources](https://github.com/the-blue-alliance/the-blue-alliance/wiki/Development-Runbook#rebuilding-web-resources-javascript-css-etc) to compile the secrets file with the Javascript.

### Setup Google Service Account Keys

Download a [Firebase service account key](https://firebase.google.com/docs/admin/setup#initialize-sdk) for your project from the Firebase console via Settings -> Service accounts. Move the downloaded key to the `ops/dev/keys/` folder.

Set the [[`google_application_credentials` of the `tba_config.json`/`tba_config.local.json`|tba-dev-config]] to the path of your downloaded key.

```json
{
    ...
    "google_application_credentials": "ops/dev/keys/my-key.json",
    ...
}
```

If you're using the development container, make sure to sync your key file to the container. A [restart or reprovision of the development container](https://github.com/the-blue-alliance/the-blue-alliance/wiki/Development-Runbook#reprovisioning-the-development-container) might be necessary in order to sync files + restart `dev_appserver.py`. Otherwise, you can kill + restart the `dev_appserver.sh` script in the tmux session manually.

```bash
$ ./ops/dev/vagrant/dev_appserver.sh
```

## Configure a Google App Engine instance

If your Firebase project is connected to your Google App Engine instance, there is very little setup necessary. Follow the instructions above for [setting up your Firebase keys in `tba_keys.js`](https://github.com/the-blue-alliance/the-blue-alliance/wiki/GAE-Firebase-Setup#setup-firebase-keys), [rebuild web resources](https://github.com/the-blue-alliance/the-blue-alliance/wiki/Development-Runbook#rebuilding-web-resources-javascript-css-etc) to compile the secrets file with the Javascript, and [re-deploy the necessary services](https://github.com/the-blue-alliance/the-blue-alliance/wiki/GAE-Firebase-Setup#deploying).

Additional configuration might be necessary for Firebase technologies. Those details will be available in the sections for those technologies.

## Authentication

1. In your Firebase project, select "Authentication" from the left bar (in the "Build" section).
2. Click the "Sign-in method" tab.
3. Under the "Sign-in providers" section, click the Google dropdown and toggle the "Enable" switch to be enabled.
4. Click the "Save" button.

When navigating your local project, make sure to use the `http://localhost:8080` domain, as `localhost` is the only local domain specified in the `Authorized domains` section. Otherwise, add `0.0.0.0` in the `Authorized domains` section.

Other authentication providers can be setup, if necessary. Currently, The Blue Alliance only supports Google and Apple as authentication providers.

### (Optional) Additional Configuration

Additional steps to replicate The Blue Alliance's Firebase configuration in your own Firebase project. These steps are included for completeness and for any situational use cases, but will not be necessary for most contributors.

#### Configure Authorized Domains

In Firebase, production domains should be included in the Develop -> Authentication -> Sign In Method -> Authorized domains section. Additionally if the Firebase API key has restricted permissions, the `{project_id}.firebaseapp.com` redirect domain must be included as a valid HTTP referrer for the API key. This can be configured in Google Cloud Platform Console when navigating to API & Services -> Credentials -> API Keys -> editing the API key in question and adding the `{project_id}.firebaseapp.com` domain under the `Website restrictions` section. If the Firebase API key is not restricted, this step is not required.

#### Sign in with Apple

In order to setup Sign in with Apple, follow the [Firebase Authenticate Using Apple with JavaScript](https://firebase.google.com/docs/auth/web/apple) guide. Sign In with Apple can only be configured by members of the [Apple Developer Program](https://developer.apple.com/programs/).

For testing, it is recommended to just test with a Google account, since features should be provider-agnostic, and Firebase manages pulling the necessary information from provider's accounts and wrapping them as Firebase users.
