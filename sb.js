// ==========================================
// 1. DYNAMIC MATCHES FETCHING (داتابێسا یاریان)
// ==========================================

const API_BASE_URL = 'http://10.101.133.101:5001';

document.addEventListener('DOMContentLoaded', () => {
    loadLiveMatches();
    initExistingUI();
});

function loadLiveMatches() {
    fetch(`${API_BASE_URL}/get_matches.php`)
        .then(response => response.json())
        .then(matches => {
            const container = document.getElementById('dynamic-matches-container');
            if (!container) return;

            if (!matches || matches.length === 0) {
                container.innerHTML = '<p style="color: #fff; text-align: center; padding: 20px;">چ یاری د بەرهەڤ نینەن!</p>';
                return;
            }

            let htmlContent = '';
            matches.forEach(match => {
                htmlContent += `
                    <div class="event-block" style="margin-bottom: 12px; background: #1e1e1e; border-radius: 8px; padding: 12px;">
                        <div class="event-block-inner">
                            <div class="event-block-head" style="display: flex; justify-content: space-between; color: #38bdf8; padding-bottom: 8px;">
                                <span class="event-block-dt">دەم: ${match.match_time}</span>
                                <span style="font-size: 12px; color: #4ade80;">${match.status || 'upcoming'}</span>
                            </div>

                            <div class="event-block-content" style="display: flex; align-items: center; justify-content: space-between;">
                                <div class="event-block-ca" style="flex: 1; color: #fff;">
                                    <div class="eb-a" style="font-weight: bold; margin-bottom: 5px;">
                                        <span class="eb-a-name">⚽ ${match.home_team}</span>
                                    </div> 
                                    <div class="eb-b" style="font-weight: bold;">
                                        <span class="eb-b-name">⚽ ${match.away_team}</span>
                                    </div> 
                                </div>

                                <!-- دوگمەیێن دانا پارەی (Odds) -->
                                <div style="display: flex; gap: 8px;">
                                    <button onclick="placeBet(${match.id}, 'home', ${match.home_odds})" style="background: #2563eb; color: #fff; border: none; padding: 10px 14px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                                        1 (${match.home_odds})
                                    </button>
                                    <button onclick="placeBet(${match.id}, 'draw', ${match.draw_odds})" style="background: #4b5563; color: #fff; border: none; padding: 10px 14px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                                        X (${match.draw_odds})
                                    </button>
                                    <button onclick="placeBet(${match.id}, 'away', ${match.away_odds})" style="background: #dc2626; color: #fff; border: none; padding: 10px 14px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                                        2 (${match.away_odds})
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = htmlContent;
        })
        .catch(error => {
            console.error('ئاریشە د بارکرنا یاریان دا:', error);
        });
}

// فەنکشنا بەستنا گرەوێ
function placeBet(matchId, choice, odds) {
    const amount = prompt("بڕێ پارەی بنڤێسە بۆ دانا سەر ڤێ یاریێ:");
    if (!amount || amount <= 0) return;

    fetch(`${API_BASE_URL}/place_bet.php`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            match_id: matchId,
            choice: choice,
            odds: odds,
            amount: parseFloat(amount)
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        if (data.status === 'success') {
            location.reload();
        }
    })
    .catch(err => alert("ئاریشەک د شاندنا زانیاریان دا چێبوو!"));
}


// ==========================================
// 2. EXISTING UI CONTROLS & ANIMATIONS (مێنویێن تە)
// ==========================================

function initExistingUI() {

    // Favourites Tab js below
    const favorInner = document.getElementById('favor-inner');
    const favorSport = document.getElementById('favor-sport');
    const favorArrow = document.getElementById('favor-arrow');

    if (favorInner && favorSport && favorArrow) {
        favorInner.addEventListener('click', () => {
            favorSport.classList.toggle('fs-hide');
            favorArrow.classList.toggle('fs-arrow');
        });
    }

    // Sports list tab js below
    const sportInner = document.getElementsByClassName('sport-inner');
    const sportArrow = document.getElementsByClassName('favor-arrow');
    const sbContainer = document.getElementsByClassName('sb-container');

    for (let i = 0; i < sportInner.length; i++) {
        sportInner[i].addEventListener('click', () => {
            sbContainer[i].classList.toggle('sb-none');
            sportArrow[i].classList.toggle('sport-arrow');

            const theCSSprop = window.getComputedStyle(sportInner[i], null).getPropertyValue("border-left-color");
            if (sbContainer[i].classList.contains('sb-none')) {
                sportInner[i].style.backgroundColor = '';
            } else {
                sportInner[i].style.backgroundColor = theCSSprop;
            }
        });
    }

    // Sub-Sports list tab js below
    const sbInner = document.getElementsByClassName('sb-inner');
    const sbSport = document.getElementsByClassName('sb-sport');
    const sbArrow = document.getElementsByClassName('sb-arrow');

    for (let i = 0; i < sbInner.length; i++) {
        sbInner[i].addEventListener('click', () => {
            sbSport[i].classList.toggle('sb-hide');
            sbArrow[i].classList.toggle('sub-arrow');
        });
    }

    // Sub Sub-Sports list tab js below
    const sbiArrow = document.getElementsByClassName('sbi-right-b');
    const sbiSport = document.getElementsByClassName('sbi-under-inner');

    for (let i = 0; i < sbiArrow.length; i++) {
        sbiArrow[i].addEventListener('click', () => {
            sbiArrow[i].classList.toggle('sbi-arrow');
            sbiSport[i].classList.toggle('sb-none');
        });
    }

    // Top Leagues Tab JS functionality
    const tlInner = document.getElementById('tl-inner');
    const tlArrow = document.getElementById('tl-arrow');
    const tlList = document.getElementById('tl-list');

    if (tlInner && tlArrow && tlList) {
        tlInner.addEventListener('click', () => {
            tlArrow.classList.toggle('flip-on');
            tlList.classList.toggle('height-off');
        });
    }

    // Sports List Tab JS functionality
    const gamesItemA = document.getElementsByClassName('games-item-a');
    const gibArrow = document.getElementsByClassName('gi-b-arrow');
    const gamesItemB = document.getElementsByClassName('games-item-b');

    for (let i = 0; i < gamesItemA.length; i++) {
        gamesItemA[i].addEventListener('click', () => {
            gibArrow[i].classList.toggle('flip-on');
            gamesItemB[i].classList.toggle('disp-on');

            const theCSSprop = window.getComputedStyle(gamesItemA[i], null).getPropertyValue("border-left-color");
            if (!gamesItemB[i].classList.contains('disp-on')) {
                gamesItemA[i].style.backgroundColor = '';
            } else {
                gamesItemA[i].style.backgroundColor = theCSSprop;
            }
        });
    }

    // Sub-Sports List Tab JS functionality
    const subGamesItemA = document.getElementsByClassName('sub-games-item-a');
    const sgibArrow = document.getElementsByClassName('sgi-b-arrow');
    const subGamesItemB = document.getElementsByClassName('sub-games-item-b');

    for (let i = 0; i < subGamesItemA.length; i++) {
        subGamesItemA[i].addEventListener('click', () => {
            sgibArrow[i].classList.toggle('flip-on');
            subGamesItemB[i].classList.toggle('disp-on');
        });
    }

    // Databox Tab JS functionality
    const boxArrow = document.getElementsByClassName('data-arrow');
    const dataBoxB = document.getElementsByClassName('data-box-b');

    for (let i = 0; i < boxArrow.length; i++) {
        boxArrow[i].addEventListener('click', () => {
            boxArrow[i].classList.toggle('sbi-arrow');
            dataBoxB[i].classList.toggle('sb-none');
        });
    }
}
