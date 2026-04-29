FROM registry.access.redhat.com/ubi9/python-311:1

WORKDIR /opt/app-root/src

COPY pyproject.toml .
COPY app/ app/
RUN pip install --no-cache-dir .

EXPOSE 9999 8000

CMD ["python", "-m", "app.main"]
