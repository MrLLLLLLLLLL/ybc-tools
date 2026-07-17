FROM python:3.12-slim

# Install Chromium + ChromeDriver from Debian repos (reliable for containers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    fonts-liberation \
    fonts-noto-cjk \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Tell Selenium where to find Chrome and ChromeDriver
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/uploads data/outputs data/screenshots chromedriver

EXPOSE 5001

CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
