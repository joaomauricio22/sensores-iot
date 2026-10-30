# Imagem base com Python
FROM python:3.11-slim

# Diretório de trabalho dentro do container
WORKDIR /app

# Copia as dependências e as instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Porta em que a API escuta
EXPOSE 8080

# Comando de inicialização da API
CMD ["python", "app.py"]
