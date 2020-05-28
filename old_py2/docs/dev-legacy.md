Setup (manual)
--------------
1. Learn a bit about Git and GitHub:
  * Install git on your PATH
  * [GitHub help](https://help.github.com/)
  * [Try Git](https://try.github.io/)
2. Install [Python 2.7.X](https://www.python.org/downloads/)
3. Install [App Engine](https://cloud.google.com/appengine/docs)
  * Specifically use the [Standard Environment Python SDK](https://cloud.google.com/appengine/docs/standard/python/download)
  * Windows/OS X: Run the installer and allow it make symbolic links (it might ask you to enter your root password)
  * Linux: Unzip the .zip file and add the location of your `google_appengine` directory to your `PATH` environment variable.
4. Get the latest version of The Blue Alliance
  * Fork TBA by clicking on "Fork" in the top right of [its GitHub page](https://github.com/the-blue-alliance/the-blue-alliance)
  * Run `git clone https://github.com/USERNAME/the-blue-alliance.git` where _USERNAME_ is your GitHub username, or use GitHub's Windows or OS X app to clone it to your computer
  * For detailed instructions see [the GitHub guide on contributing](https://guides.github.com/activities/contributing-to-open-source/index.html#contributing)
5. Install initial required Python packages
  * `pip install -r requirements.txt`
6. Install [Node.js](https://nodejs.org/) which includes [Node Package Manager](https://www.npmjs.org/)
7. Install [UglifyJS](https://www.npmjs.com/package/uglify-es) by running `npm install uglify-es -g` and [UglifyCSS](https://github.com/fmarcia/UglifyCSS) by running `npm install uglifycss -g`
8. Install [gulp](https://github.com/gulpjs/gulp) by running `npm rm --global gulp && npm install --global gulp-cli`. This removes any version of `gulp` that was previously installed globally so it doesn't conflict with `gulp-cli`. Gulp is used as the build tool for Gameday2.
9. Install all node dependencies by running `npm install`. This includes `less`, which is used to build CSS files for production, as well as a number of packages used in Gameday2.
10. Fill out `static/javascript/tba_js/tba_keys_template.js` and save it in the same directory as `tba_keys.js`. It's okay to leave a key blank if you're not doing any development that requires it, but the file `tba_keys.js` must exist or else JavaScript won't compile.
11. Fill out `test_keys_template.json` and save it in the same directory as `test_keys.json`. These are used for unit testing on your local machine only.
12. Run `paver setup` to install remaining dependencies and do an initial build of static files (CSS, HTML templates, javascript) to get you going
13. Run the app in GoogleAppEngineLauncher according to the directions below, and visit the local URL to see your own copy of The Blue Alliance!

Run a Local Dev Server
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
  * Alternatively, run `paver run`.
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

