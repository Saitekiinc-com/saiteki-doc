-- MySQL 初期化スクリプト (c-db-02)
-- DVWA用データベース

CREATE DATABASE IF NOT EXISTS dvwa;
USE dvwa;

CREATE TABLE IF NOT EXISTS users (
    user_id int(6) NOT NULL auto_increment,
    first_name varchar(15) NOT NULL,
    last_name varchar(15) NOT NULL,
    user varchar(15) NOT NULL,
    password varchar(32) NOT NULL,
    avatar varchar(70),
    last_login TIMESTAMP,
    failed_login int(3),
    PRIMARY KEY (user_id)
);

-- DVWA デフォルトユーザー (MD5パスワード)
INSERT INTO users VALUES
('1','admin','admin','admin',MD5('password'),'/hackable/users/admin.jpg',NOW(),'0'),
('2','Gordon','Brown','gordonb',MD5('abc123'),'/hackable/users/gordonb.jpg',NOW(),'0'),
('3','Hack','Me','1337',MD5('charley'),'/hackable/users/1337.jpg',NOW(),'0'),
('4','Pablo','Picasso','pablo',MD5('letmein'),'/hackable/users/pablo.jpg',NOW(),'0'),
('5','Bob','Smith','smithy',MD5('password'),'/hackable/users/smithy.jpg',NOW(),'0');
