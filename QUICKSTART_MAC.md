# 🚀 Quick Start Guide for Mac

## Prerequisites
- macOS 10.15+ (Catalina or newer)
- Python 3.8+ (usually pre-installed on modern macOS)
- Git (for cloning the repository)

## 🏃‍♂️ One-Command Setup

Clone the repository and run the setup script:

```bash
# If you haven't cloned yet
git clone <your-repository-url>
cd <your-repository-name>

# Run the automated setup
./setup_mac.sh
```

The setup script will:
- ✅ Check Python installation
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Optionally install Ollama (local AI)
- ✅ Create test files
- ✅ Set up launch script

## 🎯 Launch the Application

After setup, launch the AI File Organizer:

```bash
./run_organizer.sh
```

Or manually:
```bash
source venv/bin/activate
python3 ai_file_organizer.py
```

## 🧪 Testing with Sample Files

1. **Launch the application**
2. **Select the `test_files` folder** (created by setup script)
3. **Click "Analyze Structure"** to understand the folder
4. **Configure AI backend:**
   - For Ollama: Select "Local (Ollama)" and "llama3.1" model
   - For OpenAI: Enter your API key
5. **Click "Scan with AI"** to see AI suggestions
6. **Review suggestions** and click "Organize" to test

## 🤖 AI Backend Options

### Option 1: Ollama (Recommended for beginners)
- **Pros**: Free, private, works offline
- **Setup**: Automatically installed by setup script
- **Usage**: Select "Local (Ollama)" backend

### Option 2: OpenAI
- **Pros**: High accuracy, reliable
- **Setup**: Get API key from [OpenAI](https://platform.openai.com)
- **Usage**: Enter API key in the application

### Option 3: Grok
- **Pros**: Alternative to OpenAI
- **Setup**: Get API key from [xAI](https://console.x.ai)
- **Usage**: Enter API key in the application

## 🔧 Manual Setup (if script fails)

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Ollama (optional)
brew install ollama
ollama pull llama3.1

# 4. Run application
python3 ai_file_organizer.py
```

## 🐛 Troubleshooting

### Python Issues
```bash
# Check Python version (should be 3.8+)
python3 --version

# If Python not found, install from python.org
# or use Homebrew: brew install python
```

### Ollama Issues
```bash
# Check if Ollama is running
pgrep -f ollama

# Start Ollama manually
ollama serve

# Pull model if missing
ollama pull llama3.1
```

### Permission Issues
```bash
# Make scripts executable
chmod +x setup_mac.sh run_organizer.sh

# Fix Python path issues
which python3
```

### Virtual Environment Issues
```bash
# Remove and recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📱 GUI Features Overview

1. **Select Folder**: Choose directory to organize
2. **Analyze Structure**: Understand existing organization
3. **AI Backend**: Choose Ollama/OpenAI/Grok
4. **Test Connection**: Verify AI is working
5. **Scan with AI**: Get intelligent suggestions
6. **Review & Organize**: Check suggestions and organize files

## 🎯 Best Practices

1. **Start Small**: Test with a few files first
2. **Analyze Structure**: Always analyze before scanning
3. **Review Suggestions**: Check AI suggestions before organizing
4. **Backup Important Files**: Test with copies first
5. **Use Contextual Prompts**: Enable for better suggestions

## 📞 Getting Help

- Check the main `README.md` for detailed documentation
- Look at the `test_files` folder for examples
- Use the "Test" button to verify AI connection
- Enable "Show Structure Analysis" to understand folder patterns

## 🎉 You're Ready!

The AI File Organizer should now be running on your Mac. Start with the test files, then try it on your own folders. Happy organizing! 🗂️