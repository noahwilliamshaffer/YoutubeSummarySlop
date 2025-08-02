"""
Setup Script for YouTube Movie Automation System
Helps users quickly set up the project with all required configurations
"""

import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8+ is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = ["output", "temp", "temp/visuals", "temp/visuals/videos", 
                   "temp/visuals/images", "temp/visuals/backgrounds", "temp/visuals/transitions"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Directories created")

def setup_environment_file():
    """Set up environment file from template"""
    print("🔧 Setting up environment file...")
    
    if os.path.exists('.env'):
        print("⚠️  .env file already exists. Skipping...")
        return
    
    if os.path.exists('env.template'):
        shutil.copy('env.template', '.env')
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your API keys:")
        print("   - OPENAI_API_KEY")
        print("   - TMDB_API_KEY") 
        print("   - ELEVENLABS_API_KEY")
        print("   - PEXELS_API_KEY")
    else:
        print("❌ env.template not found")

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print("🎬 Checking FFmpeg installation...")
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found")
        print("📥 Please install FFmpeg:")
        print("   Windows: https://ffmpeg.org/download.html#build-windows")
        print("   macOS: brew install ffmpeg")
        print("   Linux: sudo apt install ffmpeg")
        return False

def display_setup_instructions():
    """Display final setup instructions"""
    print("\n🎯 Setup Instructions:")
    print("=" * 50)
    
    print("\n1. 📝 Edit .env file with your API keys:")
    print("   - Get OpenAI API key: https://platform.openai.com/api-keys")
    print("   - Get TMDb API key: https://www.themoviedb.org/settings/api")
    print("   - Get ElevenLabs API key: https://elevenlabs.io/")
    print("   - Get Pexels API key: https://www.pexels.com/api/")
    
    print("\n2. 🔑 Set up YouTube API credentials:")
    print("   - Go to: https://console.cloud.google.com/")
    print("   - Create a new project or select existing")
    print("   - Enable YouTube Data API v3")
    print("   - Create OAuth 2.0 credentials")
    print("   - Download credentials.json to project root")
    
    print("\n3. 🚀 Run the system:")
    print("   - Test: python main.py test")
    print("   - Single run: python main.py once")
    print("   - Scheduled: python main.py schedule")
    
    print("\n4. 📊 Monitor:")
    print("   - Check automation.log for detailed logs")
    print("   - Videos will be saved in output/ directory")
    print("   - Temporary files in temp/ directory")
    
    print("\n🎉 Setup complete! Happy automating!")

def main():
    """Main setup function"""
    print("🎬 YouTube Movie Automation Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Setup environment file
    setup_environment_file()
    
    # Check FFmpeg
    ffmpeg_ok = check_ffmpeg()
    
    # Display instructions
    display_setup_instructions()
    
    if not ffmpeg_ok:
        print("\n⚠️  Please install FFmpeg before running the system")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1) 