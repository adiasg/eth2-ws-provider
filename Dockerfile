FROM python:3.8
COPY ./Makefile ./Makefile
RUN make docker
COPY ./ws_server.py ./ws_server.py
EXPOSE 80

# Provide your Eth2 API endpoint
ENV ETH2_API=

CMD [ "uwsgi", "--http", "0.0.0.0:80", \
               "--wsgi", "ws_server:app" ]
