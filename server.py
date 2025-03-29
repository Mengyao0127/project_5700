import socket
import threading
import os

SERVER_HOST = "localhost"
SERVER_PORT = 5001
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

FILES_DIR = "server_files"
RECYCLE_BIN = "recycle_bin"
USERS = {
    "alice": "1234"
}


sessions = {}

if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)
if not os.path.exists(RECYCLE_BIN):
    os.makedirs(RECYCLE_BIN)

def handle_client(client_socket):
    token = None
    try:
        while True:
            command = client_socket.recv(BUFFER_SIZE).decode()
            if not command:
                break

            parts = command.split(SEPARATOR)
            if parts[0] == "UPLOAD":
                _, token, filename, filesize = parts
                filesize = int(filesize)
                filepath = os.path.join(FILES_DIR, filename)
                with open(filepath, "wb") as f:
                    received = 0
                    while received < filesize:
                        data = client_socket.recv(min(BUFFER_SIZE, filesize - received))
                        if not data:
                            break
                        f.write(data)
                        received += len(data)
                client_socket.send(f"{filename} uploaded successfully.".encode())

            elif parts[0] == "DOWNLOAD":
                _, token, filename = parts
                filepath = os.path.join(FILES_DIR, filename)
                if not os.path.exists(filepath):
                    client_socket.send(f"ERROR: File {filename} not found.".encode())
                    continue
                size = os.path.getsize(filepath)
                client_socket.send(f"{filename}{SEPARATOR}{size}".encode())
                with open(filepath, "rb") as f:
                    while chunk := f.read(BUFFER_SIZE):
                        client_socket.sendall(chunk)

            elif parts[0] == "SEARCH":
                _, token, keyword = parts if len(parts) > 2 else ("", "", "")
                matches = [f for f in os.listdir(FILES_DIR) if keyword.lower() in f.lower()]
                client_socket.send(SEPARATOR.join(matches).encode())

            elif parts[0] == "DELETE":
                _, token, filename = parts
                filepath = os.path.join(FILES_DIR, filename)
                if os.path.exists(filepath):
                    os.rename(filepath, os.path.join(RECYCLE_BIN, filename))
                    client_socket.send(f"{filename} moved to recycle bin.".encode())
                else:
                    client_socket.send(f"File {filename} not found.".encode())

            elif parts[0] == "RESTORE":
                _, token, filename = parts
                filepath = os.path.join(RECYCLE_BIN, filename)
                if os.path.exists(filepath):
                    os.rename(filepath, os.path.join(FILES_DIR, filename))
                    client_socket.send(f"{filename} restored.".encode())
                else:
                    client_socket.send(f"File {filename} not found in recycle bin.".encode())

            elif parts[0] == "SEARCH_RECYCLE":
                _, token, keyword = parts
                matches = [f for f in os.listdir(RECYCLE_BIN) if keyword.lower() in f.lower()]
                client_socket.send(SEPARATOR.join(matches).encode())

            else:
                # Handle Login
                username, password = parts[0], parts[1]
                if username in USERS and USERS[username] == password:
                    token = username
                    sessions[token] = client_socket
                    client_socket.send(f"AUTH_SUCCESS{SEPARATOR}{token}".encode())
                else:
                    client_socket.send("AUTH_FAILED".encode())
                    break
    except Exception as e:
        print(f"Client error: {e}")
    finally:
        client_socket.close()
        if token in sessions:
            del sessions[token]

def start_server():
    server = socket.socket()
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(5)
    print(f"[*] Server listening on {SERVER_HOST}:{SERVER_PORT}")
    while True:
        client_socket, _ = server.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_server()
