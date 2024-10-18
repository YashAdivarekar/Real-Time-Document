import grpc
import tkinter as tk
from tkinter import scrolledtext
import document_pb2
import document_pb2_grpc
import threading
import time

class DocumentClient:
    def __init__(self, client_id):
        self.client_id = client_id
        self.content = ""
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = document_pb2_grpc.DocumentServiceStub(self.channel)
        self.root = tk.Tk()
        self.root.title("Collaborative Document Editor")
        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.text_area.pack(expand=True, fill='both')
        self.text_area.bind("<KeyRelease>", self.on_key_release)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Subscribe to document changes in a separate thread
        threading.Thread(target=self.subscribe_to_changes, daemon=True).start()

        # Start a thread for polling changes
        threading.Thread(target=self.poll_for_changes, daemon=True).start()

    def on_key_release(self, event):
        self.content = self.text_area.get("1.0", tk.END).strip()
        if self.content:  # Only send non-empty content
            try:
                self.stub.SyncDocument(document_pb2.DocumentChange(client_id=self.client_id, content=self.content))
            except grpc.RpcError as e:
                print(f"Failed to sync document: {e}")

    def subscribe_to_changes(self):
        # Send subscribe request
        request = document_pb2.SubscribeRequest(client_id=self.client_id)
        # for change in self.stub.Subscribe(request):
        #     self.update_content(change)

    def poll_for_changes(self):
        while True:
            try:
                request = document_pb2.ChangeCheckRequest(client_id=self.client_id)
                response = self.stub.CheckForChanges(request)

                if response.content != self.content:
                    self.update_content(document_pb2.DocumentChange(content=response.content, client_id="server"))
                
            except grpc.RpcError as e:
                print(f"Error checking for changes: {e}")
                
            time.sleep(1)  # Poll every 1 seconds

    def update_content(self, change):
        if change.client_id != self.client_id:  # Prevent overwriting self's content
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, change.content)

    def on_closing(self):
        self.channel.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    client_id = input("Enter your client ID: ")
    client = DocumentClient(client_id)
    client.run()
