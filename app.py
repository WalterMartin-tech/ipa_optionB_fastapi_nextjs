from backend.app import app  # re-export the FastAPI instance

# Optional debug handler (only active if DEBUG_ERRORS=1 and debug_errors.py exists)
try:
    from debug_errors import setup as setup_debug  # root helper
    setup_debug(app)
except Exception:
    pass
