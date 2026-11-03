# Serves the site's Google fonts (Barlow Condensed, IBM Plex Sans) locally to Playwright. Without this, local screenshots and
# measurements use fallback fonts and are WRONG. Setup once: mkdir -p /tmp/claude-0/fonts && cd /tmp/claude-0/fonts && npm init -y && npm i @fontsource/barlow-condensed @fontsource/ibm-plex-sans
import os
D='/tmp/claude-0/fonts/node_modules/@fontsource/'
F=[('Barlow Condensed','barlow-condensed',w,s) for w,s in [(500,'normal'),(600,'normal'),(700,'normal'),(700,'italic'),(800,'italic')]]+[('IBM Plex Sans','ibm-plex-sans',w,'normal') for w in (400,500,600)]
CSS=''.join(f"@font-face{{font-family:'{fam}';font-style:{s};font-weight:{w};font-display:swap;src:url(https://fonts.local/{d}-latin-{w}-{s}.woff2) format('woff2')}}" for fam,d,w,s in F)
def setup(pg):
    pg.route('https://fonts.googleapis.com/**',lambda r:r.fulfill(status=200,content_type='text/css',body=CSS,headers={'access-control-allow-origin':'*'}))
    def font(r):
        n=r.request.url.rsplit('/',1)[1];d=n.split('-latin')[0]
        r.fulfill(status=200,content_type='font/woff2',body=open(D+d+'/files/'+n,'rb').read(),headers={'access-control-allow-origin':'*'})
    pg.route('https://fonts.local/**',font)
