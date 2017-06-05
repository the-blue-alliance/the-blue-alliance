#!/usr/bin/python
import os
import optparse

SCRIPTS_MAIN = ['static/jwplayer/jwplayer.js',
                'static/xcharts/d3.v2.min.js',
                'static/xcharts/xcharts.min.js',
                'static/javascript/utils/client_detection.js',
                'static/javascript/tba_js/tablesorter.js',
                'static/javascript/tba_js/tba_keys.js',
                'static/javascript/tba_js/tba.js',
                'static/javascript/tba_js/tba_charts.js',
                'static/javascript/tba_js/tba_countdown.js',
                'static/javascript/tba_js/tba_sidebar.js',
                'static/javascript/tba_js/tba_typeahead.js',
                'static/javascript/tba_js/tba_favorites.js',
                'static/javascript/tba_js/tba_fcm.js',
                'static/javascript/tba_js/ReView0.65b.js',
                ]

SCRIPTS_FIREBASE_SERVICEWORKER = ['static/javascript/tba_js/tba_keys.js',
                                  'static/javascript/tba_js/firebase_messaging_serviceworker.js',
                                  ]

SCRIPTS_GAMEDAY = SCRIPTS_MAIN + ['static/javascript/tba_js/gameday.js',
                                  'static/javascript/tba_js/gameday_twitter.js',
                                  'static/javascript/tba_js/gameday_matchbar.js',
                                  'static/javascript/tba_js/gameday_ticker.js',
                                  'static/javascript/tba_js/gameday_mytba.js']

SCRIPTS_EVENTWIZARD = ['static/javascript/tba_js/eventwizard_apiwrite.js',
                       'static/javascript/tba_js/eventwizard.js']

STYLESHEETS_MAIN = ['static/css/precompiled_css/jquery.fancybox.css',
                    'static/css/precompiled_css/tablesorter.css',
                    'static/xcharts/xcharts.min.css',
                    'static/css/less_css/tba_style.main.css',
                    ]

STYLESHEETS_GAMEDAY = ['static/css/precompiled_css/jquery.fancybox.css',
                       'static/css/precompiled_css/tablesorter.css',
                       'static/css/less_css/tba_style.gameday.css',
                       ]

SCRIPTS_MAIN_OUT = 'static/compiled/javascript/tba_combined_js.main.min.js'
SCRIPTS_GAMEDAY_OUT = 'static/compiled/javascript/tba_combined_js.gameday.min.js'
SCRIPTS_FIREBASE_SERVICEWORKER_OUT = 'static/compiled/javascript/firebase-messaging-sw.js'
SCRIPTS_EVENTWIZARD_OUT = 'static/compiled/javascript/tba_combined_js.eventwizard.min.js'
STYLESHEETS_MAIN_OUT = 'static/compiled/css/tba_combined_style.main.min.css'
STYLESHEETS_GAMEDAY_OUT = 'static/compiled/css/tba_combined_style.gameday.min.css'


def compress_css(in_files, out_file, verbose=False, temp_file='.temp'):
    os.system('uglifycss {} --output {}'.format(' '.join(in_files), out_file))
    print '=> %s' % out_file
    print ''


def compress_js(in_files, out_file):
    os.system('uglifyjs {} --compress -o {}'.format(' '.join(in_files), out_file))
    print '=> %s' % out_file
    print ''


def main(kind=None):
    for directory in ['static/compiled/javascript', 'static/compiled/css']:
        if not os.path.exists(directory):
            os.makedirs(directory)

    if kind == 'js' or kind is None:
        print 'Compressing Main JavaScript...'
        compress_js(SCRIPTS_MAIN, SCRIPTS_MAIN_OUT)

        print 'Compressing Firebase Messaging Serviceworker JavaScript...'
        compress_js(SCRIPTS_FIREBASE_SERVICEWORKER, SCRIPTS_FIREBASE_SERVICEWORKER_OUT)

        print 'Compressing GameDay JavaScript...'
        compress_js(SCRIPTS_GAMEDAY, SCRIPTS_GAMEDAY_OUT)

        print 'Compressing EventWizard JavaScript...'
        compress_js(SCRIPTS_EVENTWIZARD, SCRIPTS_EVENTWIZARD_OUT)

    if kind == 'css' or kind is None:
        print 'Compressing Main CSS...'
        compress_css(STYLESHEETS_MAIN, STYLESHEETS_MAIN_OUT)

        print 'Compressing GameDay CSS...'
        compress_css(STYLESHEETS_GAMEDAY, STYLESHEETS_GAMEDAY_OUT)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    options, args = parser.parse_args()
    if len(args) < 1:
        main()
    else:
        main(args[0])
