# Huff Curves BR Web Viewer

Static dashboard for the ANA empirical Huff curve outputs.

You can open `index.html` directly in a browser because `data/bootstrap.js`
embeds the compact station and curve data. Running a local server is still a
good option when sharing or testing.

Build compact browser assets from the current pipeline outputs:

```bash
python scripts/build_web_assets.py
```

Serve the viewer from the repository root:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/web/huff_viewer/
```
