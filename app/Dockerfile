FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
COPY app.py ./
COPY ui.py ./
COPY locales/ ./locales/
COPY static/ ./static/
CMD ["python", "app.py"]
