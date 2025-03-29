import socket
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os

SERVER_HOST = "localhost"
SERVER_PORT = 5001
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

token = None
client_socket = None
file_listbox = None

def login():
    global token, client_socket
    username = simpledialog.askstring("Login", "Username:")
    password = simpledialog.askstring("Login", "Password:", show='*')
    client_socket = socket.socket()
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    client_socket.send(f"{username}{SEPARATOR}{password}".encode())
    response = client_socket.recv(BUFFER_SIZE).decode()

    if response.startswith("AUTH_SUCCESS"):
        token = response.split(SEPARATOR)[1]
        messagebox.showinfo("Success", "Login successful.")
    else:
        messagebox.showerror("Error", "Login failed.")
        client_socket.close()
        client_socket = None

def upload_file():
    filepath = filedialog.askopenfilename()
    if not filepath or not client_socket:
        return
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    client_socket.send(f"UPLOAD{SEPARATOR}{token}{SEPARATOR}{filename}{SEPARATOR}{filesize}".encode())

    with open(filepath, "rb") as f:
        while chunk := f.read(BUFFER_SIZE):
            client_socket.sendall(chunk)
    messagebox.showinfo("Uploaded", f"{filename} uploaded successfully.")

def download_file(filename=None):
    if not filename:
        filename = simpledialog.askstring("Download", "Filename to download:")
    if not client_socket or not filename:
        return
    client_socket.send(f"DOWNLOAD{SEPARATOR}{token}{SEPARATOR}{filename}".encode())
    response = client_socket.recv(BUFFER_SIZE).decode()

    if response.startswith("ERROR"):
        messagebox.showerror("Error", response)
        return

    # ✅ 再确认是否是有效的文件信息
    parts = response.split(SEPARATOR)
    if len(parts) != 2:
        messagebox.showerror("Error", f"Invalid server response: {response}")
        return

    name, size = parts
    try:
        size = int(size)
    except ValueError:
        messagebox.showerror("Error", f"Invalid file size: {size}")
        return

    # ✅ 开始接收文件
    with open(f"downloaded_{name}", "wb") as f:
        received = 0
        while received < size:
            data = client_socket.recv(min(BUFFER_SIZE, size - received))
            if not data:
                break
            f.write(data)
            received += len(data)
    messagebox.showinfo("Downloaded", f"{name} saved as downloaded_{name}")



def search_files():
    keyword = simpledialog.askstring("Search", "Keyword:")
    if not keyword:
        return
    client_socket.send(f"SEARCH{SEPARATOR}{token}{SEPARATOR}{keyword}".encode())
    result = client_socket.recv(BUFFER_SIZE).decode()
    files = result.split(SEPARATOR)
    messagebox.showinfo("Search Results", "\n".join(files) if files[0] else "No results.")

def delete_file():
    filename = simpledialog.askstring("Delete", "Filename to delete:")
    client_socket.send(f"DELETE{SEPARATOR}{token}{SEPARATOR}{filename}".encode())
    msg = client_socket.recv(BUFFER_SIZE).decode()
    messagebox.showinfo("Delete", msg)

def restore_file():
    filename = simpledialog.askstring("Restore", "Filename to restore:")
    if not client_socket or not filename:
        return
    client_socket.send(f"RESTORE{SEPARATOR}{token}{SEPARATOR}{filename}".encode())
    response = client_socket.recv(BUFFER_SIZE).decode()
    messagebox.showinfo("Restore", response)

def search_recycle_bin():
    keyword = simpledialog.askstring("Search Recycle Bin", "Keyword:")
    client_socket.send(f"SEARCH_RECYCLE{SEPARATOR}{token}{SEPARATOR}{keyword}".encode())
    result = client_socket.recv(BUFFER_SIZE).decode()
    files = result.split(SEPARATOR)
    messagebox.showinfo("Recycle Bin Search Results", "\n".join(files) if files[0] else "No results.")

def refresh_file_list():
    if not client_socket:
        messagebox.showerror("Error", "Please login first.")
        return
    try:
        client_socket.send(f"SEARCH{SEPARATOR}{token}{SEPARATOR}".encode())
        result = client_socket.recv(BUFFER_SIZE).decode()
        files = result.split(SEPARATOR)
        file_listbox.delete(0, tk.END)
        for file in files:
            if file:
                file_listbox.insert(tk.END, file)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to refresh file list: {e}")

def on_file_double_click(event):
    selected_file = file_listbox.get(file_listbox.curselection())
    if selected_file:
        download_file(selected_file)

def setup_ui():
    global file_listbox
    root = tk.Tk()
    root.title("File Sharing App")

    tk.Button(root, text="Login", command=login).pack(pady=5)
    tk.Button(root, text="Upload File", command=upload_file).pack(pady=5)
    tk.Button(root, text="Download File", command=download_file).pack(pady=5)
    tk.Button(root, text="Search File", command=search_files).pack(pady=5)
    tk.Button(root, text="Delete File", command=delete_file).pack(pady=5)
    tk.Button(root, text="Restore File", command=restore_file).pack(pady=5)
    tk.Button(root, text="Search Recycle Bin", command=search_recycle_bin).pack(pady=5)
    tk.Button(root, text="Refresh File List", command=refresh_file_list).pack(pady=5)

    # ✅ 你漏掉了这块
    file_listbox = tk.Listbox(root, width=50, height=15)
    file_listbox.pack(pady=10)
    file_listbox.bind("<Double-1>", on_file_double_click)

    root.mainloop()

if __name__ == "__main__":
    setup_ui()
