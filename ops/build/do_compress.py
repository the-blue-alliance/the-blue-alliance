#!/usr/bin/env python3
import argparse
import os
import sys
import threading
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
            self._timers: dict[str, threading.Timer] = {}
            self._lock = threading.Lock()

        def _handle_event(self, event):
            if event.is_directory:
                return
            # For moved events (atomic saves), use the destination path
            src_path = getattr(event, "dest_path", event.src_path)
            abs_path = os.path.abspath(src_path)
            if abs_path not in file_to_bundles:
                return
            for in_files, out_file, label in file_to_bundles[abs_path]:
                self._schedule_rebuild(in_files, out_file, label, src_path)

        def on_modified(self, event):
            self._handle_event(event)

        def on_created(self, event):
            self._handle_event(event)

        def on_moved(self, event):
            self._handle_event(event)

        def _schedule_rebuild(self, in_files, out_file, label, src_path):
            """Debounce per-bundle: rebuild after a short quiet period."""
            with self._lock:
                if out_file in self._timers:
                    self._timers[out_file].cancel()

                def _rebuild():
                    with self._lock:
                        self._timers.pop(out_file, None)
                    print(
                        "\n[watch] %s changed, recompressing %s JavaScript..."
                        % (os.path.basename(src_path), label)
                    )
                    compress_js(in_files, out_file)

                timer = threading.Timer(0.3, _rebuild)
                self._timers[out_file] = timer
                timer.start()

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
