from app.business.interfaces import CSVParser_Interface

import csv
from io import StringIO
from app.domain.entities import DailyMetricsInput
from datetime import datetime

class CsvParserV1(CSVParser_Interface):
    '''
    CSV Parser implementation (Infrastructure layer)
    '''
    def parse_csv(self, file_bytes: bytes) -> list[DailyMetricsInput]:

        decoded_file = file_bytes.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(decoded_file))
        
        parsed_entities = []
        
        for row in csv_reader:
            entity = DailyMetricsInput(
                date=datetime.strptime(row['date'], '%Y-%m-%d'),
                kcal_in=int(row['kcal_in']),
                kcal_out=int(row['kcal_out']),
                steps=int(row['steps']),
                sleep_hours=float(row['sleep_hours']) 
                
            )
            parsed_entities.append(entity)
        
        return parsed_entities