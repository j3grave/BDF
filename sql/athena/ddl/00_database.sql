-- 00_database.sql
-- Base de dados no Glue Data Catalog onde ficam as tabelas do dataset (ex.: movielens_32m).
-- No Athena, uma "base de dados" é só um agrupamento de tabelas no catálogo: não guarda dados.
--
-- Parâmetros: ${database} (substituído pelo scripts/athena_setup.py)
CREATE DATABASE IF NOT EXISTS ${database}
