# Standard Airflow imports for DAG structure
from airflow.sdk import dag, task
from airflow.operators.python import BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule
import pendulum
import random
import logging

# -----------------------------------------------------------------------------
# Default arguments applied to all tasks unless overridden
# -----------------------------------------------------------------------------
default_args = {
    "owner": "airflow",
    "retries": 3,  # Any task will retry up to 3 times on failure
    "retry_delay": pendulum.duration(minutes=5),  # Wait 5 minutes between retries
    "retry_exponential_backoff": True,  # Each retry will wait longer to reduce system pressure
}

# -----------------------------------------------------------------------------
# Mock Slack alert function — would actually send a Slack alert in real-world
# -----------------------------------------------------------------------------
def slack_alert(context):
    logging.error(f"🚨 ALERT: Task {context['task_instance_key_str']} failed!")

# -----------------------------------------------------------------------------
# Define the DAG (overall container of all tasks and logic)
# -----------------------------------------------------------------------------
@dag(
    dag_id="resilient_etl_pipeline",  # Unique DAG name
    default_args=default_args,  # Apply defaults
    schedule="@daily",  # This DAG runs once per day
    catchup=False,  # Skip missed runs between start_date and now
    start_date=pendulum.datetime(2025, 1, 1),
    sla_miss_callback=slack_alert,  # If any task misses SLA, trigger alert
    tags=["resilient", "fallback", "sla"],  # Helpful UI tagging
)
def resilient_etl_pipeline():
    # -----------------------------------------------------------------------------
    # 1. Start dummy task (helps structure visualization)
    # -----------------------------------------------------------------------------
    start = EmptyOperator(task_id="start")

    # -----------------------------------------------------------------------------
    # 2. Branching: Decide whether to use Primary or Backup source
    # -----------------------------------------------------------------------------
    def is_primary_source_up():
        # Randomly simulate whether the primary system is available
        if random.choice([True, False]):
            return "primary_pull"  # Go to primary_pull task
        else:
            return "backup_pull"  # Go to backup_pull task

    branch = BranchPythonOperator(
        task_id="branch_decision",
        python_callable=is_primary_source_up,  # This function determines the path
    )

    # -----------------------------------------------------------------------------
    # 3. Primary pull task
    # -----------------------------------------------------------------------------
    @task(
        retries=2,  # This task can fail twice before giving up
        retry_delay=pendulum.duration(minutes=2),  # Wait 2 minutes between retries
        sla=pendulum.duration(minutes=10),  # SLA: if takes >10 mins, trigger an SLA miss
        on_failure_callback=slack_alert,  # Alert ops on final failure
        task_id="primary_pull"
    )
    def primary_pull():
        logging.info("🟦 Pulling from Primary Source...")
        if random.random() < 0.7:  # 70% chance we simulate a failure
            raise Exception("Primary source down!")
        return {"data": "primary_data"}  # Simulated data pull

    # -----------------------------------------------------------------------------
    # 4. Backup pull task
    # -----------------------------------------------------------------------------
    @task(
        retries=1,  # One retry allowed here — backup expected to be more reliable
        retry_delay=pendulum.duration(minutes=3),
        task_id="backup_pull"
    )
    def backup_pull():
        logging.info("🟧 Pulling from Backup Source...")
        return {"data": "backup_data"}  # Simulated backup data pull

    # -----------------------------------------------------------------------------
    # 5. Combine Results task
    # Trigger Rule: ONE_SUCCESS
    # -----------------------------------------------------------------------------
    @task(
        trigger_rule=TriggerRule.ONE_SUCCESS,
        task_id="combine_results"
    )
    def combine_results(primary_result=None, backup_result=None):
        # Only need one of primary or backup to continue
        logging.info(f"🧩 Combining Results: primary={primary_result}, backup={backup_result}")
        return primary_result or backup_result  # Prefer primary if available

    # -----------------------------------------------------------------------------
    # 6. Transform task
    # -----------------------------------------------------------------------------
    @task(task_id="transform")
    def transform(data):
        logging.info(f"🔵 Transforming Data: {data}")
        transformed_data = {"transformed_data": f"processed_{data['data']}"}
        return transformed_data  # Cleaned-up, processed data

    # -----------------------------------------------------------------------------
    # 7. Load to DB task (designed to be idempotent)
    # -----------------------------------------------------------------------------
    @task(task_id="load_to_db")
    def load_to_db(data):
        logging.info(f"🟩 Loading into DB (idempotent merge logic): {data}")
        # Here, assume real system would use UPSERT/MERGE so re-running doesn't double-insert
        return "Load Complete"

    # -----------------------------------------------------------------------------
    # 8. Success dummy task
    # -----------------------------------------------------------------------------
    success = EmptyOperator(task_id="success")

    # -----------------------------------------------------------------------------
    # Wiring up the flow (defining task dependencies)
    # -----------------------------------------------------------------------------
    start >> branch
    primary_pull_task = primary_pull()
    backup_pull_task = backup_pull()

    branch >> primary_pull_task
    branch >> backup_pull_task

    combine_results_task = combine_results(
        primary_result=primary_pull_task,
        backup_result=backup_pull_task
    )

    transform_task = transform(combine_results_task)
    load_task = load_to_db(transform_task)
    load_task >> success

# Create the DAG instance
resilient_etl_pipeline_dag = resilient_etl_pipeline()
