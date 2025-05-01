FROM apache/airflow:3.0.0

# copy your new requirements
COPY requirements.txt /requirements.txt

# upgrade pip & install your deps globally
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r /requirements.txt
