# Sử dụng base image với Java 17 và Python 3.9
FROM openjdk:17-jdk-slim-buster

# Cài đặt Python và pip (nếu không có sẵn)
RUN apt-get update && \
    apt-get install -y python3 python3-pip unzip && \ # Thêm unzip để giải nén nếu cần
    rm -rf /var/lib/apt/lists/*

# Tạo thư mục làm việc trong container
WORKDIR /app

# Sao chép các tệp backend
COPY backend/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Tạo các thư mục cần thiết cho validator và các gói FHIR
# Thư mục chứa validator.jar và các gói IG
RUN mkdir -p /app/validator-data/packages
# Thư mục tạm thời cho file JSON đầu vào
RUN mkdir -p /app/targets

# Sao chép validator.jar và các gói .tgz vào vị trí đã định
COPY validator-data/validator_cli.jar /app/validator-data/
COPY validator-data/packages/*.tgz /app/validator-data/packages/

# --- BƯỚC MỚI: PRE-CACHE CÁC GÓI FHIR CORE SỬ DỤNG VALIDATOR ---
# Sao chép gói FHIR Core (zip hoặc tgz) vào một thư mục tạm thời
# Đảm bảo fhir-core-pkg.zip có trong validator-data/
COPY validator-data/fhir-core-pkg.zip /tmp/fhir-core-pkg.zip

# Chạy validator một lần để nó tự động tải và cache các gói core cần thiết
# Đây là một thủ thuật để validator tự thiết lập cache của nó
# Chúng ta sẽ chạy một lệnh validation đơn giản với một file dummy
# để validator khởi tạo và tải các gói mà nó cần.
# Lệnh này sẽ tạo thư mục ~/.fhir/packages trong container
# Sử dụng 'root' user home directory '/root'
RUN echo "{}" > /tmp/dummy.json && \
    java -jar /app/validator-data/validator_cli.jar /tmp/dummy.json -version 4.0.1 -tx n/a -install-from-tmp /tmp/fhir-core-pkg.zip && \
    rm /tmp/dummy.json /tmp/fhir-core-pkg.zip

# Sau khi lệnh trên chạy, các gói core sẽ được cache tại /root/.fhir/packages
# Không cần lệnh `cp -r /tmp/fhir-core-extracted/...` cũ nữa

# Sao chép phần backend và frontend của ứng dụng
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Thiết lập biến môi trường cho Java (tùy chọn, nếu cần PATH)
ENV JAVA_HOME /usr/local/openjdk-17
ENV PATH $PATH:$JAVA_HOME/bin

# Đặt biến môi trường cho FLASK_APP
ENV FLASK_APP=backend/app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Expose cổng mà Flask sẽ chạy
EXPOSE 5000

# Lệnh để chạy ứng dụng Flask khi container khởi động
CMD ["flask", "run"]