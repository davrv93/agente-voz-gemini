# Solo la biblioteca estándar de Python: no hay dependencias que instalar.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY app/ app/
COPY pasos/ pasos/
COPY ejemplos/ ejemplos/
RUN useradd --uid 10001 --no-create-home agente && mkdir -p salida && chown agente salida
USER agente
EXPOSE 8090
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8090/api/estado',timeout=2)"
CMD ["python", "app/servidor.py"]
