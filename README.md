# Complete Data Pipeline to ingest flight booking data with CICD
##  Tech Stack - GitHub, GitHub Actions, Google Storage, PySpark, Dataproc Serverless, Airflow, BigQuery
     -> Process flight booking data in PySpark job to generate meaningful business insights
     -> Setup Airflow job to run PySpark job on Dataproc serverless
     -> Ingest transformed data into BigQuery tables
     -> Setup CICD process using GitHub actions to deploy code automatically in Dev/Prod environment

## Pipeline Architecture


![Airline_data_ingestion_pipeline_with_cicd](https://github.com/user-attachments/assets/1994cdb2-cc93-4e87-8210-1e89c9e504a1)
