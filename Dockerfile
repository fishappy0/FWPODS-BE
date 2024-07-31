FROM python:3.9.19
WORKDIR /usr/src/app

COPY . .
RUN pip install --upgrade pip
RUN pip install -r ./backend/requirements.txt
RUN python ./backend/manage.py migrate --no-input
RUN python ./backend/manage.py collectstatic --no-input

EXPOSE 8040

CMD ["daphne", "-e", "ssl:443:privateKey=/usr/local/share/ca-certificates/priv.pem:certKey=/usr/local/share/ca-certificates/pub.pem", "backend.asgi:application"]
