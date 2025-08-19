# AI File Organizer - Enhanced Version

An intelligent file organization tool that uses AI (Local Ollama, OpenAI, or Grok) to suggest optimal folder structures based on file content, context, and existing organization patterns.

## 🚀 Key Improvements Over Original Version

### 1. **Context-Aware AI Suggestions**
- Analyzes existing folder structure to understand organization patterns
- Provides contextual information to AI models for better suggestions
- Considers file type, size, parent directory, and existing folders

### 2. **Enhanced AI Integration**
- Support for multiple AI backends (Ollama, OpenAI, Grok)
- Improved prompt engineering for more accurate path suggestions
- Better parsing and validation of AI responses
- Confidence scoring for AI suggestions

### 3. **Smart Folder Structure Analysis**
- Automatically detects existing organization patterns
- Identifies common folder types (documents, images, code, etc.)
- Provides structure insights before scanning
- Respects existing naming conventions

### 4. **Advanced Features**
- Two-pass refinement for better accuracy
- Batch processing with progress tracking
- Enhanced file type detection with size information
- Terraform-specific handling for infrastructure projects
- Caching system to avoid re-processing files

## 📋 Features

- **AI-Powered Organization**: Uses local or cloud AI to suggest folder paths
- **Context Awareness**: Analyzes existing folder structure for better suggestions
- **Multiple AI Backends**: Supports Ollama (local), OpenAI, and Grok
- **Smart Path Extraction**: Robust parsing of AI responses
- **Confidence Scoring**: Shows how confident the AI is about each suggestion
- **Two-Pass Refinement**: Optional second pass to improve suggestions
- **Project Detection**: Recognizes different project types (Git, Node.js, Python, etc.)
- **Terraform Support**: Special handling for infrastructure files
- **Batch Operations**: Process multiple files efficiently
- **Export Capabilities**: Export organization plans to CSV
- **Undo-Safe**: Preview before organizing, with detailed status tracking

## 🛠️ Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up AI Backend** (choose one):

   **Option A: Local Ollama (Recommended)**
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama3.1  # or your preferred model
   ```

   **Option B: OpenAI**
   - Get API key from https://platform.openai.com
   - Enter key in the application

   **Option C: Grok (xAI)**
   - Get API key from https://console.x.ai
   - Enter key in the application

## 🚀 Usage

### Basic Usage
```bash
python ai_file_organizer.py
```

### Step-by-Step Guide

1. **Select Folder**: Choose the directory you want to organize
2. **Analyze Structure**: Click "Analyze Structure" to understand existing organization
3. **Configure AI**: Select backend, model, and enter API key if needed
4. **Test Connection**: Verify AI connection works
5. **Scan with AI**: Let AI suggest folder paths for each file
6. **Review Suggestions**: Check AI suggestions and confidence scores
7. **Organize**: Select files and choose destination for organization

### Configuration Options

- **Analyze existing structure**: Understand current folder organization
- **Use contextual AI prompts**: Include folder context in AI requests
- **Refine suggestions (two-pass)**: Use AI refinement for better accuracy
- **Stay under root**: Keep organized files under project root
- **Pin Terraform**: Force Terraform files to infrastructure folder
- **Prefer folder move**: Move entire folders when beneficial

## 🎯 AI Prompt Engineering

The enhanced version uses sophisticated prompts that include:

- File information (name, type, size, parent directory)
- Existing folder structure and patterns
- Root folder context
- Project type detection
- Consistency with similar files

Example contextual prompt:
```
File to organize: project_report.pdf
File info: Type=Document; Size=2.3MB; Name=project_report.pdf; Parent=downloads
Target folder context: documents, reports, presentations | Folder patterns: documents: docs, documents; images: photos, images
Root folder: MyProject

Provide a folder path (1-3 levels max) that fits the existing organization pattern.
Use existing folder names when appropriate, or create logical new ones.
Format: ParentFolder/SubFolder (use forward slashes, no extra text)
```

## 🔧 Advanced Features

### Structure Analysis
- Detects existing folder patterns
- Maps common file types to folders
- Calculates folder depth and organization complexity
- Provides insights into current organization

### Confidence Scoring
- **High**: Clear, specific AI responses with logical paths
- **Medium**: Reasonable responses with some ambiguity
- **Low**: Uncertain or generic responses

### Smart Path Extraction
- Removes verbose AI explanations
- Handles various response formats
- Validates folder name legality
- Limits path depth (max 3 levels)

### Project-Aware Organization
- Git repositories
- Node.js projects (package.json)
- Python projects (pyproject.toml)
- Go modules (go.mod)
- Terraform projects (main.tf)

## 📊 Comparison with Original

| Feature | Original | Enhanced |
|---------|----------|----------|
| File Detection | libmagic | AI + context analysis |
| Organization Logic | Fixed categories | Dynamic AI suggestions |
| Context Awareness | None | Full folder structure analysis |
| Customization | Limited | Highly configurable |
| Accuracy | Basic type matching | AI-powered with refinement |
| Project Support | None | Multiple project types |
| Preview | Basic list | Detailed with confidence |
| Batch Processing | Simple | Advanced with progress |

## 🤖 AI Backend Comparison

| Backend | Pros | Cons | Best For |
|---------|------|------|----------|
| **Ollama** | Free, private, fast | Requires local setup | Privacy-conscious users |
| **OpenAI** | High accuracy, reliable | Costs money, requires internet | Best accuracy |
| **Grok** | Good performance | Newer, limited availability | Alternative to OpenAI |

## 🔍 Troubleshooting

### Common Issues

1. **AI Connection Failed**
   - Ollama: Ensure Ollama is running (`ollama serve`)
   - OpenAI/Grok: Check API key validity
   - Check internet connection for cloud APIs

2. **Poor AI Suggestions**
   - Enable "Analyze existing structure"
   - Use "Contextual AI prompts"
   - Try two-pass refinement
   - Check if folder has existing organization

3. **Slow Performance**
   - Reduce number of files
   - Use local Ollama instead of cloud APIs
   - Disable two-pass refinement for speed

### Performance Tips
- Analyze structure before scanning for better context
- Use caching to avoid re-processing files
- Process in smaller batches for large folders
- Enable two-pass only for important organization tasks

## 📝 Export and Logging

- Export organization plans to CSV
- Detailed logging of AI responses
- Temporary scan logs for debugging
- Structure analysis reports

## 🔒 Privacy and Security

- **Local Ollama**: Complete privacy, no data leaves your machine
- **Cloud APIs**: File names and basic info sent to AI services
- **No File Content**: Only metadata is sent, never file contents
- **Caching**: Local caching reduces API calls

## 🎉 Getting Started

1. Start with local Ollama for privacy
2. Analyze a small, well-organized folder first
3. Enable all context features for best results
4. Review AI suggestions before organizing
5. Export plans for large reorganization projects

The enhanced AI File Organizer transforms chaotic file collections into well-organized, logical folder structures using the power of artificial intelligence and context awareness.

---

## Original Simple Version

The original `organizer.py` file provides a basic file type organizer using libmagic. It's still available for users who prefer a simpler, non-AI approach.

## License

This project is provided under the Apache 2.0 license. See the `LICENSE` file for details.