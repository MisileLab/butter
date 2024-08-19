FROM python:3.12.5-bullseye
RUN apt update && apt dist-upgrade -y && apt install -y firefox
RUN bash -c "curl -sSL https://pdm-project.org/install-pdm.py | python -"

ADD . /work
WORKDIR /work
RUN chmod +x ./run.sh
CMD ./run.sh
