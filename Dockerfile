FROM python:3.12

WORKDIR /app
COPY requirements.txt /app
RUN pip install -r /app/requirements.txt
COPY main.py /app

CMD ["python", "main.py"]
