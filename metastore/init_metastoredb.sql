CREATE USER hive WITH PASSWORD 'hive';
CREATE DATABASE metadata;
GRANT ALL PRIVILEGES ON DATABASE metadata TO hive;
