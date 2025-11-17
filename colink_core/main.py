from fastapi import FastAPI
import os

# Create the FastAPI application instance
app = FastAPI(title="COLINK Core API", version="0.1.0")


@app.get("/health", tags=["core"])
def health_check():
    return {"status": "ok", "component": "colink_core"}


@app.get("/version", tags=["core"])
def version():
    """
    Returns the COLINK Core API version.
    """
    return {
        "version": app.version,
        "name": app.title,
        "env": os.environ.get("COLINK_ENV", "dev"),
    }


@app.get("/config", tags=["core"])
def get_config():
    """
    Expose basic configuration info for dashboard + simulation integration.
    Extend this later with XRPL + COL/COPX metadata.
    """
    return {
        "app": app.title,
        "version": app.version,
        "environment": os.environ.get("COLINK_ENV", "dev"),
        "xrpl_network": os.environ.get("XRPL_NETWORK", "testnet"),
        "sim_mode": os.environ.get("SIM_MODE", "local"),
    }


@app.get("/status", tags=["core"])
def get_status():
    """
    Operational status endpoint — expands later with XRPL, pools, metrics, etc.
    """
    return {
        "status": "operational",
        "module": "colink_core",
        "xrpl_network": os.environ.get("XRPL_NETWORK", "testnet"),
        "ci_mode": os.environ.get("CI_MODE", "off"),
    }


def run() -> None:
    """
    Legacy runner support (CLI-style), preserved from old main.py
    """
    print("colink_core.main.run() OK")


if __name__ == "__main__":
    # If invoked directly, print OK (legacy behavior)
    run()
