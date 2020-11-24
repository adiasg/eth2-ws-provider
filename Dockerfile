FROM python:3.8
COPY ./Makefile ./Makefile
RUN make docker
COPY ./ws_server.py ./ws_server.py
EXPOSE 80

CMD [ "uwsgi", "/app/my_config.yml" ]
