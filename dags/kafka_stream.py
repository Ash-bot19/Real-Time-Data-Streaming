from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator

def get_data():
    import requests
    r = requests.get("https://randomuser.me/api/", timeout=15)
    r.raise_for_status()
    return r.json()['results'][0]

def format_data(res):
    loc = res['location']
    return {
        'first_name': res['name']['first'],
        'last_name': res['name']['last'],
        'gender': res['gender'],
        'address': f"{loc['street']['number']} {loc['street']['name']}, "
                   f"{loc['city']}, {loc['state']}, {loc['country']} {loc['postcode']}",
        'email': res['email'],
        'username': res['login']['username'],
        'dob': res['dob']['date'],
        'registered': res['registered']['date'],
        'phone': res['phone'],
        'picture': res['picture']['medium'],
    }

def stream_to_kafka():
    import json, logging, time
    from kafka import KafkaProducer

    producer = KafkaProducer(
        bootstrap_servers=['broker:29092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        retries=3,
        linger_ms=50,
        request_timeout_ms=10000,
        max_block_ms=10000,
    )

    for _ in range(5):
        try:
            res = get_data()
            data = format_data(res)
            producer.send('users_created', data)
            logging.info("Sent user %s", data['username'])
            time.sleep(1)
        except Exception as e:
            import traceback
            logging.error(traceback.format_exc())
            raise


default_args = {'owner': 'airflow', 'start_date': datetime(2023, 9, 3, 10, 0)}

with DAG(
    dag_id='user_automation_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:
    stream_task = PythonOperator(
        task_id='stream_data_from_api',
        python_callable=stream_to_kafka,
    )

