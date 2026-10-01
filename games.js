// 1. گۆڕراوا سەرەکی یا بالانسی
var balance = 0; 

// 2. تابعەک بۆ ئینانا بالانسی ژ سەرڤێری دەمێ پەڕە بار دکەت
function fetchBalance() {
    fetch('/api/balance') // ئەڤە ڕێکا API-یا سەرڤێری تە یە
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                balance = data.balance;
                updateHUD(); // بۆ نووژەنکرنا نیشاندانا بالانسی ل سەر شاشێ
            }
        })
        .catch(err => console.error('Error fetching balance:', err));
}

// 3. تابعەک بۆ هنارتنا بالانسێ نوو بۆ سەرڤێری (دەمێ دبرد یان ددۆڕێنێت)
function syncBalance() {
    fetch('/api/balance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ balance: balance })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Failed to sync balance with server');
        }
    })
    .catch(err => console.error('Error syncing:', err));
}

// 4. ل دەستپێکا بارکرنا یاریێ (د پشکا Init دا)، ڤی فۆنکشنی بانگ بکە:
document.addEventListener("DOMContentLoaded", function() {
    fetchBalance();
    // کۆدێن تر یێن دەستپێکا یاریێ ل ڤێرە هەنە...
});
