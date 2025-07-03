"""
Script untuk membuat executable (.exe) dari Discord Auto Messenger
Jalankan script ini untuk membuat file .exe yang bisa dijalankan tanpa Python
"""

import os
import subprocess
import sys

def install_pyinstaller():
    """Install PyInstaller jika belum terinstall"""
    try:
        import PyInstaller
        print("✅ PyInstaller sudah terinstall")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller berhasil diinstall")

def create_launcher_script():
    """Buat script launcher untuk menjalankan web server"""
    launcher_content = '''
import os
import sys
import webbrowser
import time
import threading
from pathlib import Path

# Add the web directory to Python path
web_dir = Path(__file__).parent / "web"
sys.path.insert(0, str(web_dir))

def start_server():
    """Start the Flask server"""
    os.chdir(web_dir)
    from server import app
    app.run(host='127.0.0.1', port=8000, debug=False)

def open_browser():
    """Open browser after server starts"""
    time.sleep(2)  # Wait for server to start
    webbrowser.open('http://localhost:8000')

if __name__ == "__main__":
    print("🚀 Starting Discord Auto Messenger...")
    print("📡 Server akan berjalan di: http://localhost:8000")
    
    # Start browser in separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start server
    try:
        start_server()
    except KeyboardInterrupt:
        print("\\n🛑 Server dihentikan")
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Tekan Enter untuk keluar...")
'''
    
    with open('discord_auto_messenger_launcher.py', 'w') as f:
        f.write(launcher_content)
    print("✅ Launcher script dibuat: discord_auto_messenger_launcher.py")

def build_executable():
    """Build executable menggunakan PyInstaller"""
    print("🔨 Building executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window (optional)
        "--name=DiscordAutoMessenger",  # Executable name
        "--add-data=web;web",          # Include web directory
        "--add-data=messages.txt;.",   # Include messages.txt
        "--add-data=info.txt;.",       # Include info.txt
        "--add-data=requirements.txt;.", # Include requirements.txt
        "discord_auto_messenger_launcher.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Executable berhasil dibuat!")
        print("📁 File executable ada di: dist/DiscordAutoMessenger.exe")
        print("\n🎯 Cara menggunakan:")
        print("1. Copy folder 'dist' ke komputer target")
        print("2. Double-click DiscordAutoMessenger.exe")
        print("3. Browser akan otomatis terbuka ke http://localhost:8000")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error building executable: {e}")
        return False
    
    return True

def create_batch_file():
    """Buat batch file untuk menjalankan aplikasi"""
    batch_content = '''@echo off
echo 🚀 Starting Discord Auto Messenger...
echo 📡 Server akan berjalan di: http://localhost:8000
echo.
cd /d "%~dp0"
python web/server.py
pause
'''
    
    with open('start_discord_messenger.bat', 'w') as f:
        f.write(batch_content)
    print("✅ Batch file dibuat: start_discord_messenger.bat")

def main():
    print("🔧 Discord Auto Messenger - Build Executable")
    print("=" * 50)
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Create launcher script
    create_launcher_script()
    
    # Create batch file alternative
    create_batch_file()
    
    # Build executable
    success = build_executable()
    
    if success:
        print("\n🎉 Build selesai!")
        print("\n📋 Pilihan untuk menjalankan aplikasi:")
        print("1. 🖥️  Executable: dist/DiscordAutoMessenger.exe")
        print("2. 📄 Batch file: start_discord_messenger.bat")
        print("3. 🐍 Python: python web/server.py")
        
        print("\n📦 Untuk distribusi:")
        print("- Copy seluruh folder 'dist' ke komputer target")
        print("- Tidak perlu install Python di komputer target")
        print("- Double-click DiscordAutoMessenger.exe untuk menjalankan")
    else:
        print("\n❌ Build gagal. Coba jalankan manual:")
        print("python web/server.py")

if __name__ == "__main__":
    main()
