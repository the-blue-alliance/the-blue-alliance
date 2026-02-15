#!/usr/bin/env python3
import argparse
import os
import sys
import time

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

# All bundles: (input_files, output_file, label)
BUNDLES = [
    (SCRIPTS_MAIN, SCRIPTS_MAIN_OUT, "Main"),
    (SCRIPTS_FIREBASE, SCRIPTS_FIREBASE_OUT, "Firebase"),
    # (SCRIPTS_FIREBASE_SERVICEWORKER, SCRIPTS_FIREBASE_SERVICEWORKER_OUT, "Firebase Messaging Serviceworker"),
    (SCRIPTS_EVENTWIZARD, SCRIPTS_EVENTWIZARD_OUT, "EventWizard"),
]


def compress_js(in_files, out_file):
    os.system(
        "npx uglify-js@3.17.4 {} --compress -o {}".format(" ".join(in_files), out_file)
    )
    print("=> %s" % out_file)
    print("")


def all_source_files():
    """Return the deduplicated set of all source files across all bundles."""
    files = set()
    for in_files, _, _ in BUNDLES:
        files.update(in_files)
    return files


def build(kind=None):
    for directory in ["src/build/javascript"]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    if kind == "js" or kind is None:
        for in_files, out_file, label in BUNDLES:
            print("Compressing %s JavaScript..." % label)
            compress_js(in_files, out_file)


def watch():
    """Watch source files for changes and rebuild affected bundles."""
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    # Build a mapping from source file path -> list of bundles that include it
    file_to_bundles = {}
    watch_dirs = set()
    for in_files, out_file, label in BUNDLES:
        for f in in_files:
            abs_path = os.path.abspath(f)
            file_to_bundles.setdefault(abs_path, []).append((in_files, out_file, label))
            watch_dirs.add(os.path.dirname(abs_path))

    class CompressHandler(FileSystemEventHandler):
        def __init__(self):
            self._last_rebuild = 0.0

        def on_modified(self, event):
            if event.is_directory:
                return
            abs_path = os.path.abspath(event.src_path)
            if abs_path not in file_to_bundles:
                return
            # Debounce: skip if we just rebuilt within the last second
            now = time.time()
            if now - self._last_rebuild < 1.0:
                return
            self._last_rebuild = now
            for in_files, out_file, label in file_to_bundles[abs_path]:
                print(
                    "\n[watch] %s changed, recompressing %s JavaScript..."
                    % (os.path.basename(event.src_path), label)
                )
                compress_js(in_files, out_file)

    handler = CompressHandler()
    observer = Observer()
    for d in watch_dirs:
        observer.schedule(handler, d, recursive=False)

    observer.start()
    print("[watch] Watching %d source files for changes..." % len(file_to_bundles))
    sys.stdout.flush()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compress legacy JS bundles")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="After initial build, watch source files and rebuild on changes",
    )
    parser.add_argument("kind", nargs="?", default=None, help="Build kind (e.g. 'js')")
    args = parser.parse_args()

    build(args.kind)

    if args.watch:
        watch()
