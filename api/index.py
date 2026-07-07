from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import yaml
import os
from dotenv import load_dotenv

app = FastAPI()

# Allow exam page
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://exam.sanand.workers.dev"],
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# -----------------------------
# Defaults
# -----------------------------

config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# -----------------------------
# YAML
# -----------------------------

with open("config.development.yaml") as f:
    yaml_cfg = yaml.safe_load(f)

config.update(yaml_cfg)

# -----------------------------
# .env
# -----------------------------

if os.getenv("APP_PORT"):
    config["port"] = int(os.getenv("APP_PORT"))

if os.getenv("NUM_WORKERS"):
    config["workers"] = int(os.getenv("NUM_WORKERS"))

if os.getenv("APP_LOG_LEVEL"):
    config["log_level"] = os.getenv("APP_LOG_LEVEL")

if os.getenv("APP_API_KEY"):
    config["api_key"] = os.getenv("APP_API_KEY")

# -----------------------------
# OS ENV
# -----------------------------

if os.getenv("APP_DEBUG"):
    config["debug"] = os.getenv("APP_DEBUG").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def parse_bool(v):
    return str(v).lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


# -----------------------------
# Endpoint
# -----------------------------

@app.get("/effective-config")
def effective_config(
    set: List[str] = Query(default=[])
):

    result = config.copy()

    for item in set:

        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key == "port":
            result[key] = int(value)

        elif key == "workers":
            result[key] = int(value)

        elif key == "debug":
            result[key] = parse_bool(value)

        else:
            result[key] = value

    result["api_key"] = "****"

    return result


@app.get("/")
def root():
    return {"status": "running"}