import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from config import Config
from models import db, User, Task
from datetime import datetime
from models import db, Task, Category
from sqlalchemy import inspect, text

# ✅ Khởi tạo ứng dụng Flask
app = Flask(__name__)
app.config.from_object(Config)

# ✅ Gán app vào SQLAlchemy & Flask-Login
db.init_app(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ✅ Kiểm tra và thêm cột 'category_id' nếu chưa có
with app.app_context():
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('task')]

    if 'category_id' not in columns:
        with db.engine.connect() as connection:
            connection.execute(text("ALTER TABLE task ADD COLUMN category_id INTEGER"))
        print("✔️ Cột 'category_id' đã được thêm vào bảng 'task'.")

# ✅ Kiểm tra định dạng file hợp lệ (avatar)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 📌 Load user từ session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------------------------------------------------
# 🏠 Trang chủ (Hiển thị task của user hiện tại)
# --------------------------------------------------------------
@app.route('/')
@login_required
def index():
    category_id = request.args.get('category_id', type=int)  # ✅ Lấy category_id từ query params

    # ✅ Chỉ lấy danh mục mà user hiện tại có Task
    user_category_ids = db.session.query(Task.category_id).filter_by(user_id=current_user.id).distinct()
    categories = Category.query.filter(Category.id.in_(user_category_ids)).all()

    # ✅ Lọc Task theo danh mục của người dùng hiện tại
    if category_id:
        tasks = Task.query.filter_by(user_id=current_user.id, category_id=category_id).all()
    else:
        tasks = Task.query.filter_by(user_id=current_user.id).all()

    return render_template('index.html', tasks=tasks, categories=categories, selected_category=category_id)


# --------------------------------------------------------------
# 🔑 Đăng ký tài khoản
# --------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Kiểm tra user đã tồn tại chưa
        if User.query.filter_by(username=username).first():
            flash("Tài khoản đã tồn tại!", "danger")
            return redirect(url_for('register'))
        
        # Mã hóa mật khẩu và tạo user mới
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')

# --------------------------------------------------------------
# 🔐 Đăng nhập
# --------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user:
            if user.is_blocked:
                flash("Tài khoản của bạn đã bị chặn bởi Admin.", "danger")
                return redirect(url_for('login'))
            
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                flash("Đăng nhập thành công!", "success")
                return redirect(url_for('index'))
        
        flash("Đăng nhập không thành công. Vui lòng kiểm tra lại!", "danger")
    
    return render_template('login.html')

# --------------------------------------------------------------
# 🔓 Đăng xuất
# --------------------------------------------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Bạn đã đăng xuất thành công.", "success")
    return redirect(url_for('login'))

# --------------------------------------------------------------
# 📝 Quản lý Task của người dùng
# --------------------------------------------------------------
@app.route('/my_tasks')
@login_required
def my_tasks():
    category_id = request.args.get('category_id', type=int)

    # ✅ Chỉ lấy danh mục mà user hiện tại có Task
    user_category_ids = db.session.query(Task.category_id).filter_by(user_id=current_user.id).distinct()
    categories = Category.query.filter(Category.id.in_(user_category_ids)).all()

    # ✅ Lọc Task theo danh mục
    if category_id:
        tasks = Task.query.filter_by(user_id=current_user.id, category_id=category_id).all()
    else:
        tasks = Task.query.filter_by(user_id=current_user.id).all()

    return render_template('my_tasks.html', tasks=tasks, categories=categories, selected_category=category_id)


@app.route('/new_task', methods=['GET', 'POST'])
@login_required
def new_task():
    categories = Category.query.all()  # ✅ Lấy danh sách danh mục

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category_id = request.form.get('category_id')  # ✅ Lấy category_id từ form
        new_category_name = request.form.get('new_category')  # ✅ Lấy danh mục mới từ form

        # ✅ Nếu có danh mục mới, kiểm tra xem có tồn tại chưa, nếu chưa thì thêm vào
        if new_category_name:
            existing_category = Category.query.filter_by(name=new_category_name).first()
            if not existing_category:
                new_category = Category(name=new_category_name)
                db.session.add(new_category)
                db.session.commit()
                category_id = new_category.id  # Gán danh mục mới cho Task
            else:
                category_id = existing_category.id  # Dùng danh mục đã có

        # ✅ Tạo công việc mới với danh mục đã chọn hoặc mới tạo
        task = Task(
            title=title,
            description=description,
            category_id=category_id if category_id else None,  # ✅ Lưu category nếu có
            user_id=current_user.id
        )
        db.session.add(task)
        db.session.commit()
        flash("Hoạt động đã được tạo!", "success")
        return redirect(url_for('my_tasks'))
    
    return render_template('new_task.html', categories=categories)


@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("Bạn không có quyền chỉnh sửa!", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']

        # ✅ Kiểm tra deadline: Nếu trống, đặt thành None
        deadline_str = request.form['deadline']
        task.deadline = datetime.strptime(deadline_str, "%Y-%m-%d") if deadline_str else None

        db.session.commit()
        flash("Hoạt động đã được cập nhật!", "success")
        return redirect(url_for('my_tasks'))
    
    return render_template('edit_task.html', task=task)


@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("Bạn không có quyền xóa!", "danger")
        return redirect(url_for('index'))
    db.session.delete(task)
    db.session.commit()
    flash("Hoạt động đã được xóa!", "success")
    return redirect(url_for('my_tasks'))

# --------------------------------------------------------------
# 👤 Quản lý Avatar của User
# --------------------------------------------------------------
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        flash('Không có file nào được chọn!', 'danger')
        return redirect(url_for('profile'))

    file = request.files['avatar']
    
    if file.filename == '':
        flash('Vui lòng chọn một file hợp lệ!', 'danger')
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Cập nhật avatar của user
        current_user.avatar = filename
        db.session.commit()

        flash('Avatar đã được cập nhật thành công!', 'success')
    else:
        flash('File không hợp lệ. Chỉ chấp nhận PNG, JPG, JPEG, GIF!', 'danger')

    return redirect(url_for('profile'))

# --------------------------------------------------------------
# 🛠 Quản lý User (Admin)
# --------------------------------------------------------------
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash("Bạn không có quyền truy cập!", "danger")
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/toggle_block/<int:user_id>')
@login_required
def toggle_block(user_id):
    if not current_user.is_admin:
        flash("Bạn không có quyền thực hiện hành động này.", "danger")
        return redirect(url_for('admin'))

    user = User.query.get(user_id)
    if user:
        user.is_blocked = not user.is_blocked  # Toggle trạng thái block/unblock
        db.session.commit()
        flash(f"Người dùng {user.username} đã {'bị khóa' if user.is_blocked else 'được mở khóa'}.", "success")
    
    return redirect(url_for('admin'))

# --------------------------------------------------------------
# 🚀 Chạy ứng dụng
# --------------------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
