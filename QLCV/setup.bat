@echo off
echo ============================
echo  🚀 To-Do List App Setup
echo ============================
echo.

:: ✅ Kiểm tra và tạo Virtual Environment nếu chưa có
if not exist venv (
    echo 🔹 Creating virtual environment...
    python -m venv venv
) else (
    echo 🔹 Virtual environment already exists.
)

:: ✅ Kích hoạt Virtual Environment
call venv\Scripts\activate

:: ✅ Cập nhật pip
echo 🔹 Updating pip...
python -m pip install --upgrade pip

:: ✅ Cài đặt thư viện trong `requirements.txt`
echo 🔹 Installing dependencies...
pip install -r requirements.txt

:: ✅ Kiểm tra thư mục database `instance/`
if not exist instance (
    mkdir instance
)

:: ✅ Khởi tạo và cập nhật database (Flask-Migrate)
echo 🔹 Setting up database...
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

:: ✅ Chạy ứng dụng Flask
echo 🔹 Running Flask App...
flask run

:: Giữ cửa sổ mở nếu có lỗi
echo.
echo ============================
echo ✅ Setup Completed! Running App...
echo ============================
pause
