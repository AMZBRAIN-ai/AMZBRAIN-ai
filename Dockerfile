FROM mcr.microsoft.com/playwright/python:v1.51.0-jammy

WORKDIR /app

# install your Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# tell Playwright to dump browsers into /ms-playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
# install Chromium once, at build time
RUN playwright install chromium

# copy your app
COPY . .

EXPOSE 3000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
