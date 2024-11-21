FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Đảm bảo tệp .env được copy
COPY .env .env

CMD ["python", "SillyTavern.py"]