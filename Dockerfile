ARG PYTHON_IMAGE=python:3.14-slim
FROM ${PYTHON_IMAGE}
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/app.py .
EXPOSE 8000
USER 1001
CMD ["python", "app.py"]
