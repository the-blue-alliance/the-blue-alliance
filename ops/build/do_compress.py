#!/usr/bin/python
import optparse
import os

SCRIPTS_MAIN = [
    "src/backend/web/static/jwplayer/jwplayer.js",
    "src/backend/web/static/xcharts/d3.v2.min.js",
    "src/backend/web/static/xcharts/xcharts.min.js",
    "src/backend/web/static/javascript/utils/client_detection.js",
    "src/backend/web/static/javascript/tba_js/tablesorter.js",
    "src/backend/web/static/javascript/tba_js/tba_keys.js",
    "src/backend/web/static/javascript/tba_js/tba.js",
    "src/backend/web/static/javascript/tba_js/tba_charts.js",
    "src/backend/web/static/javascript/tba_js/tba_countdown.js",
    "src/backend/web/static/javascript/tba_js/tba_sidebar.js",
    "src/backend/web/static/javascript/tba_js/tba_typeahead.js",
    "src/backend/web/static/javascript/tba_js/tba_favorites.js",
    "src/backend/web/static/javascript/tba_js/ReView0.65b.js",
]

SCRIPTS_FIREBASE = [
    "src/backend/web/static/javascript/tba_js/tba_keys.js",
    "src/backend/web/static/javascript/tba_js/tba_firebase.js",
    "src/backend/web/static/javascript/tba_js/tba_auth.js",
    # 'src/backend/web/static/javascript/tba_js/tba_fcm.js',
]

SCRIPTS_FIREBASE_SERVICEWORKER = [
    "src/backend/web/static/javascript/tba_js/tba_keys.js",
    "src/backend/web/static/javascript/tba_js/firebase_messaging_serviceworker.js",
]

SCRIPTS_GAMEDAY = SCRIPTS_MAIN + [
    "src/backend/web/static/javascript/tba_js/gameday.js",
    "src/backend/web/static/javascript/tba_js/gameday_twitter.js",
    "src/backend/web/static/javascript/tba_js/gameday_matchbar.js",
    "src/backend/web/static/javascript/tba_js/gameday_ticker.js",
    "src/backend/web/static/javascript/tba_js/gameday_mytba.js",
]

SCRIPTS_EVENTWIZARD = [
    "src/backend/web/static/javascript/tba_js/eventwizard_apiwrite.js",
    "src/backend/web/static/javascript/tba_js/eventwizard.js",
]

STYLESHEETS_MAIN = [
    "src/backend/web/static/css/precompiled_css/jquery.fancybox.css",
    "src/backend/web/static/css/precompiled_css/tablesorter.css",
    "src/backend/web/static/xcharts/xcharts.min.css",
    "src/build/temp/tba_style.main.css",
]

STYLESHEETS_GAMEDAY = [
    "src/backend/web/static/css/precompiled_css/jquery.fancybox.css",
    "src/backend/web/static/css/precompiled_css/tablesorter.css",
    "src/backend/web/static/css/less_css/tba_style.gameday.css",
]

SCRIPTS_MAIN_OUT = "src/build/javascript/tba_combined_js.main.min.js"
SCRIPTS_FIREBASE_OUT = "src/build/javascript/tba_combined_js.firebase.min.js"
SCRIPTS_GAMEDAY_OUT = "src/build/javascript/tba_combined_js.gameday.min.js"
SCRIPTS_FIREBASE_SERVICEWORKER_OUT = "src/build/javascript/firebase-messaging-sw.js"
SCRIPTS_EVENTWIZARD_OUT = "src/build/javascript/tba_combined_js.eventwizard.min.js"
STYLESHEETS_MAIN_OUT = "src/build/css/tba_combined_style.main.min.css"
STYLESHEETS_GAMEDAY_OUT = "src/build/css/tba_combined_style.gameday.min.css"


def compress_css(in_files, out_file, verbose=False, temp_file=".temp"):
    os.system("npx uglifycss {} --output {}".format(" ".join(in_files), out_file))
    print("=> %s" % out_file)
    print("")


def compress_js(in_files, out_file):
    os.system("npx uglify-js {} --compress -o {}".format(" ".join(in_files), out_file))
    print("=> %s" % out_file)
    print("")


def main(kind=None):
    for directory in ["src/build/javascript", "src/build/css"]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    if kind == "js" or kind is None:
        print("Compressing Main JavaScript...")
        compress_js(SCRIPTS_MAIN, SCRIPTS_MAIN_OUT)

        print("Compressing Firebase JavaScript...")
        compress_js(SCRIPTS_FIREBASE, SCRIPTS_FIREBASE_OUT)

        # print('Compressing Firebase Messaging Serviceworker JavaScript...')
        # compress_js(SCRIPTS_FIREBASE_SERVICEWORKER, SCRIPTS_FIREBASE_SERVICEWORKER_OUT)
        #
        # print('Compressing GameDay JavaScript...')
        # compress_js(SCRIPTS_GAMEDAY, SCRIPTS_GAMEDAY_OUT)
        #
        # print('Compressing EventWizard JavaScript...')
        # compress_js(SCRIPTS_EVENTWIZARD, SCRIPTS_EVENTWIZARD_OUT)

    if kind == "css" or kind is None:
        print("Compressing Main CSS...")
        compress_css(STYLESHEETS_MAIN, STYLESHEETS_MAIN_OUT)

        # print('Compressing GameDay CSS...')
        # compress_css(STYLESHEETS_GAMEDAY, STYLESHEETS_GAMEDAY_OUT)


if __name__ == "__main__":
    parser = optparse.OptionParser()
    options, args = parser.parse_args()
    if len(args) < 1:
        main()
    else:
        main(args[0])
