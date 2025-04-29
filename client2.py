import socket
import threading
import customtkinter as ctk
from cryptography.fernet import Fernet
from tkinter import messagebox

class SecureChatClient:
    def __init__(self):
        # UI Setup
        self.root = ctk.CTk()
        self.root.title("Secure Chat")
        self.root.geometry("500x600")
        
        # Configure theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Server connection frame
        self.connection_frame = ctk.CTkFrame(self.root)
        self.connection_frame.pack(pady=10, padx=10, fill="x")
        
        self.server_ip_entry = ctk.CTkEntry(self.connection_frame, placeholder_text="Server IP")
        self.server_ip_entry.pack(pady=5, padx=5, fill="x")
        self.server_ip_entry.insert(0, "127.0.0.1")
        
        self.port_entry = ctk.CTkEntry(self.connection_frame, placeholder_text="Port")
        self.port_entry.pack(pady=5, padx=5, fill="x")
        self.port_entry.insert(0, "55555")
        
        self.key_entry = ctk.CTkEntry(self.connection_frame, placeholder_text="Encryption Key")
        self.key_entry.pack(pady=5, padx=5, fill="x")
        
        self.nickname_entry = ctk.CTkEntry(self.connection_frame, placeholder_text="Nickname")
        self.nickname_entry.pack(pady=5, padx=5, fill="x")
        
        self.connect_button = ctk.CTkButton(
            self.connection_frame, 
            text="Connect", 
            command=self.connect_to_server
        )
        self.connect_button.pack(pady=5, padx=5, fill="x")
        
        # Chat frame
        self.chat_frame = ctk.CTkFrame(self.root)
        self.chat_display = ctk.CTkTextbox(self.chat_frame, state="disabled")
        self.chat_display.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.message_entry = ctk.CTkEntry(self.chat_frame, placeholder_text="Type your message...")
        self.message_entry.pack(pady=5, padx=10, fill="x")
        self.message_entry.bind("<Return>", self.send_message)
        
        self.send_button = ctk.CTkButton(
            self.chat_frame, 
            text="Send", 
            command=self.send_message
        )
        self.send_button.pack(pady=5, padx=10, fill="x")
        
        # Initialize connection variables
        self.client = None
        self.cipher = None
        self.nickname = ""
        
        self.root.mainloop()
    
    def connect_to_server(self):
        try:
            self.nickname = self.nickname_entry.get()
            if not self.nickname:
                messagebox.showerror("Error", "Please enter a nickname")
                return
                
            key = self.key_entry.get().encode()
            self.cipher = Fernet(key)
            
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((
                self.server_ip_entry.get(),
                int(self.port_entry.get())
            ))
            
            # Handle nickname exchange
            encrypted = self.client.recv(1024)
            if self.cipher.decrypt(encrypted).decode() == "NICK":
                self.client.send(self.cipher.encrypt(self.nickname.encode()))
                
            # Hide connection frame, show chat frame
            self.connection_frame.pack_forget()
            self.chat_frame.pack(pady=10, padx=10, fill="both", expand=True)
            
            # Start receive thread
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
    
    def receive_messages(self):
        while True:
            try:
                encrypted_msg = self.client.recv(1024)
                message = self.cipher.decrypt(encrypted_msg).decode()
                self.update_chat_display(message)
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.client.close()
                break
    
    def send_message(self, event=None):
        message = self.message_entry.get()
        if message:
            full_message = f"{self.nickname}: {message}"
            try:
                encrypted_msg = self.cipher.encrypt(full_message.encode())
                self.client.send(encrypted_msg)
                self.message_entry.delete(0, "end")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send message: {str(e)}")
    
    def update_chat_display(self, message):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", message + "\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

if __name__ == "__main__":
    client = SecureChatClient()
