# ---- Importing Neccesary Images ---
FROM python:3.12-slim

# ---- Set working directory
WORKDIR /app

# ---- Copying the requirements.txt file and anytyhing else to the desired directory ----
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Setting the user
RUN adduser --disabled-password --no-create-home scheduler
USER scheduler

# ---- Starting the App ----
CMD ["python", "scheduler.py"]