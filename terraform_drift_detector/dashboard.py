from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .storage import ScanStore


def create_app(db_path: Path) -> FastAPI:
    app = FastAPI(title="Terraform Drift Detector")
    store = ScanStore(db_path)

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        return """
        <!doctype html>
        <html>
          <head>
            <title>Terraform Drift Detector</title>
            <style>
              body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2937; }
              table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
              th, td { border-bottom: 1px solid #d1d5db; padding: .6rem; text-align: left; }
              .counts { display: flex; gap: .75rem; flex-wrap: wrap; }
              .count { border: 1px solid #d1d5db; border-radius: 6px; padding: .75rem 1rem; }
              code { background: #f3f4f6; padding: .1rem .3rem; border-radius: 4px; }
            </style>
          </head>
          <body>
            <h1>Terraform Drift Detector</h1>
            <div id="app">Loading...</div>
            <script>
              async function load() {
                const latest = await fetch('/api/latest').then(r => r.json());
                if (!latest) {
                  document.getElementById('app').innerHTML = '<p>No scans stored yet.</p>';
                  return;
                }
                const s = latest.summary;
                const rows = latest.findings.map(f => `
                  <tr>
                    <td>${f.kind}</td><td><code>${f.name || ''}</code></td>
                    <td>${f.resource_type || ''}</td><td>${f.diffs.length}</td>
                  </tr>`).join('');
                document.getElementById('app').innerHTML = `
                  <p>Latest scan: <code>${latest.scan_id}</code></p>
                  <div class="counts">
                    <div class="count">Expected<br><strong>${s.total_expected}</strong></div>
                    <div class="count">Actual<br><strong>${s.total_actual}</strong></div>
                    <div class="count">Missing<br><strong>${s.missing}</strong></div>
                    <div class="count">Modified<br><strong>${s.modified}</strong></div>
                    <div class="count">Tag drift<br><strong>${s.tag_drift}</strong></div>
                    <div class="count">Unmanaged<br><strong>${s.unmanaged}</strong></div>
                  </div>
                  <table><thead><tr><th>Kind</th><th>Name</th><th>Type</th><th>Diffs</th></tr></thead><tbody>${rows}</tbody></table>
                `;
              }
              load();
            </script>
          </body>
        </html>
        """

    @app.get("/api/latest")
    def latest() -> dict | None:
        return store.latest()

    @app.get("/api/scans")
    def scans(limit: int = 20) -> list[dict]:
        return store.list_scans(limit)

    return app
