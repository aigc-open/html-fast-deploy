FROM python:3.10-buster

# RUN echo "deb https://mirrors.aliyun.com/debian/ buster main contrib non-free" > /etc/apt/sources.list && \
#     echo "deb https://mirrors.aliyun.com/debian/ buster-updates main contrib non-free" >> /etc/apt/sources.list && \
#     echo "deb https://mirrors.aliyun.com/debian/ buster-backports main contrib non-free" >> /etc/apt/sources.list && \
#     echo "deb https://mirrors.aliyun.com/debian-security/ buster/updates main contrib non-free" >> /etc/apt/sources.list

RUN apt-get update && \
    apt-get install -y gcc libc-dev default-mysql-client default-libmysqlclient-dev nginx libsasl2-dev libldap2-dev libssl-dev zip jq && \
    apt-get clean

RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com


WORKDIR /workspace

# 安装本项目
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt 

COPY . /app/

ENTRYPOINT []

WORKDIR /app


CMD ["python3", "run.py"]





