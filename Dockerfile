FROM python:slim

WORKDIR /usr/local/share/safecoin-webinterface/

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]