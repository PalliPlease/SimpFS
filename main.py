import os

from disk import VirtualDisk, BLOCK_SIZE, DISK_SIZE
from filesystem import FileSystem


DISK_FILE = "disk.img"


def format_size(size):
    """Convert bytes into a human-readable size."""
    units = ("B", "KB", "MB", "GB")

    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            break

        value /= 1024

    if unit == "B":
        return f"{int(value)} {unit}"

    return f"{value:.1f} {unit}"


def print_header():
    print("\n" + "*" * 32)
    print("             SimpFS")
    print("*" * 32)


def show_help():
    print("""
Available commands:

    ls
        List all files in the filesystem.

    nano
        Create a new text file.

    cat
        Read the contents of a file.

    rm
        Delete a file.

    du
        Show filesystem storage usage.

    format
        Format the filesystem and erase all files.

    clear
        Clear the terminal screen.

    help
        Show this help message.

    e / exit
        Exit SimpFS.
""")


def list_files(fs):
    """Display all files stored in the filesystem."""

    files = fs.list_files()

    if not files:
        print("No files found.")
        return

    print(
        f"\n{'Name':<32}"
        f"{'Size':>10}"
        f"{'Blocks':>8}"
        f"{'Allocated':>12}"
    )

    print("-" * 64)

    for file_info in files:
        allocated_size = file_info["block_count"] * BLOCK_SIZE

        print(
            f"{file_info['name']:<32}"
            f"{format_size(file_info['size']):>10}"
            f"{file_info['block_count']:>8}"
            f"{format_size(allocated_size):>12}"
        )

    print()


def create_file(fs):
    """Create a new text file."""

    name = input("Enter file name: ").strip()

    if not name:
        print("File name cannot be empty.")
        return

    data = input("Enter the text: ").encode("utf-8")

    try:
        fs.create_file(name, data)
        print(f"File '{name}' created successfully.")

    except Exception as error:
        print(f"Error creating file: {error}")


def read_file(fs):
    """Read and display a file."""

    name = input("Enter file name: ").strip()

    if not name:
        print("File name cannot be empty.")
        return

    try:
        data = fs.read_file(name)

        if isinstance(data, bytes):
            print(data.decode("utf-8", errors="replace"))
        else:
            print(data)

    except Exception as error:
        print(f"Error reading file: {error}")


def delete_file(fs):
    """Delete a file."""

    name = input("Enter file name: ").strip()

    if not name:
        print("File name cannot be empty.")
        return

    try:
        fs.delete_file(name)
        print(f"File '{name}' deleted successfully.")

    except Exception as error:
        print(f"Error deleting file: {error}")


def show_storage(fs):
    """Display filesystem storage information."""

    try:
        used = fs.storage_used()

        total = DISK_SIZE
        free = total - used

        percentage = (used / total) * 100

        print()
        print("Storage Usage")
        print("-" * 32)
        print(f"Used : {format_size(used)}")
        print(f"Free : {format_size(free)}")
        print(f"Total: {format_size(total)}")
        print(f"Usage: {percentage:.2f}%")
        print()

    except Exception as error:
        print(f"Error reading storage information: {error}")


def format_filesystem(disk, fs):
    """Format the filesystem."""

    print("\nWARNING: Formatting will erase all files.")
    confirmation = input("Continue? (y/n): ").strip().lower()

    if confirmation != "y":
        print("Formatting cancelled.")
        return

    try:
        fs.format()
        print("Filesystem formatted successfully.")

    except Exception as error:
        print(f"Error formatting filesystem: {error}")


def clear_screen():
    """Clear the terminal screen."""

    os.system("clear")


def main():
    disk = VirtualDisk(DISK_FILE)

    # Create the virtual disk if it does not already exist.
    if not os.path.exists(DISK_FILE):
        disk.create()

        fs = FileSystem(disk)
        fs.format()

        print("Created and formatted a new SimpFS disk.")

    else:
        fs = FileSystem(disk)

    print_header()
    print("Type 'help' to see available commands.")

    while True:

        try:
            command = input("\nSimpFS> ").strip().lower()

        except (KeyboardInterrupt, EOFError):
            print("\nExiting SimpFS.")
            break

        if command == "":
            continue

        if command in ("e", "exit"):
            print("Exiting SimpFS.")
            break

        elif command == "help":
            show_help()

        elif command == "ls":
            list_files(fs)

        elif command == "nano":
            create_file(fs)

        elif command == "cat":
            read_file(fs)

        elif command == "rm":
            delete_file(fs)

        elif command == "du":
            show_storage(fs)

        elif command == "format":
            format_filesystem(disk, fs)

        elif command == "clear":
            clear_screen()
            print_header()

        else:
            print(
                f"Unknown command: '{command}'. "
                "Type 'help' to see available commands."
            )


if __name__ == "__main__":
    main()