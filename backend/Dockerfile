FROM python:3.9-slim
WORKDIR /app
RUN python -m pip install --upgrade pip setuptools

COPY ../requirements.txt /app
RUN pip install --upgrade pip
RUN python -m pip install -r requirements.txt

COPY . /app
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ]