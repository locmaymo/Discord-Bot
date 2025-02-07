FROM python:3.11-slim

# Tạo thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements.txt và cài đặt phụ thuộc
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã bot vào container
COPY . .

# Lệnh chạy bot
CMD ["python", "miu.py"]