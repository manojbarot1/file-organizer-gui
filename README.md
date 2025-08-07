# GUI File Organizer

This project is a simple GUI application that identifies file types and can
organize files into folders based on their type.  It uses only open‑source
packages and is intended as a starting point for building your own file
management tool.

## Features

* **Scan a directory:** Select a folder to scan, and the application will
  inspect each file using the `filemagic` library to determine its type
  (e.g., JPEG image, PDF document, plain text).
* **Display results:** The GUI shows a list of files along with their
  detected type.  This helps you see how your files are classified before
  making any changes.
* **Organize files:** You can click the **Organize** button to create
  sub‑folders based on the detected types (for example, `Images`,
  `Documents`, `Text`), and move each file into its corresponding folder.

## Installation

1. **Install `libmagic`:** On macOS, install the system library with Homebrew:
   ```sh
   brew install libmagic
   ```

2. **Install dependencies:** Create and activate a virtual environment (optional
   but recommended), then install Python packages listed in
   `requirements.txt`:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

Run the application with Python:

```sh
python organizer.py
```

In the GUI:

1. Click **Select Folder** and choose the directory you want to scan.
2. Wait for the files to be listed with their detected types.
3. Click **Organize Files** to create sub‑folders (based on the type groups
   configured in the script) and move the files.

All file operations are performed via Python’s `shutil` and will not delete
anything—files are simply moved into the new folders.  Always test with
non‑critical files first.

## License

This example is provided under the Apache 2.0 license.  See the `LICENSE`
file for details.