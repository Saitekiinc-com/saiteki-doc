# p-web-01: 公開Webサーバー1
# Apache + PHP + DVWA (Damn Vulnerable Web Application)
# 教育目的: SQLインジェクション、XSS、コマンドインジェクション等の学習用

FROM php:8.1-apache

# 必要パッケージのインストール
RUN apt-get update && apt-get install -y \
    git \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libpq-dev \
    default-mysql-client \
    curl \
    netcat-openbsd \
    iputils-ping \
    net-tools \
    nmap \
    && docker-php-ext-install pdo pdo_mysql mysqli gd \
    && rm -rf /var/lib/apt/lists/*

# Apache mod_rewrite 有効化
RUN a2enmod rewrite headers

# DVWA のインストール
RUN git clone https://github.com/digininja/DVWA.git /var/www/html/dvwa

# DVWA 設定ファイル
COPY config.inc.php /var/www/html/dvwa/config/config.inc.php

# 脆弱なPHPアプリ (追加の学習用ページ)
COPY vulnerable-app/ /var/www/html/app/

# Apache 設定
COPY apache.conf /etc/apache2/sites-available/000-default.conf

# ファイル権限
RUN chown -R www-data:www-data /var/www/html/ \
    && chmod -R 755 /var/www/html/

EXPOSE 80

CMD ["apache2-foreground"]
