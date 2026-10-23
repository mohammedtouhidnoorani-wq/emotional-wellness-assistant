from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.chat import chat_bp
    from app.routes.mood import mood_bp
    from app.routes.assessment import assessment_bp
    from app.routes.mindfulness import mindfulness_bp
    from app.routes.trading import trading_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(mood_bp, url_prefix='/mood')
    app.register_blueprint(assessment_bp, url_prefix='/assessment')
    app.register_blueprint(mindfulness_bp, url_prefix='/mindfulness')
    app.register_blueprint(trading_bp, url_prefix='/trading')

    with app.app_context():
        db.create_all()
        from app.seed import seed_mindfulness_exercises
        seed_mindfulness_exercises()

    return app