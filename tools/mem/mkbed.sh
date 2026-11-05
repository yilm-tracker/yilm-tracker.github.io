# mkbed.sh <built site dir> <bed dir>: copy a built site and point its Google Fonts link at the local fonts
set -e; rm -rf "$2"; cp -r "$1" "$2"; mkdir -p "$2/__fonts"; cp $(dirname $0)/fonts.css "$2/__fonts/"; cp /tmp/claude-0/fonts/node_modules/@fontsource/*/files/*-latin-*.woff2 "$2/__fonts/"; cp $(dirname $0)/frame.html "$2/__frame.html"; printf "<!doctype html><title>blank</title><p>blank" > "$2/blank.html"
python3 - "$2/index.html" <<'P'
import sys,re;p=sys.argv[1];s=open(p,encoding='utf-8').read()
s,n=re.subn(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2[^"]*">','<link rel="stylesheet" href="/__fonts/fonts.css">',s);assert n==1,n
s=re.sub(r'<link rel="preconnect"[^>]*>\n?','',s);open(p,'w',encoding='utf-8').write(s)
P
