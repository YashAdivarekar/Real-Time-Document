import grpc
from concurrent import futures
import time
import logging
import document_pb2
import document_pb2_grpc

# Logger configuration
logging.basicConfig(filename='changes.log', level=logging.INFO)

class DocumentService(document_pb2_grpc.DocumentServiceServicer):
    def __init__(self):
        self.clients = []  # List to keep track of client contexts
        self.document = self.load_document_from_log()  # Load initial document from log.txt

    def load_document_from_log(self):
        try:
            with open("log.txt", "r") as log_file:
                return log_file.read().strip()
        except FileNotFoundError:
            return ""  # Return empty document if log.txt doesn't exist

    def SyncDocument(self, request, context):
        # Update the document
        self.document = request.content
        
        # Log the change
        logging.info(f"Change from {request.client_id}: {request.content}")

        return document_pb2.DocumentResponse(status="Change received")

    def CheckForChanges(self, request, context):
        # Log the check for changes
        logging.info(f"Change check from {request.client_id}")

        # Send the updated document if there are changes
        if self.document:
            return document_pb2.DocumentUpdate(has_changes=1, content=self.document)
        else:
            return document_pb2.DocumentUpdate(has_changes=0, content="")

    def GetDocument(self, request, context):
        # Return the current state of the document for the logger
        return document_pb2.DocumentContent(content=self.document)

    def Subscribe(self, request, context):
        # Log the client ID and add the new client to the list
        logging.info(f"New client subscribed: {request.client_id}")

        # Add the new client context to the list
        self.clients.append(context)

        # Send the current document to the newly subscribed client
        yield document_pb2.DocumentChange(content=self.document, client_id="server")

        try:
            while True:
                time.sleep(1)  # Keep the connection alive
        finally:
            self.clients.remove(context)  # Remove the client when done
            logging.info(f"Client unsubscribed: {request.client_id}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    document_pb2_grpc.add_DocumentServiceServicer_to_server(DocumentService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started on port 50051.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
