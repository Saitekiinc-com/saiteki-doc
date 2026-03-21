<?php
// 教育目的: XSS (Cross-Site Scripting) 脆弱性のデモ
$comment = $_GET['comment'] ?? '';
// 脆弱: エスケープなしで出力している
// 攻撃例: "<script>alert('XSS')</script>"
echo "<h2>投稿されたコメント:</h2>";
echo "<p>" . $comment . "</p>";  // XSS脆弱性
echo "<p><a href='/'>戻る</a></p>";
?>
