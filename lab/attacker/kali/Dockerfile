# Kali Linux 攻撃者マシン
# 主要なペネトレーションテストツールを含む

FROM kalilinux/kali-rolling

# 主要ツールのインストール
RUN apt-get update && apt-get install -y \
    # ネットワークスキャン
    nmap \
    masscan \
    netcat-openbsd \
    # Webアプリテスト
    nikto \
    gobuster \
    sqlmap \
    curl \
    wget \
    # パスワードクラック
    hydra \
    john \
    hashcat \
    # エクスプロイト
    metasploit-framework \
    # プロキシ・傍受
    burpsuite \
    # ネットワーク解析
    wireshark-common \
    tcpdump \
    # SSH・リモートアクセス
    openssh-client \
    sshpass \
    # その他ユーティリティ
    python3 \
    python3-pip \
    git \
    vim \
    tmux \
    net-tools \
    iputils-ping \
    dnsutils \
    ftp \
    && rm -rf /var/lib/apt/lists/*

# Python ツール
RUN pip3 install \
    requests \
    impacket \
    pwntools \
    scapy

# 学習用スクリプトのコピー
COPY scripts/ /opt/lab-scripts/
RUN chmod +x /opt/lab-scripts/*.sh 2>/dev/null || true

WORKDIR /root

CMD ["/bin/bash"]
