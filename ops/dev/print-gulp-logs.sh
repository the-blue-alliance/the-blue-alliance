set -e

vagrant ssh -- -t 'tail -f /var/log/gulp.log'
