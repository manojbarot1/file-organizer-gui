#!/usr/bin/env python3
"""
Test Script for Enhanced AI File Organizer

This script tests the enhanced AI file organizer with demo projects
to verify functionality and demonstrate improvements.
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from ai_backends import (
            list_ollama_models,
            test_ai_connection,
            validate_folder_path,
            extract_path_from_response
        )
        print("✅ AI backends imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import AI backends: {e}")
        return False
    
    try:
        from ai_file_organizer import EnhancedFileAnalyzer, EnhancedAIOrganizer
        print("✅ Enhanced organizer imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import enhanced organizer: {e}")
        return False
    
    return True

def test_file_analyzer():
    """Test the enhanced file analyzer"""
    print("\n🔍 Testing file analyzer...")
    
    try:
        from ai_file_organizer import EnhancedFileAnalyzer
        
        # Test with demo project
        demo_path = Path("demo_project")
        if not demo_path.exists():
            print("❌ Demo project not found. Run demo_setup.py first.")
            return False
        
        analyzer = EnhancedFileAnalyzer(demo_path)
        print("✅ File analyzer created successfully")
        
        # Test project type detection
        project_type = analyzer._detect_project_type()
        print(f"✅ Project type detected: {project_type}")
        
        # Test file categorization
        test_file = demo_path / "main.py"
        if test_file.exists():
            category = analyzer._categorize_file(test_file)
            print(f"✅ File categorization: main.py -> {category}")
        
        # Test context extraction
        context = analyzer.get_file_context(test_file)
        print(f"✅ Context extraction: {len(context)} context items")
        
        return True
        
    except Exception as e:
        print(f"❌ File analyzer test failed: {e}")
        return False

def test_ai_backends():
    """Test AI backend functionality"""
    print("\n🔍 Testing AI backends...")
    
    try:
        from ai_backends import (
            validate_folder_path,
            extract_path_from_response,
            test_ai_connection
        )
        
        # Test path validation
        test_paths = [
            "src/components",
            "docs/api",
            "config/settings",
            "the path is src/components",  # Should clean this
            "Error: connection failed",     # Should return Uncategorized
            ""                             # Should return Uncategorized
        ]
        
        for path in test_paths:
            cleaned = validate_folder_path(path)
            print(f"✅ Path validation: '{path}' -> '{cleaned}'")
        
        # Test response extraction
        test_responses = [
            "The file should go in src/components",
            "src/components",
            "```\nsrc/components\n```",
            "The cleaned compact path would be docs/api",
            '{"path": "config/settings"}'
        ]
        
        for response in test_responses:
            extracted = extract_path_from_response(response)
            print(f"✅ Response extraction: '{response}' -> '{extracted}'")
        
        # Test connection (will fail without actual backend)
        print("⚠️  Testing AI connection (will fail without backend)...")
        success, message = test_ai_connection("Local (Ollama)", "llama3.1", "")
        print(f"✅ Connection test: {success} - {message}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI backends test failed: {e}")
        return False

def test_demo_projects():
    """Test with demo projects"""
    print("\n🔍 Testing demo projects...")
    
    demo_projects = ["demo_project", "demo_terraform_project"]
    
    for project_name in demo_projects:
        project_path = Path(project_name)
        if not project_path.exists():
            print(f"❌ Demo project '{project_name}' not found")
            continue
        
        print(f"✅ Found demo project: {project_name}")
        
        # Count files
        file_count = sum(1 for _ in project_path.rglob("*") if _.is_file())
        print(f"   📁 Contains {file_count} files")
        
        # Check for key files
        key_files = {
            "demo_project": ["main.py", "requirements.txt", ".env", "docs/README.md"],
            "demo_terraform_project": ["main.tf", "variables.tf", "modules/", "environments/"]
        }
        
        if project_name in key_files:
            for key_file in key_files[project_name]:
                if (project_path / key_file).exists():
                    print(f"   ✅ Found key file: {key_file}")
                else:
                    print(f"   ⚠️  Missing key file: {key_file}")
    
    return True

def test_organizer_creation():
    """Test organizer GUI creation (without showing window)"""
    print("\n🔍 Testing organizer creation...")
    
    try:
        import tkinter as tk
        from ai_file_organizer import EnhancedAIOrganizer
        
        # Create organizer instance
        app = EnhancedAIOrganizer()
        
        # Test basic functionality
        print("✅ Organizer GUI created successfully")
        print(f"   📏 Window size: {app.geometry()}")
        print(f"   🏷️  Title: {app.title()}")
        
        # Test folder selection (without showing dialog)
        test_folder = Path("demo_project")
        if test_folder.exists():
            app.folder = test_folder
            app.root_name = test_folder.name
            app.folder_lbl.configure(text=str(test_folder))
            print(f"   📁 Folder set: {test_folder}")
            
            # Test analyzer creation
            if hasattr(app, 'analyzer') and app.analyzer:
                print("   ✅ File analyzer created")
            else:
                print("   ⚠️  File analyzer not created")
        
        # Clean up
        app.destroy()
        print("✅ Organizer cleaned up successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Organizer creation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Enhanced AI File Organizer - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("File Analyzer Test", test_file_analyzer),
        ("AI Backends Test", test_ai_backends),
        ("Demo Projects Test", test_demo_projects),
        ("Organizer Creation Test", test_organizer_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The enhanced organizer is ready to use.")
        print("\n🚀 To run the organizer:")
        print("   python3 ai_file_organizer.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)