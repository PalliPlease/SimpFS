# SimpFS
SimpFS is a simple block based filesystem that I built from scratch in python. 
The goal of this project was to explore how a filesystem works internally. I implemented the basic ideas behind a filesystem such as block, file metadata, reading and writing files and CLI based interface.
The project is highly basic and skips over features such as updating files, having directories, etc.

## Project Structure

```text
SimpFS/
│
├── disk.py
├── filesystem.py
├── main.py
└── README.md
```

## Basic Commands

```text
ls       - List all files
nano     - Create a new file
cat      - Read a file
rm       - Delete a file
du       - Show storage usage
format   - Format the filesystem
clear    - Clear the terminal
help     - Show available commands
exit     - Exit SimpFS
e        - Exit SimpFS
```
