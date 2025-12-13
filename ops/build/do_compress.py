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

SCRIPTS_EVENTWIZARD = [
    "src/backend/web/static/javascript/tba_js/eventwizard_apiwrite.js",
    "src/backend/web/static/javascript/tba_js/eventwizard.js",
]

SCRIPTS_MAIN_OUT = "src/build/javascript/tba_combined_js.main.min.js"
SCRIPTS_FIREBASE_OUT = "src/build/javascript/tba_combined_js.firebase.min.js"
SCRIPTS_FIREBASE_SERVICEWORKER_OUT = "src/build/javascript/firebase-messaging-sw.js"
SCRIPTS_EVENTWIZARD_OUT = "src/build/javascript/tba_combined_js.eventwizard.min.js"


def compress_js(in_files, out_file):
    os.system(
        "npx uglify-js@3.17.4 {} --compress -o {}".format(" ".join(in_files), out_file)
    )
    print("=> %s" % out_file)
    print("")


def main(kind=None):
    for directory in ["src/build/javascript"]:
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
        print("Compressing EventWizard JavaScript...")
        compress_js(SCRIPTS_EVENTWIZARD, SCRIPTS_EVENTWIZARD_OUT)


if __name__ == "__main__":
    parser = optparse.OptionParser()
    options, args = parser.parse_args()
    if len(args) < 1:
        main()
    else:
        main(args[0])
