# Enhanced AI File Organizer

A sophisticated file organization tool that uses AI to intelligently categorize and organize files based on their context, project structure, and content. This enhanced version addresses the limitations of basic file organizers by providing context-aware suggestions and better path recommendations.

## 🚀 Key Improvements Over Basic Organizers

### 1. **Context-Aware Path Suggestions**
- Analyzes existing folder structure to understand organization patterns
- Considers project type (Python, Node.js, Go, Rust, etc.)
- Examines sibling files for better categorization
- Detects folder naming conventions (kebab-case, snake_case, etc.)

### 2. **Enhanced AI Integration**
- Multiple AI backends: Local (Ollama), OpenAI, Grok
- Optimized prompts for each backend
- Better response parsing and validation
- Retry logic with exponential backoff

### 3. **Smart Project Detection**
- Automatically detects project types based on root files
- Provides project-specific organization guidelines
- Adapts suggestions to existing project structure
- Supports various development frameworks

### 4. **Advanced File Analysis**
- Comprehensive file categorization (code, config, docs, media, etc.)
- Content-based file type detection
- File size and metadata analysis
- Dependency and relationship detection

## 📋 Features

### Core Features
- **Multi-AI Backend Support**: Ollama (local), OpenAI, Grok
- **Context-Aware Organization**: Considers file location and project structure
- **Smart Grouping**: Groups related files together
- **Project Type Detection**: Automatically identifies project frameworks
- **Enhanced UI**: Improved interface with context display
- **Batch Processing**: Process multiple files concurrently
- **Export Capabilities**: Export organization plans to CSV

