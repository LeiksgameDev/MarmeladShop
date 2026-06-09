import os
from flask import Flask
from app.database import init_db
from app.security import csrf_token, init_security, validate_csrf
from app.services.admin_service import cleanup_old_orders
from app.services.auth_service import current_user


def create_app():
    app = Flask(__name__, instance_relative_config=True, template_folder='../templates', static_folder='../static')
    os.makedirs(app.instance_path, exist_ok=True)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024
    init_security(app)
    init_db()

    from app.routes.public import public_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    @app.before_request
    def before_request():
        validate_csrf()
        cleanup_old_orders()

    @app.context_processor
    def inject_globals():
        return {'user': current_user(), 'csrf_token': csrf_token}

    return app
