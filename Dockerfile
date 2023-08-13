FROM pmariglia/gambit-docker as debian-with-gambit

FROM python:3.8-slim

COPY --from=debian-with-gambit /usr/local/bin/gambit-enummixed /usr/local/bin

WORKDIR /showdown

ARG BATTLE_BOT=abluble
ENV BATTLE_BOT=$BATTLE_BOT

ARG WEBSOCKET_URI=sim.smogon.com:8000
ENV WEBSOCKET_URI=$WEBSOCKET_URI

ARG PS_USERNAME
ENV PS_USERNAME=$PS_USERNAME

ARG PS_PASSWORD
ENV PS_PASSWORD=$PS_PASSWORD

ARG BOT_MODE=ACCEPT_CHALLENGE
ENV BOT_MODE=$BOT_MODE

ARG POKEMON_MODE=gen3ubers
ENV POKEMON_MODE=$POKEMON_MODE

ARG TEAM_NAME=desafiopokemon/current
ENV TEAM_NAME=$TEAM_NAME

COPY requirements.txt /showdown/requirements.txt
COPY requirements-docker.txt /showdown/requirements-docker.txt

RUN pip3 install -r requirements.txt
RUN pip3 install -r requirements-docker.txt

COPY config.py /showdown/config.py
COPY constants.py /showdown/constants.py
COPY data /showdown/data
COPY run.py /showdown/run.py
COPY showdown /showdown/showdown
COPY teams /showdown/teams
COPY teambuilderdata /showdown/teambuilderdata

ENV PYTHONIOENCODING=utf-8

CMD ["python3", "run.py"]
