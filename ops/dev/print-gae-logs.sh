set -e

vagrant ssh -- -t 'tail -f /var/log/tba.log'
