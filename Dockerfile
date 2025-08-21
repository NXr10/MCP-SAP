# Dockerfile para servidor MCP SAP Business One
# =============================================

# Usar imagen base de Python 3.11 slim para menor tamaño
FROM python:3.11-slim

# Metadatos del contenedor
LABEL maintainer="mcp-sap-server"
LABEL description="Servidor MCP para SAP Business One API"

# Configurar variables de entorno para Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Crear directorio de trabajo
WORKDIR /app

# Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copiar archivo de dependencias primero (para cache de Docker)
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Cambiar propietario de archivos al usuario no-root
RUN chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Exponer puerto HTTP
EXPOSE 8000

# Comando para ejecutar el servidor HTTP
CMD ["python", "server_http.py"]
