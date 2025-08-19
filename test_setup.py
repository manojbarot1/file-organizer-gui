#!/usr/bin/env python3
"""
Test script to verify AI File Organizer setup on Mac
"""

import sys
import os
import subprocess
from pathlib import Path

def print_status(message, status="INFO"):
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m", 
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "RESET": "\033[0m"
    }
    print(f"{colors.get(status, '')}{message}{colors['RESET']}")

def test_python_version():
    """Test Python version compatibility"""
    print_status("Testing Python version...", "INFO")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_status(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible", "SUCCESS")
        return True
    else:
        print_status(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.8+", "ERROR")
        return False

def test_dependencies():
    """Test if required dependencies are available"""
    print_status("Testing dependencies...", "INFO")
    required_modules = ['tkinter', 'requests', 'pathlib', 'json', 'threading']
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print_status(f"  ✅ {module}", "SUCCESS")
        except ImportError:
            print_status(f"  ❌ {module}", "ERROR")
            missing.append(module)
    
    if missing:
        print_status(f"Missing modules: {', '.join(missing)}", "ERROR")
        return False
    else:
        print_status("All dependencies available", "SUCCESS")
        return True

def test_files_exist():
    """Test if required files exist"""
    print_status("Testing required files...", "INFO")
    required_files = [
        'ai_file_organizer.py',
        'ai_backends.py', 
        'requirements.txt',
        'README.md'
    ]
    
    missing = []
    for file in required_files:
        if Path(file).exists():
            print_status(f"  ✅ {file}", "SUCCESS")
        else:
            print_status(f"  ❌ {file}", "ERROR")
            missing.append(file)
    
    if missing:
        print_status(f"Missing files: {', '.join(missing)}", "ERROR")
        return False
    else:
        print_status("All required files present", "SUCCESS")
        return True

def test_ollama_connection():
    """Test Ollama connection if available"""
    print_status("Testing Ollama connection...", "INFO")
    try:
        # Check if ollama command exists
        result = subprocess.run(['which', 'ollama'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_status("  ✅ Ollama command found", "SUCCESS")
            
            # Test if ollama service is running
            try:
                result = subprocess.run(['ollama', 'list'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print_status("  ✅ Ollama service is running", "SUCCESS")
                    models = result.stdout.strip()
                    if models:
                        print_status(f"  ✅ Available models found", "SUCCESS")
                        print_status(f"     {models.split()[0] if models else 'No models'}", "INFO")
                    else:
                        print_status("  ⚠️  No models installed. Run: ollama pull llama3.1", "WARNING")
                    return True
                else:
                    print_status("  ❌ Ollama service not running. Run: ollama serve", "WARNING")
                    return False
            except subprocess.TimeoutExpired:
                print_status("  ❌ Ollama service timeout", "WARNING")
                return False
        else:
            print_status("  ⚠️  Ollama not installed. Install with: brew install ollama", "WARNING")
            return False
    except Exception as e:
        print_status(f"  ❌ Ollama test failed: {e}", "WARNING")
        return False

def test_gui_import():
    """Test if GUI can be imported"""
    print_status("Testing GUI imports...", "INFO")
    try:
        import tkinter as tk
        from tkinter import ttk
        print_status("  ✅ Tkinter available", "SUCCESS")
        
        # Test if we can create a root window (headless test)
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the window
            root.destroy()
            print_status("  ✅ GUI creation works", "SUCCESS")
            return True
        except Exception as e:
            print_status(f"  ❌ GUI creation failed: {e}", "ERROR")
            return False
            
    except ImportError as e:
        print_status(f"  ❌ Tkinter import failed: {e}", "ERROR")
        return False

def test_ai_backends_import():
    """Test if AI backends can be imported"""
    print_status("Testing AI backends import...", "INFO")
    try:
        from ai_backends import (
            query_ollama, query_openai, query_grok,
            list_ollama_models, test_ai_connection,
            analyze_folder_structure, build_context_prompt
        )
        print_status("  ✅ AI backends imported successfully", "SUCCESS")
        return True
    except ImportError as e:
        print_status(f"  ❌ AI backends import failed: {e}", "ERROR")
        return False

def main():
    """Run all tests"""
    print_status("🧪 AI File Organizer Setup Test", "INFO")
    print_status("=" * 40, "INFO")
    
    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_dependencies), 
        ("Required Files", test_files_exist),
        ("GUI Support", test_gui_import),
        ("AI Backends", test_ai_backends_import),
        ("Ollama Connection", test_ollama_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print_status(f"\n--- {test_name} ---", "INFO")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_status(f"Test failed with exception: {e}", "ERROR")
            results.append((test_name, False))
    
    # Summary
    print_status("\n" + "=" * 40, "INFO")
    print_status("📊 Test Summary", "INFO")
    print_status("=" * 40, "INFO")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print_status(f"{test_name:20} {status}")
    
    print_status(f"\nOverall: {passed}/{total} tests passed", 
                "SUCCESS" if passed == total else "WARNING")
    
    if passed == total:
        print_status("\n🎉 All tests passed! You're ready to use the AI File Organizer.", "SUCCESS")
        print_status("Run: python3 ai_file_organizer.py", "INFO")
    else:
        print_status("\n⚠️  Some tests failed. Check the issues above.", "WARNING")
        print_status("You may still be able to use the application with limited functionality.", "INFO")

if __name__ == "__main__":
    main()