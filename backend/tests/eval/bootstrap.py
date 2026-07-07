# Eval bootstrap - a minimal Flask app on the REAL dev database.
# The offline harness's test database is deliberately NOT used here:
# real play logs are the corpus this tool exists to measure
# (reset_db.py precedent - dev-database tools build their own app).

import os

from flask import Flask


def build_dev_app() -> Flask:
    """A Flask app with ONLY the dev database configured - no routes,
    no LLM load, no ComfyUI check"""

    # Importing backend loads .env (backend/__init__.py calls load_dotenv)
    from backend.models.core import init_db

    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '')}"
        f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}"
        f"/{os.getenv('DB_NAME', 'monster_hunter_game')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    init_db(app)

    # GenerationLog declares its child relationships by NAME ('LLMLog',
    # 'ImageLog') - the mapper can only resolve them once those classes
    # are imported (reset_db.py's import_all_models precedent)
    from backend.models.image_log import ImageLog  # noqa: F401
    from backend.models.llm_log import LLMLog  # noqa: F401

    return app


def start_ai_queue(app):
    """Wire the singleton AI queue to this app (its worker auto-starts).
    Replay-only: report never generates anything.

    The local provider self-loads the GGUF on the first request, INSIDE
    this process - run replay with the game backend stopped (one GPU,
    one model), or switch the settings panel to a cloud provider first."""

    from backend.ai.queue import get_ai_queue

    queue = get_ai_queue()
    queue.set_flask_app(app)
    return queue
