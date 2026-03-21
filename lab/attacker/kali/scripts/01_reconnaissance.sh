#!/bin/bash
# ============================================================
# 演習1: 偵察 (Reconnaissance)
# 目的: 公開ネットワーク上のターゲットを発見する
# ============================================================

TARGET_NETWORK="172.16.10.0/24"

echo "=== ステップ1: ネットワークスキャン ==="
echo "対象: $TARGET_NETWORK"
echo ""

# ホスト発見
echo "[*] Pingスキャンでホストを発見..."
nmap -sn "$TARGET_NETWORK" -oN /tmp/hosts_discovery.txt
cat /tmp/hosts_discovery.txt

echo ""
echo "=== ステップ2: ポートスキャン ==="
echo "[*] 発見したホストの詳細スキャン..."

# 各ホストの詳細スキャン
for host in 172.16.10.10 172.16.10.11 172.16.10.21 172.16.10.100; do
    echo ""
    echo "[*] スキャン中: $host"
    nmap -sV -sC --open "$host" 2>/dev/null | head -40
done

echo ""
echo "=== 偵察完了 ==="
echo "次のステップ: 02_enumeration.sh でサービスの詳細を調査"
