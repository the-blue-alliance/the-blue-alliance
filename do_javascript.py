#!/usr/bin/python
import os, os.path, shutil

YUI_COMPRESSOR = 'yuicompressor-2.4.7.jar'
SCRIPTS = [
    'static/javascript/jquery.min.js',
    'static/javascript/jquery-ui-1.8.13.custom.min.js',
    'static/javascript/jquery.ui.touch-punch.min.js',
    'static/javascript/tba.js',
    'static/javascript/bootstrap.js',
    'static/javascript/bootstrap-typeahead.js',
    'static/javascript/jquery.fancybox.pack.js',
    'static/jwplayer/jwplayer.js',
    ]
SCRIPTS_OUT_DEBUG = 'static/javascript/tba_combined.js'
SCRIPTS_OUT = 'static/javascript/tba_combined.min.js'


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


def main():
    print 'Compressing JavaScript...'
    compress(SCRIPTS, SCRIPTS_OUT, 'js', False, SCRIPTS_OUT_DEBUG)


if __name__ == '__main__':
    main()
