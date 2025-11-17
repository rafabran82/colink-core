from fastapi import FastAPI

# Create the FastAPI application instance
app = FastAPI(title="COLINK Core API", version="0.1.0")


@app.get("/health", tags=["core"])
def health_check():
    return {"status": "ok", "component": "colink_core"}


def run() -> None:
    """
    Legacy runner support (CLI-style), preserved from old main.py
    """
    print("colink_core.main.run() OK")


if __name__ == "__main__":
    # If invoked directly, print OK (legacy behavior)
    run()
