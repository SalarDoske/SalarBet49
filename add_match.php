<?php
header('Content-Type: application/json');
include '../db.php'; // وەرگرتنا داتابێسێ ژ فۆڵدەرێ سەرەکی

$jsonInput = file_get_contents('php://input');
$data = json_decode($jsonInput, true);

if (!empty($data['home_team']) && !empty($data['away_team'])) {
    
    $home = $data['home_team'];
    $away = $data['away_team'];
    $time = $data['match_time'];
    $h_odds = $data['home_odds'];
    $d_odds = $data['draw_odds'];
    $a_odds = $data['away_odds'];

    // دروستکرنا پرسیارێ ب شێوێ پاراستی (Prepared Statement)
    $stmt = $conn->prepare("INSERT INTO matches (home_team, away_team, match_time, home_odds, draw_odds, away_odds, status) VALUES (?, ?, ?, ?, ?, ?, 'upcoming')");
    $stmt->bind_param("sssddd", $home, $away, $time, $h_odds, $d_odds, $a_odds);
    
    if ($stmt->execute()) {
        echo json_encode(["status" => "success", "message" => "یاریا $home 🆚 $away ب سەرکەفتن هاتە زێدەکرن!"]);
    } else {
        echo json_encode(["status" => "error", "message" => "ئاریشەک د تۆمارکرنا داتابێسێ دا چێبوو!"]);
    }
    $stmt->close();
} else {
    echo json_encode(["status" => "error", "message" => "تکایە هەمی خانەیان تژیکە!"]);
}

$conn->close();
?>
