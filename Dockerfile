# Use an official Python runtime as a parent image
# python:3.9-slim is a good balance of size and compatibility
# Adjust version as needed (e.g., python:3.11-slim if you prefer 3.11)
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
# This step is done early to leverage Docker's build cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces image size by not storing build artifacts
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire current directory contents into the container at /app
# This includes your .py files and shop_location.json
COPY . .

# Expose the port that Streamlit runs on (default is 8501)
EXPOSE 8501

# Define the command to run your Streamlit application
# Replace 'channel_partners_main.py' with your primary Streamlit file
CMD ["streamlit", "run", "channel_partners_main.py", "--server.port=8501", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
