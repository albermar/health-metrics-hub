from app.business.interfaces import FileStorage_Interface


class LocalFileStorage(FileStorage_Interface):
    
    def __init__(self, base_path: str):
        self.base_path = base_path # e.g., "/data/uploads/"
    

    def save_uploaded_csv(self, file_bytes: bytes, filename: str) -> str:
        # Save the file to local storage and return the file path as file_id
        file_id = f"{self.base_path}/{filename}"
        with open(file_id, "wb") as f:
            f.write(file_bytes)
        return file_id        
    
    def move_csv_to_processed(self, file_id: str):
        pass
    
    def move_csv_to_unprocessable(self, file_id: str):
        pass