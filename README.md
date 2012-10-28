The Blue Alliance
==================
The Blue Alliance is a FIRST Robotics tool to help teams scout for, compete at, and relive competitions. You can see how the whole site works here, or even write code to make it better!

[http://www.thebluealliance.com/](http://www.thebluealliance.com/ "The Blue Alliance")

Contributing
------------
1. Fork this project!
2. Make your changes on a branch.
3. Make changes!
4. Send pull request from your fork.
5. We'll review it, and push your changes to the site!

If you've having trouble getting set up, reach out to us at [https://groups.google.com/forum/?fromgroups#!forum/thebluealliance-developers](our mailing list) and we'll help you through it!

Setup
-----
0. Learn a bit about Git and Github: https://help.github.com/
1. Download Google App engine launcher ([http://code.google.com/appengine/downloads.html](http://code.google.com/appengine/downloads.html "AppEngine"))
2. Import project file into Google App Engine Launcher
3. Run the app in AppEngine
4. Get some test data: In the console, run `paver setup`
5. Visit /admin/debug to set up your local development version with data

Paver Commands
--------------
Paver is an easy way automate repetitive tasks. These tasks are stored in pavement.py. Download and install paver from [http://pypi.python.org/pypi/Paver/](http://pypi.python.org/pypi/Paver/ "Paver") or use easy_install to install it.

## Simple Commands
- `paver clean` - Deletes artifacts that the app creates that you don't need.

CSS Icon Sprites
-----------
If possible, icons are combined into single files called sprites to reduce the number of requests needed to render a page.
To simplify development, we add icons normally (not to the sprite), and every so often we will combine them all into a sprite and fix all necessary CSS.
Potentially useful: http://spriteme.org/

LESS
----
The CSS files are compiled from LESS to ease in development. Use a program such as [http://wearekiss.com/simpless](http://wearekiss.com/simpless "Simpless") that automatically compiles
the LESS files into CSS. Just drag static/css into SimpLESS, and whenever you edit and save a LESS file, the CSS will be compiled! Make sure 
"minify" is enabled in order to minimize the final CSS file size.

CSS/Javascript Combination and Compression
------------------------------------------
Once the LESS files are compressed into CSS, we combine the resulting file with other CSS files, such as 'jquery-ui-1.8.13.custom.css.' Similarly, we combine all relevant Javascript files into a single file and compress them.
This means that whenever changes are made to CSS or Javascript, you must run of the following:
- `paver less`
- `paver javascript`

Facebook
--------
We use the Facebook SDK to allow users to log in to The Blue Alliance using their pre-existing Facebook account. The Javascript
portion of this is loaded dynamically and the backend portion is kept in facebook.py, provided by [https://github.com/pythonforfacebook/facebook-sdk](https://github.com/pythonforfacebook/facebook-sdk "Facebook on Github"). To enable your development
environment, you must register an app at the [https://developers.facebook.com/apps](https://developers.facebook.com/apps "Facebook Developer Center"). Once you register an app (named tbatv-dev-YOURNAME), you can import the App ID and secret into the tba_config. Each developer should have their own App ID and secret.

Testing
-------
Testing is implemented using a combination of unittest2 and the Google App Engine testbed framework. Test coverage is a work in progress, and focuses on maintaining datafeed integrity in the face of optimizations and changes to FIRST's data formats.

To run the tests, or just the offline (fast) tests:
- `paver test`
- `paver test_fast`
