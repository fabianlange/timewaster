FROM python:3.12 AS base

WORKDIR /app
COPY requirements.txt /app
RUN pip install -r /app/requirements.txt

FROM base AS http

COPY . /app
CMD ["python", "main.py"]


FROM base AS ssh

RUN apt update && apt install -y openssh-client
RUN ssh-keygen -f /root/ssh_host_key  -N ""

COPY . /app
CMD ["python", "ssh.py"]
