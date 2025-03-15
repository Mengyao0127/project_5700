import unittest
import socket
import os
import time

# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000
BUFFER_SIZE = 4096
TEST_FILE = "test_upload.txt"
DOWNLOAD_FILE = "test_download.txt"
LARGE_FILE = "large_file.bin"
USERNAME = "admin"
PASSWORD = "admin"

def send_command(command):
    """Send a command to the server and get the response"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.send(command.encode())
        response = client_socket.recv(BUFFER_SIZE).decode()
        return response

def authenticate():
    """Authenticate with the server"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.send(f"{USERNAME}:{PASSWORD}".encode())
        response = client_socket.recv(BUFFER_SIZE).decode()
        return response == "AUTH_SUCCESS"

def upload_test_file(filename):
    """Upload a test file"""
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("This is a test file for upload.")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.send(f"UPLOAD {filename}".encode())
        with open(filename, "rb") as f:
            while chunk := f.read(BUFFER_SIZE):
                client_socket.send(chunk)
        client_socket.send(b"END")
        response = client_socket.recv(BUFFER_SIZE).decode()
        return response

def download_test_file(filename):
    """Download a test file"""
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
            return "DOWNLOAD SUCCESS"
        else:
            return "FILE NOT FOUND"

def delete_file(filename):
    """Delete a file"""
    response = send_command(f"DELETE {filename}")
    return response

def restore_file(filename):
    """Restore a file"""
    response = send_command(f"RESTORE {filename}")
    return response

def bulk_delete(filenames):
    """Bulk delete files"""
    response = send_command(f"BULK_DELETE {' '.join(filenames)}")
    return response

def bulk_restore(filenames):
    """Bulk restore files"""
    response = send_command(f"BULK_RESTORE {' '.join(filenames)}")
    return response

class TestFileSharing(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Authenticate before running tests"""
        if not authenticate():
            raise Exception("Authentication failed. Cannot proceed with tests.")

    def test_1_upload(self):
        """Test file upload"""
        response = upload_test_file(TEST_FILE)
        self.assertEqual(response, "UPLOAD SUCCESS")

    def test_2_search(self):
        """Test file search"""
        response = send_command(f"SEARCH {TEST_FILE}")
        self.assertIn(TEST_FILE, response)

    def test_3_download(self):
        """Test file download"""
        response = download_test_file(TEST_FILE)
        self.assertEqual(response, "DOWNLOAD SUCCESS")
        self.assertTrue(os.path.exists(DOWNLOAD_FILE))

    def test_4_delete(self):
        """Test file deletion"""
        response = delete_file(TEST_FILE)
        self.assertEqual(response, "FILE MOVED TO RECYCLE BIN")

    def test_5_restore(self):
        """Test file restoration"""
        response = restore_file(TEST_FILE)
        self.assertEqual(response, "FILE RESTORED")
        search_response = send_command(f"SEARCH {TEST_FILE}")
        self.assertIn(TEST_FILE, search_response)

    def test_6_bulk_delete(self):
        """Test bulk delete"""
        # Upload multiple files
        upload_test_file("file1.txt")
        upload_test_file("file2.txt")
        upload_test_file("file3.txt")

        # Bulk delete
        response = bulk_delete(["file1.txt", "file2.txt", "file3.txt"])
        self.assertEqual(response, "BULK DELETE SUCCESS")

        # Verify files are in the Recycle Bin
        search_response = send_command("SEARCH file1.txt")
        self.assertNotIn("file1.txt", search_response)
        search_response = send_command("SEARCH file2.txt")
        self.assertNotIn("file2.txt", search_response)
        search_response = send_command("SEARCH file3.txt")
        self.assertNotIn("file3.txt", search_response)

    def test_7_bulk_restore(self):
        """Test bulk restore"""
        # Bulk restore
        response = bulk_restore(["file1.txt", "file2.txt", "file3.txt"])
        self.assertEqual(response, "BULK RESTORE SUCCESS")

        # Verify files are restored
        search_response = send_command("SEARCH file1.txt")
        self.assertIn("file1.txt", search_response)
        search_response = send_command("SEARCH file2.txt")
        self.assertIn("file2.txt", search_response)
        search_response = send_command("SEARCH file3.txt")
        self.assertIn("file3.txt", search_response)

    def test_8_large_file_transfer(self):
        """Test large file transfer"""
        # Create a large file (10MB)
        with open(LARGE_FILE, "wb") as f:
            f.write(os.urandom(10 * 1024 * 1024))  # 10MB file

        # Upload large file
        response = upload_test_file(LARGE_FILE)
        self.assertEqual(response, "UPLOAD SUCCESS")

        # Download large file
        response = download_test_file(LARGE_FILE)
        self.assertEqual(response, "DOWNLOAD SUCCESS")
        self.assertTrue(os.path.exists(LARGE_FILE))

    def test_9_auto_delete_recycle_bin(self):
        """Test recycle bin auto-cleanup (simulate time passing)"""
        # Delete a file
        send_command(f"DELETE {TEST_FILE}")
        time.sleep(1)  # Simulate time passing
        send_command("CLEANUP")  # Trigger cleanup
        search_response = send_command(f"SEARCH {TEST_FILE}")
        self.assertNotIn(TEST_FILE, search_response)

    @classmethod
    def tearDownClass(cls):
        """Clean up test files after tests"""
        test_files = [TEST_FILE, DOWNLOAD_FILE, LARGE_FILE, "file1.txt", "file2.txt", "file3.txt"]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)

if __name__ == "__main__":
    unittest.main()