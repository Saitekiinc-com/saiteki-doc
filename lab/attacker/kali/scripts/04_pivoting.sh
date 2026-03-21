#!/bin/bash
# ============================================================
# 演習4: ピボット攻撃 (Pivoting)
# 目的: ジャンプボックスを踏み台にして内部NWへアクセス
# ============================================================

JUMPBOX="172.16.10.100"
INTERNAL_DB="10.1.0.20"
INTERNAL_RAILS="10.1.0.10"

echo "=== 演習4: ピボット攻撃 ==="
echo ""
echo "シナリオ:"
echo "  攻撃者: 172.16.10.200 (Kali)"
echo "  踏み台: $JUMPBOX (ジャンプボックス)"
echo "  目標:   $INTERNAL_DB (内部DB) / $INTERNAL_RAILS (内部Rails)"
echo ""

echo "[*] ジャンプボックスへSSH接続してポートフォワード設定..."
echo "実行コマンド例:"
echo ""
echo "  # SSHダイナミックポートフォワーディング (SOCKSプロキシ)"
echo "  ssh -D 1080 -N admin@$JUMPBOX -p 2222"
echo ""
echo "  # 内部DBへのローカルポートフォワード"
echo "  ssh -L 5432:$INTERNAL_DB:5432 admin@$JUMPBOX -p 2222"
echo ""
echo "  # proxychains で内部NWのスキャン"
echo "  proxychains nmap -sT -Pn $INTERNAL_DB"
echo ""

# 実際に接続してみる
echo "[*] ジャンプボックスを経由して内部DBに接続..."
sshpass -p 'admin123' ssh -o StrictHostKeyChecking=no \
    -o ConnectTimeout=5 \
    admin@"$JUMPBOX" -p 2222 \
    "ping -c 2 $INTERNAL_DB 2>/dev/null && echo '[+] 内部DBへの到達を確認'" 2>/dev/null

echo ""
echo "=== ピボット演習完了 ==="
