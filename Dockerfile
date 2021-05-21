FROM python:3.8
COPY ./Makefile ./Makefile
RUN make docker
COPY ./ws_server.py ./ws_server.py
EXPOSE 8081

CMD [ "uwsgi", "/app/config.yml" ]
