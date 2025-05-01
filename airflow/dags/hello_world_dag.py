from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from datetime import timedelta

default_args = {
    "owner": "airflow",
    "start_date": datetime(2025, 1, 1),
    "retries": 5,
    "retry_delay": timedelta(minutes=5),
}

def get_age(ti):
    # This function will be called by the PythonOperator
    # and will return the age of the user.
    age = 5
    ti.xcom_push(key='age', value=age)
    return age

with DAG(
    dag_id="create_python_dag_v06",
    default_args=default_args,
    description="A simple hello world DAG and our first python DAG",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",  # ← use `schedule_interval`, not `schedule`
    catchup=False,
    tags=["example"],
) as dag:
    def say_hello(age, ti):
        # This function will be called by the PythonOperator
        # and will print a greeting message.
        first_name = ti.xcom_pull(task_ids="get_name", key="first_name")
        last_name = ti.xcom_pull(task_ids="get_name", key="last_name")
        name = f"{first_name} {last_name}"
        age = ti.xcom_pull(task_ids="get_age", key="age")
        print(f"👋 Hello, {name}! You are {age} years old.")

    def get_name(ti):
        ti.xcom_push(key='first_name', value='Jerry')
        ti.xcom_push(key='last_name', value='Fridman')

    task1 = PythonOperator(
        task_id="say_hello",
        python_callable=say_hello,
        op_kwargs={"age": 5},
    )

    task2 = PythonOperator(
        task_id="get_name",
        python_callable=get_name,
    )

    task3 = PythonOperator(
        task_id="get_age",
        python_callable=get_age,
    )

    [task2, task3] >> task1  # This sets the task dependencies
