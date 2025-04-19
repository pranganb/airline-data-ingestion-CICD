from datetime import datetime, timedelta
import uuid
from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import DataprocCreateBatchOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.models import Variable

# DAG default arguments

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries' : 1,
    'retry_delay' : timedelta(minutes = 5),
    'start_date': datetime(2025, 4, 20)
}

# Define DAG
with DAG(
    dag_id = "flight_booking_dataproc_bq_dag",
    default_args = default_args,
    schedule_interval = None,
    catchup = False
) as dag:
    
    # Fetch environment variables
    env = Variable.get("env", default_var = "dev")
    gcs_bucket = Variable.get("gcs_bucket", default_var = "mybucket-airflow")
    bq_project = Variable.get("bq_project", default_var="warm-tome-457114-a0")
    bq_dataset = Variable.get("bq_dataset", default_var=f"flight_data_{env}")
    tables = Variable.get("tables", deserialize_json=True)

    # Extract table names from the 'tables' variable
    transformed_table = tables["transformed_table"]
    route_insights_table = tables["route_insights_table"]
    origin_insights_table = tables["origin_insights_table"]

    # Generate a unique batch ID using UUID
    batch_id = f"flight-booking-batch-{env}-{str(uuid.uuid4())[:8]}"   # Shortened UUID for brevity

    # # task 1: File censor for GCS

    file_sensor = GCSObjectExistenceSensor(
        task_id = "check_file_arrival",
        bucket = gcs_bucket,
        object = f"airline_data/source-{env}/flight_booking.csv",
        google_cloud_conn_id = "google_cloud_default",
        timeout = 300,
        poke_interval = 30, #time between checks
        mode = "poke",  #Blocking mode
    )


    # task 2: Submit Job to Dataproc Serverless
    batch_details = {
        "pyspark_batch" : {
            "main_python_file_uri" : f"gs://{gcs_bucket}/mybucket-airflow/spark-job/spark_job.py",
            "python_file_uris": [], # Python WHL files
            "jar_file_uris": [], #JAR files
            "args": [
                f"--env = {env}",
                f"--bq_project={bq_project}",
                f"--bq_dataset={bq_dataset}",
                f"--transformed_table={transformed_table}",
                f"--route_insights_table={route_insights_table}",
                f"--origin_insights_table={origin_insights_table}",
            ]
        },
        "runtime_config": {
            "version" : "2.2"
        },
        "environment_config": {
            "execution_config": {
                "service_account" : "407250823299-compute@developer.gserviceaccount.com",
                "network_uri": "projects/warm-tome-457114-a0/global/networks/default",
                "subnetwork_uri": "projects/warm-tome-457114-a0/regions/us-central1/subnetworks/default",
            }
        },
    }

    pyspark_task = DataprocCreateBatchOperator(
        task_id = "run_spark_job_on_dataproc_serverless",
        batch = batch_details,
        batch_id = batch_id,
        project_id = "warm-tome-457114-a0",
        region = "us-central1",
        gcp_conn_id = "google_cloud_default"
    )

    # Task Dependencies
    file_sensor >> pyspark_task