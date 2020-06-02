set -e

npx -p less lessc src/backend/web/static/css/less_css/tba_style.main.less src/build/temp/tba_style.main.css
python ./ops/build/do_compress.py
npm run build
