FROM python:3.12-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget curl unzip fonts-liberation \
    libnss3 libxss1 libasound2 libx11-xcb1 libxcomposite1 \
    libxdamage1 libatk-bridge2.0-0 libatk1.0-0 \
    libgtk-3-0 libgbm1 libxrandr2 libxfixes3 libglib2.0-0 \
    ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Chrome
# RUN wget -O chrome-linux64.zip https://storage.googleapis.com/chrome-for-testing-public/136.0.7103.92/linux64/chrome-linux64.zip && \
#     unzip chrome-linux64.zip && \
#     mv chrome-linux64 /opt/chrome && \
#     ln -s /opt/chrome/chrome /usr/bin/google-chrome && \
#     rm chrome-linux64.zip

# Install Chromedriver
# RUN wget -O chromedriver-linux64.zip https://storage.googleapis.com/chrome-for-testing-public/136.0.7103.92/linux64/chromedriver-linux64.zip && \
#     unzip chromedriver-linux64.zip && \
#     mv chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
#     chmod +x /usr/bin/chromedriver && \
#     rm -rf chromedriver-linux64.zip chromedriver-linux64

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

# Copy the rest of your code
COPY . .

# Set environment variables to help Chrome run headlessly
# ENV CHROME_BIN=/usr/bin/google-chrome
# ENV PATH="${PATH}:/usr/bin"

# Run your app
CMD ["python", "run.py"]
