# iPhone Safari emulation for local QA. A width token is either plain CSS px or a device token:
#   402, 1440        plain desktop-style viewport (CSS px = the number), as before
#   402P / 440P      iPhone portrait:  isMobile, hasTouch, Safari UA, DPR 3, Safari page zoom (see below)
#   874L / 956L      iPhone landscape: same, width x height 874x402 / 956x440 points
#   956L@1           any device token with an explicit page zoom (1 = 100%)
# Pages set <meta viewport initial-scale=0.85> (2026-11-05): on a phone at 100% Safari zoom the layout is points / 0.85
# (360/402/440 portrait -> 424/473/518 CSS px; 874/956 landscape -> 1028/1125 CSS px, 956 = the >=1100px desktop layout).
# Chromium mobile emulation (isMobile) applies that meta like Safari does. ZOOM = Safari page zoom (aA menu) on top of it:
# default 1 (DT_ZOOM overrides; 0.85 reproduces the pre-meta setup Nicklaus used before 2026-11-05).
# Report device measurements in points (CSS px x 0.85 x zoom), which is what a screenshot of the phone shows.
import os
UA = ('Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) '
      'Version/18.0 Mobile/15E148 Safari/604.1')
SIZES = {'402P': (402, 874), '440P': (440, 956), '360P': (360, 780), '874L': (874, 402), '956L': (956, 440)}
ZOOM = float(os.environ.get('DT_ZOOM', '1'))

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
