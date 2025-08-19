#!/usr/bin/env python3
"""
Demo Setup Script for Enhanced AI File Organizer

This script creates a sample project structure with various file types
to demonstrate the enhanced AI file organizer's capabilities.
"""

import os
import shutil
from pathlib import Path
import random

def create_demo_project():
    """Create a demo project with various file types and structures"""
    
    # Create demo directory
    demo_dir = Path("demo_project")
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    demo_dir.mkdir()
    
    print("Creating demo project structure...")
    
    # Create a Python project structure
    create_python_project(demo_dir)
    
    # Create some mixed content
    create_mixed_content(demo_dir)
    
    # Create configuration files
    create_config_files(demo_dir)
    
    # Create documentation
    create_documentation(demo_dir)
    
    # Create media files (simulated)
    create_media_files(demo_dir)
    
    print(f"\n✅ Demo project created at: {demo_dir.absolute()}")
    print("\n📁 Project structure:")
    print_project_structure(demo_dir)
    
    print("\n🚀 To test the AI File Organizer:")
    print(f"1. Run: python ai_file_organizer.py")
    print(f"2. Select folder: {demo_dir.absolute()}")
    print(f"3. Configure AI backend and scan")

def create_python_project(root_dir):
    """Create a Python project structure"""
    
    # Python project files
    python_files = {
        "main.py": "#!/usr/bin/env python3\nprint('Hello, World!')\n",
        "requirements.txt": "requests>=2.28.0\npython-magic>=0.4.27\n",
        "setup.py": "from setuptools import setup\nsetup(name='demo-project')\n",
        "config.py": "import os\n\nDEBUG = True\nAPI_KEY = 'demo-key'\n",
        "utils.py": "def helper_function():\n    return 'helper'\n",
        "test_main.py": "import unittest\nfrom main import *\n\nclass TestMain(unittest.TestCase):\n    pass\n",
        "data_processor.py": "import pandas as pd\n\ndef process_data():\n    pass\n",
        "api_client.py": "import requests\n\ndef make_request():\n    pass\n"
    }
    
    # Create files in root
    for filename, content in python_files.items():
        with open(root_dir / filename, 'w') as f:
            f.write(content)

def create_mixed_content(root_dir):
    """Create mixed content files"""
    
    # Create some subdirectories with mixed content
    subdirs = {
        "old_files": {
            "legacy_code.py": "# Old code\nprint('legacy')\n",
            "backup.txt": "This is a backup file\n",
            "old_config.json": '{"old": "config"}\n'
        },
        "temp": {
            "temp_file.tmp": "Temporary content\n",
            "cache.dat": "Cache data\n",
            "log.txt": "Log entry\n"
        },
        "downloads": {
            "downloaded_file.zip": "ZIP content\n",
            "image.jpg": "JPEG data\n",
            "document.pdf": "PDF content\n"
        }
    }
    
    for subdir, files in subdirs.items():
        subdir_path = root_dir / subdir
        subdir_path.mkdir()
        
        for filename, content in files.items():
            with open(subdir_path / filename, 'w') as f:
                f.write(content)

def create_config_files(root_dir):
    """Create various configuration files"""
    
    config_files = {
        ".env": "DEBUG=True\nAPI_KEY=demo\nDATABASE_URL=sqlite:///demo.db\n",
        "config.json": '{"debug": true, "port": 8000, "host": "localhost"}\n',
        "settings.yaml": "debug: true\nport: 8000\nhost: localhost\n",
        "docker-compose.yml": "version: '3'\nservices:\n  app:\n    image: demo\n",
        "Dockerfile": "FROM python:3.9\nCOPY . .\nRUN pip install -r requirements.txt\n",
        ".gitignore": "*.pyc\n__pycache__\n.env\n*.log\n",
        "Makefile": "install:\n\tpip install -r requirements.txt\n\nrun:\n\tpython main.py\n"
    }
    
    for filename, content in config_files.items():
        with open(root_dir / filename, 'w') as f:
            f.write(content)

def create_documentation(root_dir):
    """Create documentation files"""
    
    docs_dir = root_dir / "docs"
    docs_dir.mkdir()
    
    doc_files = {
        "README.md": "# Demo Project\n\nThis is a demo project for testing the AI file organizer.\n",
        "API.md": "# API Documentation\n\nAPI endpoints and usage.\n",
        "setup.md": "# Setup Guide\n\nHow to set up this project.\n",
        "CHANGELOG.md": "# Changelog\n\n## Version 1.0.0\n- Initial release\n",
        "LICENSE": "MIT License\n\nCopyright (c) 2024 Demo Project\n"
    }
    
    for filename, content in doc_files.items():
        with open(docs_dir / filename, 'w') as f:
            f.write(content)

