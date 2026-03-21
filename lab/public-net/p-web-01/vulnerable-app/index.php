<?php
// 教育目的の脆弱なPHPアプリ
// 学習できる脆弱性: SQLインジェクション、XSS、コマンドインジェクション
?>
<!DOCTYPE html>
<html>
<head><title>ACME Corp - ユーザー検索</title></head>
<body>
<h1>ACME Corp ユーザー検索システム</h1>

<!-- SQLインジェクション脆弱性 -->
<h2>ユーザー検索</h2>
<form method="GET">
    <input name="user" placeholder="ユーザー名を入力">
    <button type="submit">検索</button>
</form>
<?php
if (isset($_GET['user'])) {
    $conn = new mysqli("10.1.0.21", "dvwa", "password", "dvwa");
    // 脆弱: ユーザー入力をそのままSQLに埋め込んでいる
    $sql = "SELECT * FROM users WHERE user = '" . $_GET['user'] . "'";
    $result = $conn->query($sql);
    if ($result) {
        while ($row = $result->fetch_assoc()) {
            echo "<p>ユーザー: " . $row['user'] . "</p>";
        }
    }
}
?>

<!-- XSS脆弱性 -->
<h2>コメント</h2>
<form method="GET" action="comment.php">
    <input name="comment" placeholder="コメントを入力">
    <button type="submit">投稿</button>
</form>

<!-- コマンドインジェクション脆弱性 -->
<h2>Ping テスト</h2>
<form method="POST" action="ping.php">
    <input name="host" placeholder="IPアドレスまたはホスト名">
    <button type="submit">Ping実行</button>
</form>
</body>
</html>
