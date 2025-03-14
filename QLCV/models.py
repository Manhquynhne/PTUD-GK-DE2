from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()  # ✅ Không truyền app ở đây

# Model danh mục công việc
class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    tasks = db.relationship('Task', backref='category', lazy=True)


# 📌 Model Người dùng (User)
class User(UserMixin, db.Model):
    __tablename__ = "user"  # ✅ Định danh bảng tránh xung đột
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    avatar = db.Column(db.String(255), default="default_avatar.png")  
    tasks = db.relationship('Task', backref='user', lazy=True)

# Model công việc (Task)
class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)  # ✅ Đảm bảo có cột này
