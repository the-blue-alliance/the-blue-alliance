#!/usr/bin/python
import os.path
import optparse

YUI_COMPRESSOR = 'utils/yuicompressor-2.4.7.jar'

SCRIPTS_MAIN = ['static/jwplayer/jwplayer.js',
                'static/xcharts/d3.v2.min.js',
                'static/xcharts/xcharts.min.js',
                'static/javascript/tba_js/tablesorter.js',
                'static/javascript/tba_js/tba_charts.js',
                'static/javascript/tba_js/tba_countdown.js',
                'static/javascript/tba_js/tba_sidebar.js',
                'static/javascript/tba_js/tba_typeahead.js',
                'static/javascript/tba_js/tba_favorites.js',
                'static/javascript/tba_js/tba.js',
                'static/javascript/tba_js/ReView0.65b.js',
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
                    'static/css/precompiled_css/blue_banners.css',
                    'static/xcharts/xcharts.min.css',
                    'static/css/less_css/tba_style.main.css',
                    ]

STYLESHEETS_GAMEDAY = ['static/css/precompiled_css/jquery.fancybox.css',
                       'static/css/precompiled_css/tablesorter.css',
                       'static/css/less_css/tba_style.gameday.css',
                       ]

SCRIPTS_MAIN_OUT = 'static/javascript/tba_combined_js.main.min.js'
SCRIPTS_GAMEDAY_OUT = 'static/javascript/tba_combined_js.gameday.min.js'
SCRIPTS_EVENTWIZARD_OUT = 'static/javascript/tba_combined_js.eventwizard.min.js'
STYLESHEETS_MAIN_OUT = 'static/css/tba_combined_style.main.min.css'
STYLESHEETS_GAMEDAY_OUT = 'static/css/tba_combined_style.gameday.min.css'


def compress(in_files, out_file, in_type='js', verbose=False,
             temp_file='.temp'):
    temp = open(temp_file, 'w')
    for f in in_files:
        fh = open(f)
        data = fh.read() + '\n'
        fh.close()

        temp.write(data)

        print ' + %s' % f
    temp.close()

    options = ['-o "%s"' % out_file,
               '--type %s' % in_type]

    if verbose:
        options.append('-v')

    os.system('java -jar "%s" %s "%s"' % (YUI_COMPRESSOR,
                                          ' '.join(options),
                                          temp_file))

    org_size = os.path.getsize(temp_file)
    new_size = os.path.getsize(out_file)

    print '=> %s' % out_file
    print 'Original: %.2f kB' % (org_size / 1024.0)
    print 'Compressed: %.2f kB' % (new_size / 1024.0)
    print 'Reduction: %.1f%%' % (float(org_size - new_size) / org_size * 100)
    print ''


def main(kind=None):
    if kind == 'js' or kind is None:
        print 'Compressing Main JavaScript...'
        compress(SCRIPTS_MAIN, SCRIPTS_MAIN_OUT, 'js')

        print 'Compressing GameDay JavaScript...'
        compress(SCRIPTS_GAMEDAY, SCRIPTS_GAMEDAY_OUT, 'js')

        print 'Compressing EventWizard JavaScript...'
        compress(SCRIPTS_EVENTWIZARD, SCRIPTS_EVENTWIZARD_OUT, 'js')

    if kind == 'css' or kind is None:
        print 'Compressing Main CSS...'
        compress(STYLESHEETS_MAIN, STYLESHEETS_MAIN_OUT, 'css')

        print 'Compressing GameDay CSS...'
        compress(STYLESHEETS_GAMEDAY, STYLESHEETS_GAMEDAY_OUT, 'css')

if __name__ == '__main__':
    parser = optparse.OptionParser()
    options, args = parser.parse_args()
    if len(args) < 1:
        main()
    else:
        main(args[0])
