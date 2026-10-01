<?php
$host = 'localhost';
$dbname = 'database.db'; // ناڤێ داتابەیسا خۆ لێرە بنڤیسە
$username = 'root';
$password = '';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("شکست لە پەیوەندیکردن ب داتابەیسێ: " . $e->getMessage());
}
?>
