import os

class Config:
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASEDIR, 'instance', 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "your_secret_key"
    
    # Cấu hình thư mục lưu Avatar
    UPLOAD_FOLDER = os.path.join(BASEDIR, 'static/uploads/avatars')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
