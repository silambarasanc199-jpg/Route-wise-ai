"""Fast, offline checks for the deployable static frontend."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_frontend_has_responsive_accessible_shell_and_required_views():
    html=(ROOT/"frontend/index.html").read_text()
    css=(ROOT/"frontend/styles.css").read_text()
    for view in ("dashboard","deliveries","routes","reports"):
        assert f'id="page-{view}"' in html
    assert 'name="viewport"' in html
    assert 'aria-label="Main navigation"' in html
    assert "@media(max-width:560px)" in css


def test_frontend_calls_real_api_and_does_not_ship_seed_orders_or_secrets():
    js=(ROOT/"frontend/app.js").read_text()
    config=(ROOT/"frontend/config.js").read_text()
    assert 'api("/deliveries")' in js
    assert 'api("/routes/optimize"' in js
    assert 'api("/uploads/signature")' in js
    assert "No sample orders" in js
    assert "api_secret" not in config.lower()
    assert "apiBaseUrl: \"\"" in config


def test_dashboard_displays_each_delivery_status_and_priority_counts():
    html=(ROOT/"frontend/index.html").read_text()
    js=(ROOT/"frontend/app.js").read_text()
    for field in ("statPending", "statTransit", "statCompleted", "statDelayed", "statHighPriority"):
        assert f'id="{field}"' in html
    for value in ("d.pending", "d.in_transit", "d.completed", "d.delayed", "d.high_priority", "d.overdue"):
        assert value in js


def test_cloudinary_upload_rejects_provider_errors_and_reports_failure():
    js=(ROOT/"frontend/app.js").read_text()
    assert 'if(!response.ok)throw new Error(uploaded.error?.message' in js
    assert 'toast(`Proof upload failed: ${e.message}`,"error")' in js
