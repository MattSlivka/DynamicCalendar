# ---- Importing Neccesary Images ---
FROM python:3.12-slim

# ---- Set working directory
WORKDIR /app

# ---- Copying the requirements.txt file to the desired directory ----
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# ---- Setting the user
RUN adduser --disabled-password --no-create-home notifier
USER notifier

# ---- Setting Default Port ----
EXPOSE 5001

# ---- Starting the App ----
CMD ["python", "app.py"]
