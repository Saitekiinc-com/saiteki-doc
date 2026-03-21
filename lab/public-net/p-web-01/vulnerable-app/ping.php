<?php
// 教育目的: コマンドインジェクション脆弱性のデモ
// 本番環境では絶対に使用しないこと
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['host'])) {
    $host = $_POST['host'];
    // 脆弱: ユーザー入力をそのままshellに渡している
    // 攻撃例: "8.8.8.8; cat /etc/passwd"
    $output = shell_exec("ping -c 3 " . $host);
    echo "<pre>" . htmlspecialchars($output) . "</pre>";
}
?>
<a href="/">戻る</a>
