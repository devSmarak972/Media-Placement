FROM python:3.12-slim

# Install dependencies including Chromium and Chromium driver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget curl unzip fonts-liberation \
    libnss3 libxss1 libasound2 libx11-xcb1 libxcomposite1 \
    libxdamage1 libatk-bridge2.0-0 libatk1.0-0 \
    libgtk-3-0 libgbm1 libxrandr2 libxfixes3 libglib2.0-0 \
    ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set Chromium binary path environment variable
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH="${PATH}:/usr/lib/chromium"

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Run your app
CMD ["python", "run.py"]
