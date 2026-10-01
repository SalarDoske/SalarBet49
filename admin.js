document.addEventListener('DOMContentLoaded', () => {
    loadAdminMatches();

    document.getElementById('addMatchForm').addEventListener('submit', function(e) {
        e.preventDefault();

        const matchData = {
            home_team: document.getElementById('homeTeam').value,
            away_team: document.getElementById('awayTeam').value,
            match_time: document.getElementById('matchTime').value,
            home_odds: parseFloat(document.getElementById('homeOdds').value),
            draw_odds: parseFloat(document.getElementById('drawOdds').value),
            away_odds: parseFloat(document.getElementById('awayOdds').value)
        };

        // ئادرێسێ ڕاستەوخۆ بۆ سێرڤەرێ پایتۆن ل سەر پۆرتێ 5001
        fetch('http://10.101.133.101:5001/backend/add_match.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(matchData)
        })
        .then(res => res.json())
        .then(data => {
            alert(data.message);
            if (data.status === 'success') {
                document.getElementById('addMatchForm').reset();
                loadAdminMatches();
            }
        })
        .catch(err => {
            console.error('ئاریشە هەبوو:', err);
            alert('ئاریشەک د گەهشتنا سەرڤەری دا چێبوو!');
        });
    });
});

function loadAdminMatches() {
    // ئینانا لیستەیا یاریان ژ سێرڤەرێ پایتۆن
    fetch('http://10.101.133.101:5001/get_matches.php')
    .then(res => res.json())
    .then(matches => {
        const tableBody = document.getElementById('adminMatchesTable');
        if (!tableBody) return;
        tableBody.innerHTML = '';

        if(!matches || matches.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5">چ یاری نەهاتینە تۆمارکرن!</td></tr>';
            return;
        }

        matches.forEach((m, index) => {
            tableBody.innerHTML += `
                <tr>
                    <td>${index + 1}</td>
                    <td><b>${m.home_team}</b> 🆚 <b>${m.away_team}</b></td>
   1                <td>${m.match_time}</td>
                    <td>${m.home_odds} | ${m.draw_odds} | ${m.away_odds}</td>
                    <td>${m.status || 'upcoming'}</td>
                </tr>
            `;
        });
    })
    .catch(err => {
        console.error('ئاریشە د ئینانا لیستێ دا:', err);
    });
}