### Advanced Features
- **Two-Pass Refinement**: Initial suggestion + refinement for better accuracy
- **Structure-Aware Adjustments**: Adapts to existing folder patterns
- **Caching System**: Remembers previous decisions for efficiency
- **Error Handling**: Robust error handling and recovery
- **Progress Tracking**: Real-time progress updates
- **Logging**: Detailed logs for debugging and analysis

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- For local AI: [Ollama](https://ollama.ai/) installed and running
- For cloud AI: API keys for OpenAI or Grok

### Install Dependencies
```bash
pip install -r requirements.txt
```

### For Windows Users
If you encounter issues with `python-magic`, install the Windows version:
```bash
pip install python-magic-bin
```

## 🚀 Usage

### Basic Usage
```bash
python ai_file_organizer.py
```

### Step-by-Step Guide

1. **Launch the Application**
   - Run the script to open the GUI
   - The interface will show connection options and settings

2. **Configure AI Backend**
   - Select your preferred AI backend (Local/Ollama, OpenAI, or Grok)
   - For local: Choose an Ollama model (llama3.1, codellama, etc.)
   - For cloud: Enter your API key and select a model

3. **Test Connection**
   - Click "Test" to verify your AI backend is working
   - Ensure you get a successful connection message

4. **Select Folder**
   - Click "Select Folder" to choose the directory to organize
   - The app will analyze the folder structure automatically

5. **Configure Options**
   - **Use Context**: Enable to consider file context and project structure
   - **Consider Structure**: Adapt suggestions to existing folder patterns
   - **Smart Grouping**: Group related files together
   - **Refine Suggestions**: Use two-pass AI for better accuracy

6. **Scan with AI**
   - Click "Scan with AI" to analyze all files
   - Watch the progress as files are processed
   - Review suggestions in the tree view

7. **Review and Organize**
   - Check the suggested paths for each file
   - Use "Select All" or manually select files
   - Click "Organize" to move files to their suggested locations

## 🔧 Configuration Options

### AI Backend Settings
- **Local (Ollama)**: Fast, private, no API costs
- **OpenAI**: High quality, requires API key
- **Grok**: xAI's model, requires API key

### Organization Options
- **Use Context**: Consider file location and project structure
- **Consider Structure**: Adapt to existing folder naming patterns
- **Smart Grouping**: Group related files together
- **Refine Suggestions**: Use two-pass AI for better accuracy

### Advanced Settings
- **Cache Management**: Clear cache for fresh AI suggestions
- **Export Options**: Export organization plans to CSV
- **Logging**: Detailed logs for debugging

## 📁 Supported Project Types

The organizer automatically detects and provides specialized organization for:

### Development Projects
- **Python**: src/, tests/, docs/, config/
- **Node.js**: src/, lib/, test/, docs/
- **Go**: cmd/, pkg/, internal/, test/
- **Rust**: src/, tests/, examples/, docs/
- **Java (Maven/Gradle)**: src/main/, src/test/, docs/
- **Terraform**: terraform/, modules/, environments/

### General Organization
- **Documents**: docs/, reports/, presentations/
- **Media**: images/, audio/, video/, assets/
- **Archives**: backups/, old/, archive/
- **Configuration**: config/, settings/, env/

## 🎯 File Categories

The organizer recognizes and categorizes:

### Code Files
- Source code (.py, .js, .java, .cpp, .go, .rs, etc.)
- Configuration files (.json, .yaml, .toml, .env)
- Documentation (.md, .txt, .rst, .pdf)
- Scripts and executables

### Media Files
- Images (.jpg, .png, .gif, .svg, etc.)
- Audio (.mp3, .wav, .flac, etc.)
- Video (.mp4, .avi, .mov, etc.)

### Project Files
- Build files (Makefile, Dockerfile, etc.)
- Dependencies (requirements.txt, package.json, etc.)
- Version control (.gitignore, .gitattributes)

## 🔍 How It Works

### 1. Project Analysis
The organizer starts by analyzing the selected folder:
- Detects project type based on root files
- Analyzes existing folder structure
- Identifies naming conventions
- Maps file relationships

### 2. Context Extraction
For each file, it extracts comprehensive context:
- File type and category
- Current location and depth
- Sibling files and relationships
- Project-specific patterns

### 3. AI Processing
The AI receives detailed prompts including:
- File information and context
- Project type and guidelines
- Existing structure patterns
- Smart grouping rules

### 4. Response Processing
AI responses are processed and validated:
- Path extraction and cleaning
- Structure-aware adjustments
- Validation and fallbacks
- Optional refinement pass

### 5. Organization
Files are moved to their suggested locations:
- Creates necessary directories
- Handles naming conflicts
- Preserves file relationships
- Provides progress feedback

## 🐛 Troubleshooting

### Common Issues

**Ollama Connection Failed**
- Ensure Ollama is running: `ollama serve`
- Check if models are installed: `ollama list`
- Install a model: `ollama pull llama3.1`

**OpenAI/Grok API Errors**
- Verify your API key is correct
- Check your account has sufficient credits
- Ensure the model name is correct

**File Permission Errors**
- Run with appropriate permissions
- Check folder write access
- Ensure files aren't locked by other processes

**Poor AI Suggestions**
- Enable "Use Context" and "Consider Structure"
- Try different AI models
- Use "Refine Suggestions" for better accuracy
- Clear cache and rescan

### Debug Mode
Enable detailed logging by checking the console output or temp log files in your system's temp directory.

## 📊 Performance Tips

### For Large Folders
- Use local Ollama for faster processing
- Disable "Refine Suggestions" for speed
- Process in smaller batches
- Use SSD storage for better I/O

### For Better Accuracy
- Enable all context options
- Use higher-quality AI models
- Enable refinement for complex projects
- Provide clear project structure

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional AI backend support
- More project type detectors
- Enhanced file type recognition
- UI/UX improvements
- Performance optimizations

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Built with Python and Tkinter
- AI integration with Ollama, OpenAI, and Grok
- File type detection with python-magic
- Inspired by the need for intelligent file organization

---

**Note**: This enhanced version significantly improves upon basic file organizers by providing context-aware, AI-powered organization that considers your project structure and file relationships.