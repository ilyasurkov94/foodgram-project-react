FROM python:3.9-slim

WORKDIR /app
COPY ./requirements.txt .

RUN pip install --upgrade pip
RUN python -m pip install -r requirements.txt

COPY . /app

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ]