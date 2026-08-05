FROM python:3.11-slim

WORKDIR /app

COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "import nltk; nltk.download('punkt_tab'); nltk.download('punkt')"

COPY services/api/ ./services/api/
COPY services/ai/ ./services/ai/
COPY services/__init__.py ./services/__init__.py
COPY shared/ ./shared/

WORKDIR /app/services/api

EXPOSE 8001

CMD ["python", "main.py"]
