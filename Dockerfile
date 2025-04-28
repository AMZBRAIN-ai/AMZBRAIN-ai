# 1) Use the Playwright Python image (includes browsers + deps)
FROM mcr.microsoft.com/playwright/python:v1.51.0-jammy

# 2) Create & switch to working dir
WORKDIR /app

# 3) Copy & install Python requirements
COPY requirements.txt .
COPY google_credentials.json .

RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

# 4) Copy your source code
#    (assuming main.py lives at the repo root alongside Dockerfile)
COPY . .

# 5) Expose whatever port you use (3000 in your uvicorn command)
EXPOSE 3000

# 6) Start your FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
