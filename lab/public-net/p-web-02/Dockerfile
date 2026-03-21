# p-web-02: 公開Webサーバー2
# Nginx + PHP-FPM (ディレクトリリスティング有効、弱い認証)

FROM nginx:alpine

RUN apk add --no-cache \
    php83 \
    php83-fpm \
    php83-mysqli \
    php83-curl \
    curl \
    iputils \
    net-tools \
    bash

# Nginx 設定 (ディレクトリリスティング有効)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 公開ファイル
COPY html/ /var/www/html/

# PHP-FPM 設定
RUN mkdir -p /run/php/

EXPOSE 80

CMD sh -c "php-fpm83 && nginx -g 'daemon off;'"
