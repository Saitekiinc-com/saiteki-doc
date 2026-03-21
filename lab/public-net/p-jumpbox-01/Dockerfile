# p-jumpbox-01: ジャンプボックス / 踏み台サーバー
# 公開NWと社内NW両方に接続 - ピボット攻撃の学習用

FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    openssh-server \
    curl \
    wget \
    net-tools \
    iputils-ping \
    nmap \
    netcat-openbsd \
    python3 \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# SSH設定 (弱い設定)
RUN mkdir -p /var/run/sshd
COPY sshd_config /etc/ssh/sshd_config

# ユーザー作成 (弱いパスワード)
RUN useradd -m -s /bin/bash admin && echo "admin:admin123" | chpasswd
RUN useradd -m -s /bin/bash developer && echo "developer:dev123" | chpasswd
RUN echo "admin ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# SSH ホストキーの生成
RUN ssh-keygen -A

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
