import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

db = SQLAlchemy()

def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    

    # Om DATABASE_URL finns (AWS), använd den. 
    # Annars, använd din lokala MySQL-adress.
    local_db = "mysql+pymysql://root:Password@localhost/gymshop"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", local_db)
    
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    #
    with app.app_context():
        from . import models  
        db.create_all()

    return app
