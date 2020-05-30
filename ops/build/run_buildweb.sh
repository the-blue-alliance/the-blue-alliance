set -e

npx -p less lessc src/web/static/css/less_css/tba_style.main.less src/web/static/css/less_css/tba_style.main.css
python ./ops/build/do_compress.py
