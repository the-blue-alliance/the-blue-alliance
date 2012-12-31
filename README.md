The Blue Alliance
==================
The Blue Alliance is a FIRST Robotics tool to help teams scout for, compete at, and relive competitions. You can see how the whole site works here, or even write code to make it better!

Contributing
------------
1. Fork this project!
2. Make your changes on a branch.
3. Make changes!
4. Send pull request from your fork.
5. We'll review it, and push your changes to the site!

If you're having trouble getting set up, reach out to us at [our mailing list](https://groups.google.com/forum/?fromgroups#!forum/thebluealliance-developers) and we'll help you through it!

Setup
-----
0. Learn a bit about Git and Github:
	* http://help.github.com
	* http://learn.github.com
1. Install [App Engine](http://code.google.com/intl/en/appengine/)
	* Specifically use the [Python SDK](http://code.google.com/intl/en/appengine/downloads.html#Google_App_Engine_SDK_for_Python)
	* Run installer and allow it make symbolic links (you will be asked to enter your root password)
2. Get the latest version of The Blue Alliance
	* Run `git clone git://github.com/gregmarra/the-blue-alliance.git`
3. Import the project into Google App Engine Launcher
	* By default TBA uses port **8088**, make sure your local setup is consistent with this
4. Run the app in App Engine
5. Get some test data: In your terminal console, from the `the-blue-alliance` directory, run the following command
	* `paver setup` (Make sure that you already have [Paver installed](#paver-commands))
6. You should now have a basic development installation!
	* Visit [localhost:8088](http://localhost:8088) to see your local version of The Blue Alliance
	* Visit [localhost:8088/admin/debug](http://localhost:8088/admin/debug) to run more commands and populate your install with extra data

Paver Commands
--------------
Paver is an easy way automate repetitive tasks. For The Blue Alliance, these tasks are stored in _pavement.py_. 
To install paver, use one of the methods below:
* Download and install paver from [http://pypi.python.org/pypi/Paver/](http://pypi.python.org/pypi/Paver/ "Paver") 
* Run `easy_install Paver`

## Simple Commands
* `paver clean` - Deletes artifacts that the app creates that you don't need.

CSS Icon Sprites
-----------
If possible, icons are combined into single files called sprites to reduce the number of requests needed to render a page.
To simplify development, we add icons normally (not to the sprite), and every so often we will combine them all into a sprite and fix all necessary CSS.
Potentially useful: http://spriteme.org/

LESS
----
The CSS files are compiled from LESS to ease in development. Use a program such as [http://wearekiss.com/simpless](http://wearekiss.com/simpless "Simpless") that automatically compiles
the LESS files into CSS. Just drag static/css into SimpLESS, and whenever you edit and save a LESS file, the CSS will be compiled! Make sure "minify" is enabled in order to minimize the final CSS file size.

CSS/Javascript Combination and Compression
------------------------------------------
Once the LESS files are compressed into CSS, we combine the resulting file with other CSS files, such as 'jquery-ui-1.8.13.custom.css.' Similarly, we combine all relevant Javascript files into a single file and compress them.
This means that whenever changes are made to CSS or Javascript, you must run of the following:
* `paver less`
* `paver javascript`

Facebook
--------
We use the Facebook SDK to allow users to log in to The Blue Alliance using their pre-existing Facebook account. The Javascript
portion of this is loaded dynamically and the backend portion is kept in facebook.py, provided by [https://github.com/pythonforfacebook/facebook-sdk](https://github.com/pythonforfacebook/facebook-sdk "Facebook on Github"). To enable your development
environment, you must register an app at the [https://developers.facebook.com/apps](https://developers.facebook.com/apps "Facebook Developer Center"). 

Once you register an app (named tbatv-dev-YOURNAME), you can configure The Blue Alliance to use the App ID and secret by adding them to your [Sitevars](http://localhost:8088/admin/sitevar) (/admin/sitevar/create). _Each developer should have their own App ID and secret_.

Testing
-------
Testing is implemented using a combination of [unittest2](http://pypi.python.org/pypi/unittest2 "Uniter Test 2") and the Google App Engine testbed framework. Test coverage is a work in progress, and focuses on maintaining datafeed integrity in the face of optimizations and changes to FIRST's data formats.

To run the tests, or just the offline (fast) tests:
* `paver test`
* `paver test_fast`
