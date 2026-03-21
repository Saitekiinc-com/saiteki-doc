<?php
# DVWA 設定ファイル
# 警告: これは意図的に脆弱な設定です。教育目的のみ。

$_DVWA = array();

# データベース設定
$_DVWA[ 'db_server' ]   = getenv('MYSQL_HOST') ?: '10.1.0.21';
$_DVWA[ 'db_database' ] = getenv('MYSQL_DB')   ?: 'dvwa';
$_DVWA[ 'db_user' ]     = getenv('MYSQL_USER') ?: 'dvwa';
$_DVWA[ 'db_password' ] = getenv('MYSQL_PASSWORD') ?: 'password';
$_DVWA[ 'db_port']      = '3306';

# reCAPTCHA (無効化)
$_DVWA[ 'recaptcha_public_key' ]  = '';
$_DVWA[ 'recaptcha_private_key' ] = '';

# デフォルトセキュリティレベル: low (最も脆弱)
$_DVWA[ 'default_security_level' ] = 'low';

# PHPIDS (無効化)
$_DVWA[ 'disable_authentication' ] = false;
$_DVWA[ 'allowed_upload_types' ]  = array( 'jpeg', 'jpg', 'png', 'gif', 'php' );

?>
