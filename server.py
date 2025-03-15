import socket
import threading
import os
import time
import json

# Server configurations
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000
BUFFER_SIZE = 4096
STORAGE_DIR = "server_files"
RECYCLE_BIN = "recycle_bin"
USERS_FILE = "users.json"

# Ensure directories exist
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(RECYCLE_BIN, exist_ok=True)

# Load users from file
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
else:
    users = {"admin": "admin"}  # Default admin user
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# Track deleted files with timestamps
deleted_files = {}

# Function to handle client requests
def handle_client(client_socket):
    try:
        # Authenticate user
        credentials = client_socket.recv(BUFFER_SIZE).decode()
        username, password = credentials.split(":")
        if username in users and users[username] == password:
            client_socket.send(b"AUTH_SUCCESS")
        else:
            client_socket.send(b"AUTH_FAIL")
            client_socket.close()
            return

        while True:
            request = client_socket.recv(BUFFER_SIZE).decode()
            if not request:
                break

            command, *args = request.split()

            if command == "UPLOAD":
                filename = args[0]
                save_path = os.path.join(STORAGE_DIR, filename)
                with open(save_path, "wb") as f:
                    while True:
                        data = client_socket.recv(BUFFER_SIZE)
                        if not data or data == b"END":
                            break
                        f.write(data)
                client_socket.send(b"UPLOAD SUCCESS")

            elif command == "DOWNLOAD":
                filename = args[0]
                file_path = os.path.join(STORAGE_DIR, filename)
                if os.path.exists(file_path):
                    client_socket.send(b"FILE FOUND")
                    with open(file_path, "rb") as f:
                        while chunk := f.read(BUFFER_SIZE):
                            client_socket.send(chunk)
                    client_socket.send(b"END")
                else:
                    client_socket.send(b"FILE NOT FOUND")

            elif command == "SEARCH":
                keyword = args[0]
                files = [f for f in os.listdir(STORAGE_DIR) if keyword in f]
                client_socket.send("\n".join(files).encode() or b"NO FILES FOUND")

            elif command == "DELETE":
                filename = args[0]
                file_path = os.path.join(STORAGE_DIR, filename)
                if os.path.exists(file_path):
                    deleted_path = os.path.join(RECYCLE_BIN, filename)
                    os.rename(file_path, deleted_path)
                    deleted_files[deleted_path] = time.time()
                    client_socket.send(b"FILE MOVED TO RECYCLE BIN")
                else:
                    client_socket.send(b"FILE NOT FOUND")

            elif command == "RESTORE":
                filename = args[0]
                deleted_path = os.path.join(RECYCLE_BIN, filename)
                if os.path.exists(deleted_path):
                    os.rename(deleted_path, os.path.join(STORAGE_DIR, filename))
                    deleted_files.pop(deleted_path, None)
                    client_socket.send(b"FILE RESTORED")
                else:
                    client_socket.send(b"FILE NOT IN RECYCLE BIN")

            elif command == "BULK_DELETE":
                filenames = args
                for filename in filenames:
                    file_path = os.path.join(STORAGE_DIR, filename)
                    if os.path.exists(file_path):
                        deleted_path = os.path.join(RECYCLE_BIN, filename)
                        os.rename(file_path, deleted_path)
                        deleted_files[deleted_path] = time.time()
                client_socket.send(b"BULK DELETE SUCCESS")

            elif command == "BULK_RESTORE":
                filenames = args
                for filename in filenames:
                    deleted_path = os.path.join(RECYCLE_BIN, filename)
                    if os.path.exists(deleted_path):
                        os.rename(deleted_path, os.path.join(STORAGE_DIR, filename))
                        deleted_files.pop(deleted_path, None)
                client_socket.send(b"BULK RESTORE SUCCESS")

            else:
                client_socket.send(b"INVALID COMMAND")
    except:
        pass
    finally:
        client_socket.close()

# Function to clean up recycle bin
def cleanup_recycle_bin():
    while True:
        time.sleep(3600)  # Check every hour
        for file_path, timestamp in list(deleted_files.items()):
            if time.time() - timestamp > 30 * 24 * 3600:
                os.remove(file_path)
                deleted_files.pop(file_path)

# Start the server
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server started on {SERVER_HOST}:{SERVER_PORT}")

    threading.Thread(target=cleanup_recycle_bin, daemon=True).start()

    while True:
        client_socket, _ = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_server()