# Use the AWS Lambda Python runtime as a base image
FROM python:3-slim-buster

RUN mkdir /app

WORKDIR /app

# Copy function code and requirements file
COPY . .

# Install the function's dependencies using requirements.txt
RUN pip install -r requirements.txt


# Expose the port on which the application will run
EXPOSE 8011

# Run the FastAPI application using uvicorn server
CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=8011"]