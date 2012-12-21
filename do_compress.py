#!/usr/bin/python
import os.path
import optparse

YUI_COMPRESSOR = 'yuicompressor-2.4.7.jar'

SCRIPTS_MAIN = ['static/javascript/jquery_js/jquery.min.js',
                'static/javascript/jquery_js/jquery-ui-1.8.13.custom.min.js',
                'static/javascript/jquery_js/jquery.ui.touch-punch.min.js',
                'static/javascript/bootstrap_js/bootstrap.js',
                'static/javascript/bootstrap_js/bootstrap-typeahead.js',
                'static/javascript/jquery_js/jquery.fancybox.pack.js',
                'static/jwplayer/jwplayer.js',
                'static/javascript/jquery_js/jquery.fitvids.js',
                'static/javascript/tba_js/tba.js',
                ]
SCRIPTS_MAIN_OUT_DEBUG = 'static/javascript/debug/tba_combined.main.js'
SCRIPTS_MAIN_OUT = 'static/javascript/tba_combined.main.min.js'

SCRIPTS_GAMEDAY = SCRIPTS_MAIN + ['static/javascript/tba_js/gameday.js']
SCRIPTS_GAMEDAY_OUT_DEBUG = 'static/javascript/debug/tba_combined.gameday.js'
SCRIPTS_GAMEDAY_OUT = 'static/javascript/tba_combined.gameday.min.js'

STYLESHEETS_MAIN = ['static/css/style.css',
                    'static/css/jquery-ui-1.8.13.custom.css',
                    'static/css/jquery.fancybox.css',
                    ]
STYLESHEETS_MAIN_OUT = 'static/css/style.min.css'

STYLESHEETS_GAMEDAY = ['static/css/style_gameday.css',
                       'static/css/jquery-ui-1.8.13.custom.css',
                       'static/css/jquery.fancybox.css',
                       ]
STYLESHEETS_GAMEDAY_OUT = 'static/css/style_gameday.min.css'


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
    if kind == 'js' or kind == None:
        print 'Compressing Main JavaScript...'
        compress(SCRIPTS_MAIN, SCRIPTS_MAIN_OUT, 'js', False, SCRIPTS_MAIN_OUT_DEBUG)
    
        print 'Compressing GameDay JavaScript...'
        compress(SCRIPTS_GAMEDAY, SCRIPTS_GAMEDAY_OUT, 'js', False, SCRIPTS_GAMEDAY_OUT_DEBUG)

    if kind == 'css' or kind == None:
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
