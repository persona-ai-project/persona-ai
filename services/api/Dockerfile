FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK data needed by P1's chunker
RUN python -c "import nltk; nltk.download('punkt_tab'); nltk.download('punkt')"

COPY . .

EXPOSE 8001

CMD ["python", "main.py"]
