from webapp import create_app
from generator.config import load_config

_cfg = load_config()
app = create_app()

if __name__ == '__main__':
    app.run(host=_cfg.get('host', '0.0.0.0'), port=_cfg.get('port', 5200), debug=_cfg.get('debug', False))
