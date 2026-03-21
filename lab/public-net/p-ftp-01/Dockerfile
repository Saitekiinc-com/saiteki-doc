# p-ftp-01: FTPサーバー
# 匿名ログイン有効、弱いパスワード設定

FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    vsftpd \
    ftp \
    curl \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# vsftpd 設定
COPY vsftpd.conf /etc/vsftpd.conf

# 匿名FTPの公開ディレクトリ
RUN mkdir -p /var/ftp/pub
COPY pub/ /var/ftp/pub/

# FTPユーザー作成 (弱いパスワード)
RUN useradd -m ftpuser && echo "ftpuser:ftpuser" | chpasswd
RUN useradd -m backup && echo "backup:backup123" | chpasswd

# パッシブモード用ディレクトリ
RUN mkdir -p /var/ftp/pub && chown ftp:ftp /var/ftp/pub

EXPOSE 21 21100-21110

CMD ["/usr/sbin/vsftpd", "/etc/vsftpd.conf"]
