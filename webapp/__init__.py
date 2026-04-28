from pathlib import Path
from flask import Flask

from .routes import bp


def create_app() -> Flask:
    # 显式指定模板/静态目录，避免后续改包结构时路径漂移
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
        static_url_path="/static",
    )
    app.register_blueprint(bp)
    return app

