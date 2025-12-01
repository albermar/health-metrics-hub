* CSV general info
    - Only accept CSV via POST endpoint with AUTH Key
    - We receive a CSV with health info. We must extract data and store in our DB. 
    - We must check repeated rows, type errors, columns mispelling, etc
    - CSV file name won't be important (only columns inside)
    - Column expected names are point 1 ones
    - Columns may not be ordered
    - Received CSVs will be saved in folder input_files/
    - Processed CSVs will be moved from input_files/ to input_files/processed/
    - CSVs illegibles or with any kind of error that makes it impossible to process data will be moved to input_files/unprocessable

* CSV Columns (Received in POST endpoint)
    - date
    - steps_n
    - proteins_g
    - kcal_in
    - kcal_junk_in
    - kcal_out_training
    - sleep_hours
    - stress_rel
    - weight_kg
    - waist_cm