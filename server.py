import socket
import threading
from cryptography.fernet import Fernet
import time

class SecureChatServer:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 55555
        self.server = None
        self.clients = []
        self.nicknames = []
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.running = False

    def broadcast(self, message):
        for client in self.clients:
            try:
                encrypted_msg = self.cipher.encrypt(message.encode())
                client.send(encrypted_msg)
            except:
                self.remove_client(client)

    def remove_client(self, client):
        if client in self.clients:
            index = self.clients.index(client)
            self.clients.remove(client)
            nickname = self.nicknames[index]
            self.broadcast(f"{nickname} left the chat!")
            self.nicknames.remove(nickname)
            client.close()

    def handle_client(self, client):
        while self.running:
            try:
                encrypted_msg = client.recv(1024)
                if not encrypted_msg:
                    break
                message = self.cipher.decrypt(encrypted_msg).decode()
                self.broadcast(message)
            except:
                self.remove_client(client)
                break

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server.bind((self.host, self.port))
        except OSError as e:
            print(f"Failed to bind to port {self.port}: {e}")
            return False
            
        self.server.listen()
        self.running = True
        
        print(f"Server started on {self.host}:{self.port}")
        print(f"Encryption key: {self.key.decode()}")
        print("Waiting for connections...")
        
        try:
            while self.running:
                client, address = self.server.accept()
                print(f"Connected with {address}")

                client.send(self.cipher.encrypt("NICK".encode()))
                nickname = self.cipher.decrypt(client.recv(1024)).decode()

                self.nicknames.append(nickname)
                self.clients.append(client)

                print(f"Nickname: {nickname}")
                self.broadcast(f"{nickname} joined the chat!")
                client.send(self.cipher.encrypt("Connected to secure chat!".encode()))

                thread = threading.Thread(target=self.handle_client, args=(client,))
                thread.start()
        except KeyboardInterrupt:
            print("Shutting down server...")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        for client in self.clients:
            client.close()
        if self.server:
            self.server.close()
        print("Server stopped")

if __name__ == "__main__":
    server = SecureChatServer()
    try:
        server.start()
    except Exception as e:
        print(f"Server error: {e}")
        server.stop()
