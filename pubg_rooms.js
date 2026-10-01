document.addEventListener("DOMContentLoaded", function () {
    loadPubgRooms();
});

function loadPubgRooms() {
    fetch('/api/pubg/rooms')
        .then(response => response.json())
        .then(rooms => {
            const container = document.getElementById("pubg-rooms-container");
            if (!container) return;
            
            container.innerHTML = "";
            if (rooms.length === 0) {
                container.innerHTML = "<p class='text-center text-gray-400'>چ ڕۆمێن پۆبچی یێن ڤەکری نینن نوکە!</p>";
                return;
            }

            rooms.forEach(room => {
                let card = `
                    <div class="bg-gray-800 p-4 rounded-lg shadow-md mb-4 border border-gray-700">
                        <h3 class="text-xl font-bold text-yellow-400 mb-2">${room.room_name}</h3>
                        <p class="text-gray-300">تێچوونا پشکداریێ: <span class="text-white font-semibold">${room.entry_fee} IQD</span></p>
                        <p class="text-gray-300">خەلات: <span class="text-green-400 font-semibold">${room.prize_pool} IQD</span></p>
                        <p class="text-gray-300 mb-4">یاریزانێن تۆمارکری: <span class="text-blue-400 font-semibold">${room.registered_count} / ${room.max_players}</span></p>
                        
                        <button onclick="openJoinModal(${room.id})" class="bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-bold px-4 py-2 rounded transition w-full">
                            پشکداری کرن (Join Room)
                        </button>
                    </div>
                `;
                container.innerHTML += card;
            });
        })
        .catch(err => console.error("Error loading PUBG rooms:", err));
}

function openJoinModal(roomId) {
    let playerName = prompt("ناڤێ خوە یێ یاریێ (Player Name) بنڤیسە:");
    if (!playerName) return;

    let pubgId = prompt("پۆبچی ئایدی خوە (PUBG ID) بنڤیسە:");
    if (!pubgId) return;

    joinPubgRoom(roomId, playerName, pubgId);
}

function joinPubgRoom(roomId, playerName, pubgId) {
    fetch('/api/pubg/join', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            room_id: roomId,
            player_name: playerName,
            pubg_id: pubgId
        })
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || "چەوتییەک هەی!");
        }
        return data;
    })
    .then(data => {
        if (data.status === 'success') {
            alert(data.message + "\nRoom ID: " + data.room_credentials.room_id + "\nPassword: " + data.room_credentials.room_pass);
            location.reload();
        } else {
            alert("خەلەت: " + data.message);
        }
    })
    .catch(err => {
        console.error("Error:", err);
        alert("ئاگه‌هداری: " + err.message);
    });
}
