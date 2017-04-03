The Blue Alliance
==================
The Blue Alliance is a FIRST Robotics tool to help teams scout for, compete at, and relive competitions. You can see how the whole site works here, or even write code to make it better!

Help Build The Blue Alliance
------------

### Stay in Touch

* *Mailing List* Join [thebluealliance-developers on groups.google.com](https://groups.google.com/forum/#!forum/thebluealliance-developers) to stay up to date with development.
* *Slack* Ask to join [the-blue-alliance.slack.com](https://the-blue-alliance.slack.com) to hang out in our chat channels.

### Add Data
* *Facebook* Join our group, [#moardata @ The Blue Alliance](https://www.facebook.com/groups/moardata/), to submit video and match data we're missing on the site.
* Submit missing videos using the "Add Video" links on the site.
* Submit missing webcasts, team photos, etc using other links on the site.

### Contributing Code

1. Fork this project!
2. Make a branch to hold your changes.
3. Make changes!
4. Send over a pull request from your fork.
5. We'll review it, and push your changes to the site!

If you're having trouble getting set up, reach out to us at [our mailing list](https://groups.google.com/forum/?fromgroups#!forum/thebluealliance-developers) and we'll help you through it!

Setup
-----
1. Learn a bit about Git and GitHub:
  * Install git on your PATH
  * [GitHub help](https://help.github.com/)
  * [Try Git](https://try.github.io/)
2. Install [Python 2.7.X](https://www.python.org/downloads/)
3. Install [App Engine](https://cloud.google.com/appengine/docs)
  * Specifically use the [Python SDK](https://cloud.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python)
  * Windows/OS X: Run the installer and allow it make symbolic links (it might ask you to enter your root password)
  * Linux: Unzip the .zip file and add the location of your `google_appengine` directory to your `PATH` environment variable.
4. Get the latest version of The Blue Alliance
  * Fork TBA by clicking on "Fork" in the top right of [its GitHub page](https://github.com/the-blue-alliance/the-blue-alliance)
  * Run `git clone https://github.com/USERNAME/the-blue-alliance.git` where _USERNAME_ is your GitHub username, or use GitHub's Windows or OS X app to clone it to your computer
  * For detailed instructions see [the GitHub guide on contributing](https://guides.github.com/activities/contributing-to-open-source/index.html#contributing)
5. Install initial required Python packages
  * `pip install -r requirements.txt`
6. Install [Node.js](https://nodejs.org/) which includes [Node Package Manager](https://www.npmjs.org/)
7. Install [UglifyJS2](https://github.com/mishoo/UglifyJS2) by running `npm install uglify-js -g`
8. Install [gulp](https://github.com/gulpjs/gulp) by running `npm rm --global gulp && npm install --global gulp-cli`. This removes any version of `gulp` that was previously installed globally so it doesn't conflict with `gulp-cli`. Gulp is used as the build tool for Gameday2.
9. Install all node dependencies by running `npm install`. This includes `less`, which is used to build CSS files for production, as well as a number of packages used in Gameday2.
10. Fill out `static/javascript/tba_js/tba_keys_template.js` and save it in the same directory as `tba_keys.js`. It's okay to leave a key blank if you're not doing any development that requires it, but the file `tba_keys.js` must exist or else JavaScript won't compile.
11. Fill out `test_keys_template.json` and save it in the same directory as `test_keys.json`. These are used for unit testing on your local machine only.
12. Run `paver setup` to install remaining dependencies and do an initial build of static files (CSS, HTML templates, javascript) to get you going
13. Run the app in GoogleAppEngineLauncher according to the directions below, and visit the local URL to see your own copy of The Blue Alliance!

Run a local dev server
----------------------
1. Import the project into Google App Engine Launcher
  * NOTE: If you have the Linux version, skip to step 2, as it does not come packaged with the App Engine Launcher. You will be manually adding the ports and modules as options when launching the server.
  * Open App Engine Launcher
  * File > Add Existing Application...
  * Set the Application Path to your `the-blue-alliance` directory
  * Set port **8088**
  * Add modules (dispatch.yaml, app.yaml, app-backend-tasks.yaml, and app-backend-tasks-b2.yaml) as extra flags [https://cloud.google.com/appengine/docs/python/modules/#devserver](https://cloud.google.com/appengine/docs/python/modules/#devserver).
2. Run the app in App Engine Launcher and view its Logs window
  * If you are using the Linux version, you can start the application by moving into your `the-blue-alliance` directory and running `dev_appserver.py --port 8088 dispatch.yaml app.yaml app-backend-tasks.yaml app-backend-tasks-b2.yaml` on the command line.
3. You should now have a basic development installation!
  * Visit [localhost:8088](http://localhost:8088) to see your local version of The Blue Alliance
  * Also see [localhost:8088/admin/](http://localhost:8088/admin/)
4. Get some data into the local server
  * NOTE: These steps are intended for local dev servers. They might also work on a deployed server if you edit `tba_config.py` to set `DEBUG = True`.
  * NOTE: The /admin/ page's buttons "Get FMS Teams" and the existing import /tasks are broken due to the move to FMSAPI datafeed. "Create Test Events" still works *if* you have teams in the database. Try visiting the urls /tasks/enqueue/csv_restore_events/YEAR (for a chosen year) or /tasks/enqueue/csv_restore_events.
  * Visit, say, [localhost:8088/tasks/get/usfirst_teams_tpids/2015?skip=0](http://localhost:8088/tasks/get/usfirst_teams_tpids/2015?skip=0), [localhost:8088/tasks/get/usfirst_teams_tpids/2015?skip=1000](http://localhost:8088/tasks/get/usfirst_teams_tpids/2015?skip=1000), ...
  * Also visit [localhost:8088/tasks/enqueue/usfirst_event_details/2015](http://localhost:8088/tasks/enqueue/usfirst_event_details/2015), [2014](http://localhost:8088/tasks/enqueue/usfirst_event_details/2014), ...
  * Once you have events for a certain year, you can visit [localhost:8088/tasks/enqueue/csv_restore_events/2015](http://localhost:8088/tasks/enqueue/csv_restore_events/2015), [2014](http://localhost:8088/tasks/enqueue/csv_restore_events/2014), ... etc. to get data from [github.com/the-blue-alliance/the-blue-alliance-data](https://github.com/the-blue-alliance/the-blue-alliance-data) instead of hitting up usfirst.org lots of times.
  * If you want to test development using the offical FMS API, you can request API keys [here](https://usfirst.collab.net/sf/projects/first_community_developers/). Once you have your keys, you can input them in [the admin panel](http://localhost:8088/admin/authkeys)
5. Ignore these warnings in the local dev server:
  * `pytz is required to calculate future run times for cron jobs with timezones` (The pytz library is in the source tree and works fine.)

Run an App Engine server
------------------------
See [myTBA Configuration](https://github.com/the-blue-alliance/the-blue-alliance-android/wiki/myTBA-Configuration) for how to create and configure an App Engine server.

Setup notes:

* You _could_ edit the `app.yaml` file to change its `application:` setting from `tbatv-dev-hrd` to your app's Project ID, but then you'll have to remember to not check in that edit. Better yet, write a script like the following `mydeploy.sh` file (that filename is in `.gitignore`):

        #!/bin/sh
        appcfg.py --oauth2 --application=<MY_PROJECT_ID> update app.yaml app-backend-tasks.yaml
        appcfg.py --oauth2 --application=<MY_PROJECT_ID> update_dispatch .

* Note that it needs your application's "Project ID", not its "Project name".
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

Notes:

* See [localhost:8088/apidocs](http://localhost:8088/apidocs) and [localhost:8088/apidocs/webhooks](http://localhost:8088/apidocs/webhooks) for self-hosted API docs.


Paver Commands
--------------
Paver is an easy way automate repetitive tasks. For The Blue Alliance, these tasks are stored in _pavement.py_.
To install paver, use one of the methods below:

* Download and install paver from [http://pypi.python.org/pypi/Paver/](http://pypi.python.org/pypi/Paver/ "Paver")
* Run `easy_install Paver`

Paver commands include:

* `paver javascript`  -- combine and compress JavaScript files
* `paver less`  -- translate LESS files to CSS and combine with other CSS files
* `paver setup`  -- build CSS and JavaScript files
* `paver lint`
* `paver test_fast`  -- run tests that don't require HTTP

CSS Icon Sprites
-----------
Icons get combined into single files called sprites to reduce the number of HTTP requests needed to render a page.
To simplify development, we add icons normally (not to the sprite), and every so often we will combine them all into a sprite and fix all necessary CSS.

Potentially useful: http://spriteme.org/

Testing
-------
[![Build Status](https://travis-ci.org/the-blue-alliance/the-blue-alliance.svg?branch=master)](https://travis-ci.org/the-blue-alliance/the-blue-alliance)

Testing is implemented using a combination of [unittest2](http://pypi.python.org/pypi/unittest2 "Uniter Test 2") and the Google App Engine testbed framework. Test coverage is a work in progress, and focuses on maintaining datafeed integrity in the face of optimizations and changes to FIRST's data formats.

To run the tests, or just the offline (fast) tests:

* `paver test`
* `paver test_fast`
