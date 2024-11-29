FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY ./src /app/src

# Expose the desired port
EXPOSE 80

# Command to run your application
CMD ["gunicorn", "--bind","0.0.0.0:80","src.app:app"]
