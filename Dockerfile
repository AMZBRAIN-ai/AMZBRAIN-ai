# 1) Start from Playwright’s official Python image
FROM mcr.microsoft.com/playwright/python:latest

# 2) Set working directory
WORKDIR /app

# 3) Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4) Copy your FastAPI app code
COPY . .

# 5) Install Playwright browsers
RUN playwright install --with-deps

# 6) Expose the app port
EXPOSE 3000

# 7) Start the FastAPI server
CMD uvicorn main:app --host 0.0.0.0 --port 3000

# # 1) Start from Playwright’s official Python image (includes system libs + browsers)
# FROM mcr.microsoft.com/playwright/python:latest

# # 2) Set working dir
# WORKDIR /app

# # 3) Copy & install Python deps
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # 4) Copy your FastAPI appsss
# COPY . .

# # 5) Expose the port your app uses
# EXPOSE 3000

# # 6) Default command: no more 'install-deps' needed — it's all in the image

# # CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
# CMD uvicorn main:app --host 0.0.0.0 --port 3000
