FROM mcr.microsoft.com/playwright/python:v1.51.0-jammy

WORKDIR /app

# 1) Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Tell both build and runtime to use /ms-playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV XDG_CACHE_HOME=/ms-playwright

# 3) Install Chromium into /ms-playwright
RUN playwright install chromium

# 4) Your code
COPY . .

EXPOSE 3000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
