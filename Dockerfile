FROM python:3.10-bullseye

WORKDIR /usr/src/app

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY ./src ./src

EXPOSE 8000

CMD [ "uvicorn", "src.main:app", "--reload" ]