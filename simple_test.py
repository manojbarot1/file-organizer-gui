#!/usr/bin/env python3
"""
Simplified Test for Enhanced AI File Organizer

This script demonstrates the enhanced AI file organizer's capabilities
without requiring external dependencies like tkinter or requests.
"""

import os
import sys
from pathlib import Path

def demonstrate_file_analysis():
    """Demonstrate the file analysis capabilities"""
    print("🔍 Demonstrating Enhanced File Analysis")
    print("=" * 50)
    
    # Simulate the enhanced file analyzer logic
    def categorize_file(file_path):
        """Simulate file categorization"""
        ext = file_path.suffix.lower()
        name = file_path.name.lower()
        
        # Enhanced categorization
        categories = {
            "code": {".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".hpp", ".cs", ".php", ".rb", ".go", ".rs", ".swift", ".kt"},
            "config": {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env", ".properties"},
            "docs": {".md", ".txt", ".rst", ".adoc", ".tex", ".doc", ".docx", ".pdf", ".rtf"},
            "images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg", ".ico"},
            "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"},
            "video": {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v"},
            "archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
            "data": {".csv", ".xlsx", ".xls", ".db", ".sqlite", ".xml", ".json"},
            "terraform": {".tf", ".tfvars", ".tfstate", ".lock.hcl"},
            "docker": {"Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"},
            "git": {".gitignore", ".gitattributes", ".gitmodules"},
            "logs": {".log", ".out", ".err", ".trace"}
        }
        
        for category, extensions in categories.items():
            if ext in extensions or name in extensions:
                return category
        
        return "unknown"
    
    def detect_project_type(root_path):
        """Simulate project type detection"""
        try:
            root_files = set(os.listdir(root_path))
            
            if '.git' in root_files:
                if 'package.json' in root_files:
                    return 'nodejs'
                elif 'pyproject.toml' in root_files or 'requirements.txt' in root_files:
                    return 'python'
                elif 'go.mod' in root_files:
                    return 'golang'
                elif 'Cargo.toml' in root_files:
                    return 'rust'
                elif 'pom.xml' in root_files:
                    return 'java_maven'
                elif 'build.gradle' in root_files:
                    return 'java_gradle'
                elif any(f.endswith('.tf') for f in root_files):
                    return 'terraform'
                else:
                    return 'git_repo'
            elif 'Dockerfile' in root_files:
                return 'docker'
            elif any(f.endswith('.tf') for f in root_files):
                return 'terraform'
            else:
                return 'general'
                
        except Exception:
            return 'unknown'
    
    # Test with demo projects
    demo_projects = ["demo_project", "demo_terraform_project"]
    
    for project_name in demo_projects:
        project_path = Path(project_name)
        if not project_path.exists():
            continue
        
        print(f"\n📁 Analyzing project: {project_name}")
        
        # Detect project type
        project_type = detect_project_type(project_path)
        print(f"   🏷️  Project type: {project_type}")
        
        # Analyze files
        files = list(project_path.rglob("*"))
        files = [f for f in files if f.is_file()]
        
        # Categorize files
        categories = {}
        for file_path in files:
            category = categorize_file(file_path)
            if category not in categories:
                categories[category] = []
            categories[category].append(file_path.name)
        
        print(f"   📊 File categories found:")
        for category, files_list in categories.items():
            print(f"      {category}: {len(files_list)} files")
            if len(files_list) <= 3:
                for file_name in files_list:
                    print(f"        - {file_name}")
            else:
                for file_name in files_list[:3]:
                    print(f"        - {file_name}")
                print(f"        ... and {len(files_list) - 3} more")

def demonstrate_ai_prompt_generation():
    """Demonstrate AI prompt generation"""
    print("\n🤖 Demonstrating AI Prompt Generation")
    print("=" * 50)
    
    # Simulate the enhanced prompt generation
    def build_enhanced_prompt(file_path, context):
        """Simulate enhanced prompt building"""
        prompt_parts = [
            "You are an expert file organizer. Analyze the file and suggest the best folder path for organization.",
            "",
            f"FILE: {file_path.name}",
            f"EXTENSION: {file_path.suffix}",
            f"CURRENT LOCATION: {file_path.parent}",
            f"CATEGORY: {context.get('file_category', 'unknown')}",
            f"PROJECT TYPE: {context.get('project_type', 'unknown')}",
        ]
        
        # Add context
        if context.get('sibling_files'):
            prompt_parts.append(f"SIBLING FILES: {', '.join(context['sibling_files'][:5])}")
        
        # Add project-specific guidance
        project_type = context.get('project_type', 'unknown')
        if project_type == 'python':
            prompt_parts.extend([
                "",
                "PROJECT GUIDELINES:",
                "- Keep source code in 'src/' or similar",
                "- Separate tests in 'tests/' or 'test/'",
                "- Configuration files in 'config/' or root",
                "- Documentation in 'docs/' or 'doc/'",
                "- Assets in 'assets/', 'static/', or 'public/'"
            ])
        elif project_type == 'terraform':
            prompt_parts.extend([
                "",
                "PROJECT GUIDELINES:",
                "- Terraform files in 'terraform/' or 'infrastructure/'",
                "- Separate environments (dev, staging, prod)",
                "- Keep modules in 'modules/'",
                "- Variables and outputs in separate files"
            ])
        
        # Final instructions
        prompt_parts.extend([
            "",
            "RESPONSE FORMAT:",
            "- Return ONLY the folder path (e.g., 'src/components' or 'docs/api')",
            "- Use forward slashes (/)",
            "- Keep paths concise (1-3 levels)",
            "- If uncertain, use 'Uncategorized'",
            "",
            "SUGGESTED PATH:"
        ])
        
        return "\n".join(prompt_parts)
    
    # Demonstrate with sample files
    sample_files = [
        ("main.py", {"file_category": "code", "project_type": "python", "sibling_files": ["config.py", "utils.py"]}),
        ("test_main.py", {"file_category": "code", "project_type": "python", "sibling_files": ["main.py", "utils.py"]}),
        ("config.json", {"file_category": "config", "project_type": "python", "sibling_files": ["main.py", ".env"]}),
        ("main.tf", {"file_category": "terraform", "project_type": "terraform", "sibling_files": ["variables.tf", "outputs.tf"]}),
        ("README.md", {"file_category": "docs", "project_type": "python", "sibling_files": ["main.py", "docs/"]})
    ]
    
    for filename, context in sample_files:
        print(f"\n📄 Generating prompt for: {filename}")
        prompt = build_enhanced_prompt(Path(filename), context)
        print("   Generated prompt:")
        print("   " + "\n   ".join(prompt.split('\n')[:10]) + "\n   ...")

def demonstrate_path_processing():
    """Demonstrate path processing and validation"""
    print("\n🛣️  Demonstrating Path Processing")
    print("=" * 50)
    
    def validate_folder_path(path):
        """Simulate path validation"""
        if not path or path.lower() in ['error', 'none', 'null', 'undefined']:
            return "Uncategorized"
        
        # Clean the path
        path = path.strip().strip('"\'`')
        path = path.replace('\\', '/')
        path = path.strip('/')
        
        # Remove invalid characters
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            path = path.replace(char, '')
        
        # Remove common unwanted prefixes
        unwanted_prefixes = ['the path is', 'the folder is', 'suggested path:', 'folder path:', 'path:']
        for prefix in unwanted_prefixes:
            if path.lower().startswith(prefix.lower()):
                path = path[len(prefix):].strip()
        
        # Limit path length and depth
        if len(path) > 100:
            parts = path.split('/')
            if len(parts) > 1:
                path = '/'.join(parts[:3])  # Keep first 3 parts
            else:
                path = path[:100]
        
        # Ensure it's not empty after cleaning
        if not path or path.isspace():
            return "Uncategorized"
        
        return path
    
    def extract_path_from_response(response):
        """Simulate response extraction"""
        if not response:
            return "Uncategorized"
        
        # Remove code blocks and formatting
        import re
        response = re.sub(r"```.*?```", "", response, flags=re.DOTALL)
        response = re.sub(r"<.*?>", "", response, flags=re.DOTALL)
        
        # Remove common prose phrases
        prose_patterns = [
            r"\b(the cleaned compact path would be|the path would be|the best path is|final path:)\b.*",
            r"\b(this file should go in|this belongs in|organize this as)\b.*",
            r"\b(suggested organization|recommended location)\b.*"
        ]
        
        for pattern in prose_patterns:
            response = re.sub(pattern, "", response, flags=re.IGNORECASE)
        
        # Look for path-like patterns
        path_patterns = [
            r"([A-Za-z0-9 _.-]+(?:/[A-Za-z0-9 _.-]+){0,2})",  # Basic path
        ]
        
        for pattern in path_patterns:
            matches = re.findall(pattern, response)
            if matches:
                return validate_folder_path(matches[0])
        
        return "Uncategorized"
    
    # Test path processing
    test_cases = [
        "src/components",
        "the path is docs/api",
        "Error: connection failed",
        "```\nsrc/components\n```",
        "The cleaned compact path would be config/settings",
        '{"path": "assets/images"}',
        "This file should go in tests/unit",
        "Uncategorized"
    ]
    
    for test_case in test_cases:
        processed = extract_path_from_response(test_case)
        print(f"   '{test_case}' -> '{processed}'")

def demonstrate_improvements():
    """Demonstrate the key improvements over basic organizers"""
    print("\n🚀 Demonstrating Key Improvements")
    print("=" * 50)
    
    improvements = [
        {
            "feature": "Context-Aware Path Suggestions",
            "description": "Analyzes existing folder structure and project type",
            "benefit": "More accurate and relevant organization suggestions",
            "example": "Detects Python project and suggests src/, tests/, docs/ structure"
        },
        {
            "feature": "Enhanced AI Integration",
            "description": "Multiple backends with optimized prompts",
            "benefit": "Better AI responses and fallback options",
            "example": "Ollama (local), OpenAI, Grok with backend-specific optimizations"
        },
        {
            "feature": "Smart Project Detection",
            "description": "Automatically identifies project frameworks",
            "benefit": "Project-specific organization guidelines",
            "example": "Python, Node.js, Go, Rust, Terraform, Docker projects"
        },
        {
            "feature": "Advanced File Analysis",
            "description": "Comprehensive file categorization and context",
            "benefit": "Better understanding of file relationships",
            "example": "Code, config, docs, media, archives, logs, etc."
        },
        {
            "feature": "Structure-Aware Adjustments",
            "description": "Adapts to existing folder naming patterns",
            "benefit": "Consistent with project conventions",
            "example": "kebab-case, snake_case, PascalCase detection"
        },
        {
            "feature": "Two-Pass Refinement",
            "description": "Initial suggestion + refinement for accuracy",
            "benefit": "Higher quality organization suggestions",
            "example": "First pass suggests, second pass improves"
        }
    ]
    
    for i, improvement in enumerate(improvements, 1):
        print(f"\n{i}. {improvement['feature']}")
        print(f"   📝 {improvement['description']}")
        print(f"   ✅ {improvement['benefit']}")
        print(f"   💡 {improvement['example']}")

def main():
    """Run all demonstrations"""
    print("🎯 Enhanced AI File Organizer - Capability Demonstration")
    print("=" * 60)
    
    demonstrations = [
        ("File Analysis", demonstrate_file_analysis),
        ("AI Prompt Generation", demonstrate_ai_prompt_generation),
        ("Path Processing", demonstrate_path_processing),
        ("Key Improvements", demonstrate_improvements)
    ]
    
    for demo_name, demo_func in demonstrations:
        try:
            demo_func()
        except Exception as e:
            print(f"❌ {demo_name} demonstration failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Demonstration Complete!")
    print("\n📋 Summary of Enhanced Features:")
    print("✅ Context-aware file organization")
    print("✅ Multi-AI backend support")
    print("✅ Smart project detection")
    print("✅ Advanced file categorization")
    print("✅ Structure-aware adjustments")
    print("✅ Two-pass refinement")
    print("✅ Enhanced error handling")
    print("✅ Comprehensive logging")
    
    print("\n🚀 To use the full organizer:")
    print("1. Install dependencies: pip install requests python-magic")
    print("2. Run: python3 ai_file_organizer.py")
    print("3. Select a folder and configure AI backend")
    print("4. Watch intelligent file organization in action!")

if __name__ == "__main__":
    main()