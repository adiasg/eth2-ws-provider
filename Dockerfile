FROM python:3.8
COPY ./Makefile ./Makefile
RUN make docker
COPY ./ws_server.py ./ws_server.py
EXPOSE 80
COPY ./uwsgi_config.ini ./uwsgi_config.ini

CMD [ "uwsgi", "uwsgi_config.ini" ]
