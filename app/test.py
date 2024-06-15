import psycopg2

try:
    conn = psycopg2.connect(
        dbname='postgres',  # Имя вашей базы данных
        user='postgres',      # Имя пользователя базы данных
        password='postgres',  # Пароль пользователя базы данных
        host='localhost',     # Адрес сервера базы данных (обычно 'localhost')
        port='5432'           # Порт сервера базы данных (по умолчанию 5432)
    )
    print("Connection successful")
except psycopg2.OperationalError as e:
    print(f"Connection failed: {e}")