import grpc
import time
import document_pb2
import document_pb2_grpc

def read_log_file():
    try:
        with open("log.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""

def write_log_file(content):
    with open("log.txt", "w") as file:
        file.write(content)

def check_and_update_document():
    # Establish gRPC channel
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = document_pb2_grpc.DocumentServiceStub(channel)
        
        # Request the current document from the server
        response = stub.GetDocument(document_pb2.Empty())
        server_document = response.content
        
        # Read the local log file
        log_document = read_log_file()

        # Compare documents
        if server_document != log_document:
            print("Document has changed, updating log.txt")
            write_log_file(server_document)
        else:
            print("No changes in the document.")

if __name__ == "__main__":
    while True:
        check_and_update_document()
        time.sleep(5)  # Check for changes every 5 seconds
