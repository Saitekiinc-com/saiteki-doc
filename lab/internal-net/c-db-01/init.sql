-- PostgreSQL 初期化スクリプト (c-db-01)
-- 教育目的: 適切でない権限設定のデモ

CREATE DATABASE rails_app;
\c rails_app

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(200),
    password_hash VARCHAR(200),  -- MD5ハッシュ (弱い)
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 初期データ (弱いパスワードのデモ)
INSERT INTO users (username, email, password_hash, role) VALUES
    ('admin', 'admin@acme-corp.local', md5('admin123'), 'admin'),
    ('john.doe', 'john@acme-corp.local', md5('Password1'), 'user'),
    ('sysadmin', 'sysadmin@acme-corp.local', md5('Qwerty123'), 'admin');

-- 機密テーブル
CREATE TABLE secrets (
    id SERIAL PRIMARY KEY,
    key VARCHAR(200) NOT NULL,
    value TEXT NOT NULL
);

INSERT INTO secrets (key, value) VALUES
    ('api_key', 'sk-prod-xxxxxxxxxxxxxxxxxx'),
    ('aws_access_key', 'AKIAIOSFODNN7EXAMPLE'),
    ('aws_secret_key', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY');

-- 過剰な権限を持つユーザー (教育目的)
CREATE USER app_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE rails_app TO app_user;
