from app.domain.entities import DailyMetricsInput, DailyKPIsOutput
from datetime import datetime

#We use ABC module to create abstract base classes (interfaces)
#abstractmethod decorator to define abstract methods that must be implemented by subclasses
from abc import ABC, abstractmethod #-> Compile-time protection. Prevents instantiation, forces implementation, makes contracts explicit. fits perfectly with clean architecture ports and adapters.

#The interface should represent the minimum operations your use cases actually need.

#-----------------------------------------------------------------------------------------
#----------------------------------REPOSITORY INTERFACES----------------------------------
#-----------------------------------------------------------------------------------------
class InputRepository_Interface(ABC):
        """
        Port for saving and fetching DailyMetricsInput entities.
        """
        @abstractmethod
        def save_input(self, input_data: DailyMetricsInput) -> None :
            raise NotImplementedError
        
        @abstractmethod
        def get_input(self, start: datetime, end: datetime) -> list[DailyMetricsInput]:
            raise NotImplementedError
    

class OutputRepository_Interface(ABC):
        """
        Port for saving and fetching DailyKPIsOutput entities.
        """
        @abstractmethod
        def save_output(self, output_data: list[DailyKPIsOutput]) -> None :
            raise NotImplementedError
        
        @abstractmethod
        def get_output(self, start: datetime, end: datetime) -> list[DailyKPIsOutput]:
            raise NotImplementedError


#-----------------------------------------------------------------------------------------
#------------------------------------STORAGE INTERFACE------------------------------------
#-----------------------------------------------------------------------------------------

class InputFileStorage_Interface(ABC):
        """
        Port for handling CSV files uploaded through the API.
        Note: this port must be storage-agnostic (local, S3, etc.)
        """
        @abstractmethod
        def save_uploaded_csv(self, file_bytes: bytes, filename: str) -> str:
            """
            Persist the uploaded CSV file and return a storage-agnostic file_id.
            file_id can be a filename, UUID, blob key, etc.
            """            
            raise NotImplementedError
        
        @abstractmethod
        def move_csv_to_processed(self, file_id: str):
            raise NotImplementedError
        
        @abstractmethod
        def move_csv_to_unprocessable(self, file_id: str):
            raise NotImplementedError
        

"""
Why use bytes:
    Uploaded files arrive as raw bytes. Storage layers should operate on binary
    data to avoid encoding issues.

Why raise NotImplementedError:
    Ensures subclasses are forced to implement the methods.
    Prevents accidental instantiation of incomplete implementations.
"""