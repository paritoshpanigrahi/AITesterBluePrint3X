import multiprocessing
import os
import sys

if __name__ == "__main__":
    multiprocessing.freeze_support()
    port = int(os.getenv("PORT", "8765"))
    from backend.app import app
    import uvicorn
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    except (KeyboardInterrupt, SystemExit):
        pass
