The Blue Alliance
==================
The Blue Alliance is a FIRST Robotics tool to help teams scout for,
compete at, and relive competitions.

[http://www.thebluealliance.com/](http://www.thebluealliance.com/ "The Blue Alliance")



Setup
---------

1. Download Google App engine launcher ([http://code.google.com/appengine/downloads.html](http://code.google.com/appengine/downloads.html "AppEngine"))
2. Import project file into Google App Engine Launcher
3. Run!
4. Visit /admin/debug to set up your local development version with data

Paver Commands
--------------

Paver is an easy way automate repetitive tasks. These tasks are stored in pavement.py. Download and install paver from [http://pypi.python.org/pypi/Paver/](http://pypi.python.org/pypi/Paver/ "Paver") or use easy_install to install it.

Simple Commands
---------------

- paver clean - Deletes artifacts that the app creates that you don't need.

LESS
----

The CSS files are compiled from LESS to ease in development. Use a program such as [http://wearekiss.com/simpless](http://wearekiss.com/simpless "Simpless") that automatically compiles
the LESS files into CSS. Just drag static/css into SimpLESS, and whenever you edit and save a LESS file, the CSS will be compiled! Make sure 
"minify" is enabled in order to minimize the final CSS file size.

Testing
-------

Testing is implemented using a combination of unittest2 and the Google App Engine testbed framework. Test coverage is a work in progress, and focuses on maintaining datafeed integrity in the face of optimizations and changes to FIRST's data formats.

To run the tests:

 `python run_tests.py (app_engine_sdk_path)`

On a Mac, /usr/local/google_appengine is the App Engine SDK path, so:

`python run_tests.py /usr/local/google_appengine`


Contributing
-----------
1. Fork it!
2. Make your changes on a branch.
3. Make changes!
4. Send pull request from your fork.
