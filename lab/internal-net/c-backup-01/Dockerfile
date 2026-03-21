# c-backup-01: バックアップサーバー
# rsync + Samba (弱い設定)

FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    rsync \
    samba \
    openssh-server \
    curl \
    net-tools \
    iputils-ping \
    cron \
    && rm -rf /var/lib/apt/lists/*

# SSH設定
RUN mkdir -p /var/run/sshd
RUN echo 'root:backup_root_pass' | chpasswd
COPY sshd_config /etc/ssh/sshd_config

# Samba設定
COPY smb.conf /etc/samba/smb.conf
RUN useradd -m backupuser && echo "backupuser:backup123" | chpasswd
RUN echo -e "backup123\nbackup123" | smbpasswd -a backupuser -s

# バックアップディレクトリ
RUN mkdir -p /backup/{databases,configs,logs}
COPY sample-backups/ /backup/

# SSH ホストキーの生成
RUN ssh-keygen -A

EXPOSE 22 445 139

CMD sh -c "service smbd start && /usr/sbin/sshd -D"
