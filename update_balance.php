<?php
require_once 'db.php';
header('Content-Type: application/json');

// نموونە: ل ڤێرە مە ID-یێ بکارهێنەری کریە 1 (یان دشێی سیستەمێ Session بکاربینی)
$user_id = 1; 

$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET') {
    // بۆ خوێندنا بالانسێ
    $stmt = $pdo->prepare("SELECT balance FROM users WHERE id = ?");
    $stmt->execute([$user_id]);
    $user = $stmt->fetch();
    
    if ($user) {
        echo json_encode(['success' => true, 'balance' => floatval($user['balance'])]);
    } else {
        echo json_encode(['success' => false, 'message' => 'User not found']);
    }
} 
elseif ($method === 'POST') {
    // بۆ گوهۆڕینا بالانسێ (دەمێ دبرد یان ددۆڕێنێت)
    $data = json_decode(file_get_contents('php://input'), true);
    $new_balance = $data['balance'] ?? null;

    if ($new_balance !== null && is_numeric($new_balance)) {
        $stmt = $pdo->prepare("UPDATE users SET balance = ? WHERE id = ?");
        if ($stmt->execute([$new_balance, $user_id])) {
            echo json_encode(['success' => true, 'balance' => floatval($new_balance)]);
        } else {
            echo json_encode(['success' => false, 'message' => 'Failed to update']);
        }
    } else {
        echo json_encode(['success' => false, 'message' => 'Invalid data']);
    }
}
?>
