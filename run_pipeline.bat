@echo off
echo =======================================================
echo  Starting Distributed Stock Market Analytics Pipeline
echo =======================================================
echo.

echo [1/7] Ensuring Docker containers (Kafka, Zookeeper, TimescaleDB) are running...
docker compose up -d

echo.
echo Waiting 10 seconds for Kafka to warm up...
timeout /t 10 /nobreak >nul

echo [2/7] Starting API Backend...
start "StockPulse API Backend" cmd /k ".\.venv\Scripts\python.exe backend/api.py"

echo [3/7] Starting React Frontend...
cd frontend
start "StockPulse Frontend" cmd /k "npm install && npm run dev"
cd ..

echo [4/7] Starting Ingestion Service (yfinance)...
start "Ingestion Service" cmd /k ".\.venv\Scripts\python.exe -m ingestion.main"

echo [5/7] Starting Streaming Processor (PySpark)...
start "Spark Processor" cmd /k "spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.5.4 processing/spark_job.py"

echo [6/7] Starting Anomaly Detector...
start "Anomaly Detector" cmd /k ".\.venv\Scripts\python.exe -m Anomaly_Detection.Detector"

echo [7/7] Starting Alerts Consumer...
start "Alerts Consumer" cmd /k ".\.venv\Scripts\python.exe -m alerts.alert_consumer"

echo.
echo =======================================================
echo All services have been launched in separate windows!
echo Your dashboard will be available at http://localhost:5173 
echo =======================================================
pause
