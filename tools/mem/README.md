# Memory checks (WebKit and Chromium)

Safari's engine is WebKit. Playwright's WebKit build cannot be downloaded in the sandbox (its CDN is not on the network
allowlist), so these use Ubuntu's WebKitGTK (2.52, same engine) through its WebDriver, on a virtual display.

One-time setup:
    apt-get install -y webkit2gtk-driver xvfb xauth
    pip install --break-system-packages selenium
    (fonts: see tools/realfonts.py header)
    Xvfb :99 -screen 0 1920x1200x24 &

Measure:
    bash tools/mem/mkbed.sh site /tmp/bed            # copy of a built site, Google Fonts pointed at local files, + blank.html
    (cd /tmp/bed && python3 -m http.server 8811 &)
    DISPLAY=:99 python3 tools/mem/wkmem.py http://localhost:8811/index.html 402 tab-lb tab-ro ...   # WebKit
    python3 tools/mem/chmem.py http://localhost:8811/index.html 402 tab-lb tab-ro ...                 # Chromium
    (blank.html in the same way = the browser's own baseline; the page's cost is the difference)

Figures are private memory (USS) of the web content / renderer process from /proc. The page is hosted in a same-origin
iframe of the exact width (MiniBrowser will not size its content below 447px); blank.html uses the same wrapper.
Run-to-run noise: about +-2 MB at 402, +-5 MB at 1440; take the median of two runs.
Absolute figures differ from Safari on macOS (Activity Monitor counts more, e.g. CoreText fonts); compare before/after.
