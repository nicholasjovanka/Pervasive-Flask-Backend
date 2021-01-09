FROM python:3.7.9

WORKDIR /usr/app

COPY ./requirements.txt ./
RUN pip install -r requirements.txt
COPY ./ ./

CMD ["gunicorn", "main:app" ,"-b", "0.0.0.0:8000"]