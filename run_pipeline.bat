@echo off
set PYTHONPATH=.
set HADOOP_HOME=C:\hadoop
set PATH=%HADOOP_HOME%\bin;%PATH%

echo [1/8] Initializing Infrastructure (Kafka + DB)...
set PYTHONPATH=.
.\.venv\Scripts\python.exe infrastructure/init_all.py

echo [2/8] Starting Database Persistence Sink (Kafka to Timescale)...
start "DB Persistence Sink" cmd /k "set PYTHONPATH=. && .\.venv\Scripts\python.exe processing/kafka_to_db.py"

echo [3/8] Starting API Backend...
start "StockPulse API Backend" cmd /k "set PYTHONPATH=. && .\.venv\Scripts\python.exe backend/api.py"

echo [4/8] Starting React Frontend...
cd frontend
start "StockPulse Frontend" cmd /k "npm run dev"
cd ..

echo [5/8] Starting Ingestion Service (yfinance)...
start "Ingestion Service" cmd /k "set PYTHONPATH=. && .\.venv\Scripts\python.exe -m ingestion.main"

echo [6/8] Starting Anomaly Detector...
start "Anomaly Detector" cmd /k "set PYTHONPATH=. && .\.venv\Scripts\python.exe -m Anomaly_Detection.Detector"

echo [7/8] Starting Alerts Consumer...
start "Alerts Consumer" cmd /k "set PYTHONPATH=. && .\.venv\Scripts\python.exe -m alerts.alert_consumer"

echo [8/8] Starting Market Processor (Real-time Analytics)...
start "Market Processor" cmd /k "set PYTHONPATH=. && .\.venv\Scripts\python.exe processing/processor.py"

echo.
echo =======================================================
echo All services have been launched in separate windows!
echo Your dashboard will be available at http://localhost:5173 
echo =======================================================
pause
