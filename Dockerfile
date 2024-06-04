# Use the official Python image
FROM python:3.9.18

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory into the container
COPY . /app

# Install pip
RUN apt-get update && \
    apt-get install -y python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install packages from requirements.txt
RUN pip install -r requirements.txt