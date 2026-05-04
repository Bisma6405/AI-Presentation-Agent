"""
Main entry point for the AI Presentation Agent
Run with: streamlit run main.py
"""
import subprocess
import sys


def check_dependencies():
    """Check if required packages are installed"""
    required = ['streamlit', 'groq', 'python-pptx', 'requests', 'Pillow', 'python-dotenv']
    missing = []

    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)

    if missing:
        print("❌ Missing packages:", ', '.join(missing))
        print("📦 Installing missing packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("✅ Installation complete!")


if __name__ == "__main__":
    check_dependencies()
    print("🚀 Starting AI Presentation Agent...")
    print("📊 Opening in browser at http://localhost:8501")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])