Run an App Engine Server
------------------------
See [myTBA Configuration](https://github.com/the-blue-alliance/the-blue-alliance-android/wiki/myTBA-Configuration) for how to create and configure an App Engine server.

Setup notes:

* You _could_ edit the `app.yaml` file to change its `application:` setting from `tbatv-dev-hrd` to your app's Project ID, but then you'll have to remember to not check in that edit. Better yet, write a script like the following `mydeploy.sh` file (that filename is in `.gitignore`):

        #!/bin/sh
        appcfg.py --oauth2 --application=<MY_PROJECT_ID> update app.yaml app-backend-tasks.yaml
        appcfg.py --oauth2 --application=<MY_PROJECT_ID> update_dispatch .

* Note that it needs your application's "Project ID", not its "Project name".
* Make sure you run `paver install_libs` so that all of your dependencies are there
* The `--oauth2` argument of `appcfg.py` [saves repeating the login steps each time](https://cloud.google.com/appengine/docs/python/tools/uploadinganapp#Python_Password-less_login_with_OAuth2). If you skip it or deploy via the App Engine Launcher, you'll have to enter your name and password each time. If you use 2-Step Verification for your Google account (you should!), that means generating an [App password](https://security.google.com/settings/security/apppasswords) each time.
* The `cron.yaml` file in master will create cron jobs that use up daily free AE Datastore quotas.
  * To avoid that in a dev server, checkout [a no-op version of cron.yaml](https://github.com/the-blue-alliance/the-blue-alliance/blob/c5d173f23310caf9f2c80d08829083c22ea1c0c3/cron.yaml).
  * If it's already happening in a dev server, deploy a no-op `cron.yaml` via `appcfg.py update_cron`, then delete the tasks in the `usfirst` queue.)
  * If you try to deploy a server while it's over Datastore quota, appcfg will say "there was an error updating your indexes. Please retry later with appcfg.py update_indexes." The fix is to wait until the next day's quota then use `appcfg.py update_indexes` or `appcfg.py update`.
* When you set sitevars, the server automatically internalizes them.
* You don't need a sitevar for `firebase.secrets` even though that's the placeholder text for a new sitevar name.
* Ignore these deployment warnings:
  * `Cannot upload both <filename>.py and <filename>.pyc`
  * `Could not guess mimetype for static/ovp/<filename>.xap.  Using application/octet-stream.`
  * `WARNING old_run.py:88 This function, oauth2client.tools.run(), and the use of the gflags library are deprecated and will be removed in a future version of the library.`
* Ignore these warnings in a deployed server's logs:
  * `Exception: Missing sitevar: firebase.secrets. Can't write to Firebase` (It just means that no push notifications to GameDay will be sent, which is OK for a dev server.)
* Make sure `static/javascript/tba_js/tba_keys.js` exists


