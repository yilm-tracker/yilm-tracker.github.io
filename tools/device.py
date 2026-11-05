# iPhone Safari emulation for local QA. A width token is either plain CSS px or a device token:
#   402, 1440        plain desktop-style viewport (CSS px = the number), as before
#   402P / 440P      iPhone portrait:  isMobile, hasTouch, Safari UA, DPR 3, Safari page zoom (see below)
#   874L / 956L      iPhone landscape: same, width x height 874x402 / 956x440 points
#   956L@1           any device token with an explicit page zoom (1 = 100%)
# Safari page zoom (aA menu) changes the CSS viewport: layout width = points / zoom, DPR = 3 x zoom. Nicklaus's device
# shows the 956-point landscape nav band at 34-922 points = the >=1100px desktop layout at 85% (956/0.85 = 1125 CSS px;
# band (1125-80) x 0.85 = 888 points, left 40 x 0.85 = 34). Device tokens therefore default to zoom 0.85 (DT_ZOOM overrides).
# Report device measurements in points (CSS px x zoom), which is what a screenshot of the phone shows.
import os
UA = ('Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) '
      'Version/18.0 Mobile/15E148 Safari/604.1')
SIZES = {'402P': (402, 874), '440P': (440, 956), '360P': (360, 780), '874L': (874, 402), '956L': (956, 440)}
ZOOM = float(os.environ.get('DT_ZOOM', '0.85'))

def parse(tok):
    """-> dict(token, points (w,h), zoom, css (w,h), device bool)"""
    tok = str(tok); z = None
    if '@' in tok: tok, z = tok.split('@'); z = float(z)
    if tok.upper() in SIZES:
        w, h = SIZES[tok.upper()]; z = ZOOM if z is None else z
        return {'token': tok.upper() + ('' if z == ZOOM else f'@{z:g}'), 'points': (w, h), 'zoom': z, 'device': True,
                'css': (round(w / z), round(h / z))}
    w = int(tok); return {'token': str(w), 'points': (w, None), 'zoom': 1.0, 'device': False, 'css': (w, None)}

def new_page(browser, tok, height=1000):
    """New page for a width token; returns (page, info). Plain widths keep the old behaviour (viewport w x height)."""
    d = parse(tok)
    if not d['device']:
        return browser.new_page(viewport={'width': d['css'][0], 'height': height}), d
    ctx = browser.new_context(viewport={'width': d['css'][0], 'height': d['css'][1]}, device_scale_factor=3 * d['zoom'],
                              is_mobile=True, has_touch=True, user_agent=UA)
    return ctx.new_page(), d
