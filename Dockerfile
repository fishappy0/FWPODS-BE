FROM python:3.9.19-alpine3.19
WORKDIR /usr/src/app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . .

RUN pip install --upgrade pip
RUN pip install -r ./backend/requirements.txt

EXPOSE 8069

CMD ["python", "./backend/manage.py", "runserver", ""]