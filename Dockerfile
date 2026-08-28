FROM python:3.11-slim

WORKDIR /app

ENV SUPABASE_URL=https://afjfieukktcjxgvtawjy.supabase.co
ENV SUPABASE_SERVICE_KEY_B64=c2Jfc2VjcmV0XzNrMDJiTWVBbFFxd0RQRnJILW8xRWdfNFRjUTRESWU=

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/app/ ./backend/app/
COPY backend/research_manager.db ./backend/research_manager.db
COPY backend/uploads/ ./backend/uploads/
COPY frontend/dist/ ./frontend/dist/

WORKDIR /app/backend

CMD gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}
