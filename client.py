import socket
import os

# Client configurations
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000
BUFFER_SIZE = 4096

def authenticate():
    username = input("Enter username: ")
    password = input("Enter password: ")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.send(f"{username}:{password}".encode())
        response = client_socket.recv(BUFFER_SIZE).decode()
        return response == "AUTH_SUCCESS"

def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.send(command.encode())
        response = client_socket.recv(BUFFER_SIZE).decode()
        return response

def upload_file(filename):
    if not os.path.exists(filename):
        print("File not found.")
        return
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.send(f"UPLOAD {filename}".encode())
        with open(filename, "rb") as f:
            while chunk := f.read(BUFFER_SIZE):
                client_socket.send(chunk)
        client_socket.send(b"END")
        response = client_socket.recv(BUFFER_SIZE).decode()
        print(response)

def download_file(filename):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.send(f"DOWNLOAD {filename}".encode())
        response = client_socket.recv(BUFFER_SIZE).decode()
        if response == "FILE FOUND":
            with open(filename, "wb") as f:
                while True:
                    data = client_socket.recv(BUFFER_SIZE)
                    if not data or data == b"END":
                        break
                    f.write(data)
            print("Download complete.")
        else:
            print("File not found.")

def search_files(keyword):
    response = send_command(f"SEARCH {keyword}")
    print("Files found:\n" + response)

def delete_file(filename):
    response = send_command(f"DELETE {filename}")
    print(response)

def restore_file(filename):
    response = send_command(f"RESTORE {filename}")
    print(response)

def bulk_delete(filenames):
    response = send_command(f"BULK_DELETE {' '.join(filenames)}")
    print(response)

def bulk_restore(filenames):
    response = send_command(f"BULK_RESTORE {' '.join(filenames)}")
    print(response)

# CLI Menu
if authenticate():
    while True:
        print("\nSimple File Sharing Client")
        print("1. Upload File")
        print("2. Download File")
        print("3. Search for a File")
        print("4. Delete a File")
        print("5. Restore a File")
        print("6. Bulk Delete Files")
        print("7. Bulk Restore Files")
        print("8. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            filename = input("Enter filename to upload: ")
            upload_file(filename)
        elif choice == "2":
            filename = input("Enter filename to download: ")
            download_file(filename)
        elif choice == "3":
            keyword = input("Enter keyword to search: ")
            search_files(keyword)
        elif choice == "4":
            filename = input("Enter filename to delete: ")
            delete_file(filename)
        elif choice == "5":
            filename = input("Enter filename to restore: ")
            restore_file(filename)
        elif choice == "6":
            filenames = input("Enter filenames to delete (separated by spaces): ").split()
            bulk_delete(filenames)
        elif choice == "7":
            filenames = input("Enter filenames to restore (separated by spaces): ").split()
            bulk_restore(filenames)
        elif choice == "8":
            break
        else:
            print("Invalid choice. Try again.")
else:
    print("Authentication failed. Please check your username and password.")