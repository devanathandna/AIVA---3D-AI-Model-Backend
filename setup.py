"""
Quick setup script for Chopper AI Agent with Audio Features
"""
import os
import sys
import subprocess
import shutil

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description} found")
        return True
    else:
        print(f"❌ {description} not found: {filepath}")
        return False

def main():
    """Main setup function"""
    print_header("Chopper AI Agent - Audio Setup")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")
    
    # Check required files
    print_header("Checking Project Structure")
    
    required_files = [
        ("requirements.txt", "Requirements file"),
        (".env.example", "Environment template"),
        ("main.py", "Main application"),
        ("audio/stt.py", "STT processor"),
        ("audio/tts.py", "TTS processor"),
        ("config/api_keys.py", "API key manager")
    ]
    
    all_files_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_files_exist = False
    
    if not all_files_exist:
        print("❌ Missing required files. Please ensure you're in the correct directory.")
        return False
    
    # Install dependencies
    print_header("Installing Dependencies")
    
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        print("❌ Failed to install dependencies. Please check your pip installation.")
        return False
    
    # Check for .env file
    print_header("Environment Configuration")
    
    if not os.path.exists(".env"):
        print("📝 Creating .env file from template...")
        try:
            shutil.copy(".env.example", ".env")
            print("✅ .env file created from template")
            print("\n⚠️  IMPORTANT: Please edit .env with your API keys before starting the server!")
            print("\nRequired API Keys:")
            print("- 1 Deepgram STT API key")
            print("- 5 Gemini TTS API keys") 
            print("- 5 Gemini AI API keys")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("✅ .env file already exists")
    
    # Check API keys configuration
    print_header("API Key Validation")
    
    try:
        with open(".env", "r") as f:
            env_content = f.read()
        
        # Count configured keys
        deepgram_key = len([line for line in env_content.split('\n') if line.startswith('DEEPGRAM_API_KEY') and '=' in line and line.split('=')[1].strip()])
        gemini_tts_keys = len([line for line in env_content.split('\n') if line.startswith('GEMINI_TTS_API_KEY_') and '=' in line and line.split('=')[1].strip()])
        gemini_ai_keys = len([line for line in env_content.split('\n') if line.startswith('GEMINI_AI_API_KEY_') and '=' in line and line.split('=')[1].strip()])
        
        print(f"📊 API Key Configuration:")
        print(f"   - Deepgram STT key: {'1/1' if deepgram_key > 0 else '0/1'}")
        print(f"   - Gemini TTS keys: {gemini_tts_keys}/5") 
        print(f"   - Gemini AI keys: {gemini_ai_keys}/5")
        print(f"   - Total: {deepgram_key + gemini_tts_keys + gemini_ai_keys}/11")
        
        if deepgram_key == 0 and gemini_tts_keys == 0 and gemini_ai_keys == 0:
            print("\n⚠️  No API keys configured yet. Please add your keys to .env")
        elif deepgram_key == 0 or gemini_tts_keys < 5 or gemini_ai_keys < 5:
            print("\n⚠️  Not all API keys configured. For optimal performance, configure all keys.")
        else:
            print("\n✅ All API keys configured!")
            
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
    
    # Test import dependencies
    print_header("Testing Dependencies")
    
    test_imports = [
        ("fastapi", "FastAPI framework"),
        ("deepgram", "Deepgram SDK"),
        ("google.generativeai", "Google Generative AI"),
        ("websockets", "WebSocket support"),
        ("chromadb", "ChromaDB vector database")
    ]
    
    all_imports_work = True
    for module, description in test_imports:
        try:
            __import__(module)
            print(f"✅ {description} imported successfully")
        except ImportError:
            print(f"❌ {description} import failed - please check installation")
            all_imports_work = False
    
    if not all_imports_work:
        print("\n❌ Some dependencies failed to import. Please run 'pip install -r requirements.txt' again.")
        return False
    
    # Final instructions
    print_header("Setup Complete!")
    
    print("🎉 Chopper AI Agent setup completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Edit .env file with your API keys")
    print("2. Start the server: python main.py")
    print("3. Test audio features: python audio_client_example.py")
    print("4. Access documentation: http://localhost:8000/docs")
    print("\n🔗 Useful URLs:")
    print("- Health Check: http://localhost:8000/")
    print("- Audio Info: http://localhost:8000/audio/info")
    print("- Key Status: http://localhost:8000/admin/api-keys/status")
    print("\n🎵 Audio Features:")
    print("- STT: Deepgram Nova-2 with single API key")
    print("- TTS: Gemini TTS with 5-key rotation")
    print("- AI: Gemini 2.5 Flash with 5-key rotation")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)