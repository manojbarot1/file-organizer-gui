#!/bin/bash

# AI File Organizer - Mac Setup Script
# This script will set up everything you need to run the AI File Organizer on macOS

echo "🚀 Setting up AI File Organizer on macOS..."
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3 is installed
print_status "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Found $PYTHON_VERSION"
else
    print_error "Python 3 is not installed. Please install Python 3.8+ from https://python.org"
    exit 1
fi

# Check if pip is available
print_status "Checking pip installation..."
if command -v pip3 &> /dev/null; then
    print_success "pip3 is available"
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    print_success "pip is available"
    PIP_CMD="pip"
else
    print_error "pip is not available. Please install pip."
    exit 1
fi

# Create virtual environment
print_status "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_status "Upgrading pip..."
$PIP_CMD install --upgrade pip

# Install requirements
print_status "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    $PIP_CMD install -r requirements.txt
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Check if Homebrew is installed (for Ollama)
print_status "Checking Homebrew installation..."
if command -v brew &> /dev/null; then
    print_success "Homebrew is installed"
    BREW_AVAILABLE=true
else
    print_warning "Homebrew not found. You can install it from https://brew.sh"
    BREW_AVAILABLE=false
fi

# Offer to install Ollama
echo ""
echo "🤖 AI Backend Setup"
echo "=================="
echo "The AI File Organizer supports multiple AI backends:"
echo "1. Ollama (Local, Free, Private) - Recommended"
echo "2. OpenAI (Cloud, Paid, High Quality)"
echo "3. Grok (Cloud, Paid, Alternative)"
echo ""

read -p "Would you like to install Ollama for local AI? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ "$BREW_AVAILABLE" = true ]; then
        print_status "Installing Ollama..."
        brew install ollama
        
        print_status "Starting Ollama service..."
        brew services start ollama
        
        # Wait a moment for service to start
        sleep 3
        
        print_status "Installing recommended model (llama3.1)..."
        ollama pull llama3.1
        
        print_success "Ollama setup complete!"
        echo "  • Service is running in the background"
        echo "  • Model 'llama3.1' is ready to use"
    else
        print_warning "Homebrew required for easy Ollama installation"
        echo "Please install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "Then run: brew install ollama && ollama pull llama3.1"
    fi
fi

# Create test folder structure
print_status "Creating test folder structure..."
mkdir -p test_files/{documents,images,code,misc}

# Create sample test files
cat > test_files/documents/report.txt << 'EOF'
This is a sample report document for testing the AI file organizer.
It should be categorized as a document.
EOF

cat > test_files/images/photo_info.txt << 'EOF'
This file contains information about photos.
It might be categorized with images or documents.
EOF

cat > test_files/code/script.py << 'EOF'
# Sample Python script
print("Hello, World!")
def organize_files():
    pass
EOF

cat > test_files/misc/readme.md << 'EOF'
# Test Files
This folder contains test files for the AI organizer.
EOF

echo "Sample files created in test_files/ directory"

# Create a launch script
print_status "Creating launch script..."
cat > run_organizer.sh << 'EOF'
#!/bin/bash
# Launch script for AI File Organizer

echo "🚀 Starting AI File Organizer..."

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Please run setup_mac.sh first."
    exit 1
fi

# Check if Ollama is running (if installed)
if command -v ollama &> /dev/null; then
    if ! pgrep -f "ollama" > /dev/null; then
        echo "🤖 Starting Ollama service..."
        ollama serve &
        sleep 2
    fi
    echo "✅ Ollama is running"
fi

# Launch the application
echo "🎯 Launching AI File Organizer..."
python3 ai_file_organizer.py

EOF

chmod +x run_organizer.sh
print_success "Launch script created (run_organizer.sh)"

# Final instructions
echo ""
echo "🎉 Setup Complete!"
echo "================="
print_success "AI File Organizer is ready to use!"
echo ""
echo "📋 Next Steps:"
echo "1. Run the application: ./run_organizer.sh"
echo "2. Or manually: source venv/bin/activate && python3 ai_file_organizer.py"
echo "3. Test with the sample files in test_files/ directory"
echo ""
echo "🔧 Configuration:"
echo "• For Ollama: Select 'Local (Ollama)' backend and 'llama3.1' model"
echo "• For OpenAI: Get API key from https://platform.openai.com"
echo "• For Grok: Get API key from https://console.x.ai"
echo ""
echo "📚 Need help? Check the README.md file for detailed instructions."
echo ""
print_success "Happy organizing! 🗂️"