def create_media_files(root_dir):
    """Create simulated media files"""
    
    media_dir = root_dir / "media"
    media_dir.mkdir()
    
    # Create subdirectories for different media types
    media_types = {
        "images": ["photo1.jpg", "screenshot.png", "icon.ico", "logo.svg"],
        "audio": ["music.mp3", "podcast.wav", "sound.flac"],
        "video": ["demo.mp4", "tutorial.avi", "presentation.mov"],
        "documents": ["report.pdf", "presentation.pptx", "spreadsheet.xlsx"]
    }
    
    for media_type, files in media_types.items():
        type_dir = media_dir / media_type
        type_dir.mkdir()
        
        for filename in files:
            # Create a small file with appropriate extension
            with open(type_dir / filename, 'w') as f:
                f.write(f"Simulated {media_type} file: {filename}\n")

def print_project_structure(directory, prefix="", max_depth=3, current_depth=0):
    """Print the project structure in a tree-like format"""
    if current_depth > max_depth:
        return
    
    items = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name))
    
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        next_prefix = "    " if is_last else "│   "
        
        if item.is_file():
            print(f"{prefix}{current_prefix}{item.name}")
        else:
            print(f"{prefix}{current_prefix}{item.name}/")
            print_project_structure(item, prefix + next_prefix, max_depth, current_depth + 1)

def create_terraform_demo():
    """Create a Terraform project demo"""
    
    tf_dir = Path("demo_terraform_project")
    if tf_dir.exists():
        shutil.rmtree(tf_dir)
    tf_dir.mkdir()
    
    print("\nCreating Terraform demo project...")
    
    # Terraform files
    tf_files = {
        "main.tf": 'resource "aws_instance" "demo" {\n  ami = "ami-123456"\n  instance_type = "t2.micro"\n}\n',
        "variables.tf": 'variable "region" {\n  default = "us-west-2"\n}\n',
        "outputs.tf": 'output "instance_id" {\n  value = aws_instance.demo.id\n}\n',
        "terraform.tfvars": 'region = "us-west-2"\n',
        "versions.tf": 'terraform {\n  required_version = ">= 1.0"\n}\n'
    }
    
    # Create modules directory
    modules_dir = tf_dir / "modules"
    modules_dir.mkdir()
    
    # Create environments
    environments = ["dev", "staging", "prod"]
    for env in environments:
        env_dir = tf_dir / "environments" / env
        env_dir.mkdir(parents=True)
        
        with open(env_dir / "main.tf", 'w') as f:
            f.write(f'# {env} environment\nmodule "demo" {{\n  source = "../../modules/demo"\n}}\n')
        
        with open(env_dir / "terraform.tfvars", 'w') as f:
            f.write(f'environment = "{env}"\n')
    
    # Create module files
    module_files = {
        "main.tf": 'resource "aws_s3_bucket" "demo" {\n  bucket = var.bucket_name\n}\n',
        "variables.tf": 'variable "bucket_name" {\n  type = string\n}\n',
        "outputs.tf": 'output "bucket_id" {\n  value = aws_s3_bucket.demo.id\n}\n'
    }
    
    for filename, content in module_files.items():
        with open(modules_dir / filename, 'w') as f:
            f.write(content)
    
    # Create main project files
    for filename, content in tf_files.items():
        with open(tf_dir / filename, 'w') as f:
            f.write(content)
    
    print(f"✅ Terraform demo created at: {tf_dir.absolute()}")

if __name__ == "__main__":
    print("🎯 Enhanced AI File Organizer - Demo Setup")
    print("=" * 50)
    
    create_demo_project()
    create_terraform_demo()
    
    print("\n🎉 Demo setup complete!")
    print("\n📋 What was created:")
    print("1. demo_project/ - Python project with mixed content")
    print("2. demo_terraform_project/ - Terraform infrastructure project")
    print("\n🔧 These demos showcase:")
    print("- Project type detection (Python, Terraform)")
    print("- Mixed file types and structures")
    print("- Configuration files and documentation")
    print("- Media files and archives")
    print("- Nested directory structures")
    
    print("\n🚀 Next steps:")
    print("1. Run: python ai_file_organizer.py")
    print("2. Select one of the demo folders")
    print("3. Configure your AI backend")
    print("4. Watch the AI organize files intelligently!")