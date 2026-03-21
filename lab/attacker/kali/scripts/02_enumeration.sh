#!/bin/bash
# ============================================================
# 演習2: 列挙 (Enumeration)
# 目的: Webサーバー、FTPサーバーの詳細を調査する
# ============================================================

WEB_01="172.16.10.10"
WEB_02="172.16.10.11"
FTP_01="172.16.10.21"

echo "=== Webサーバー列挙 (p-web-01: $WEB_01) ==="

echo "[*] Nikto でWebスキャン..."
nikto -h "http://$WEB_01" -output /tmp/nikto_web01.txt 2>/dev/null &

echo "[*] Gobuster でディレクトリ探索..."
gobuster dir \
    -u "http://$WEB_01" \
    -w /usr/share/wordlists/dirb/common.txt \
    -o /tmp/gobuster_web01.txt \
    2>/dev/null

echo ""
echo "=== Webサーバー2 (p-web-02: $WEB_02) ディレクトリリスト ==="
echo "[*] ディレクトリリスティングを確認..."
curl -s "http://$WEB_02/" | grep -i "href"
curl -s "http://$WEB_02/backup/" 2>/dev/null
curl -s "http://$WEB_02/config/" 2>/dev/null

echo ""
echo "=== FTPサーバー列挙 ($FTP_01) ==="
echo "[*] 匿名FTPアクセスを試みる..."
ftp -n "$FTP_01" << 'EOF'
user anonymous anonymous@test.com
ls -la
get README.txt /tmp/ftp_readme.txt
bye
EOF
cat /tmp/ftp_readme.txt 2>/dev/null

echo ""
echo "=== 列挙完了 ==="
echo "次のステップ: 03_exploitation.sh で脆弱性を悪用"
