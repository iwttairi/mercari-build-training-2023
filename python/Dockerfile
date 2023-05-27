FROM python:3.10.11-alpine

RUN addgroup -S mercari && adduser -S trainee -G mercari

WORKDIR /app
COPY . .

WORKDIR /app/python
RUN pip install --upgrade pip && pip install -r requirements.txt --verbose

RUN chown -R trainee:mercari /app/db
RUN chown -R trainee:mercari /app/python/images

USER trainee

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]