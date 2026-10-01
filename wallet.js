document.getElementById('withdrawForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const method = document.getElementById('withdrawMethod').value;
    const accountNum = document.getElementById('withdrawAccount').value;
    const amount = document.getElementById('withdrawAmount').value;
    const msgEl = document.getElementById('withdrawMsg');

    msgEl.style.color = '#fff';
    msgEl.textContent = 'چاوەڕێ بە، داواکاری دهێتە ناردن...';

    try {
        const response = await fetch('/api/withdraw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                amount: parseFloat(amount),
                method: method,
                accountNum: accountNum
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            msgEl.style.color = '#2ecc71';
            msgEl.textContent = data.message || 'داواکارییا ڕاکێشانێ ب سەرکەفتیانە هاتە هنارتن!';
            
            // نوێکردنەوەی لاپەڕە دوای سەرکەوتنی پرۆسەکە بۆ نیشاندانی باڵانسی نوێ
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            msgEl.style.color = '#e74c3c';
            msgEl.textContent = data.error || 'هەڵەیەک ڕووی دا!';
        }
    } catch (err) {
        console.error(err);
        msgEl.style.color = '#e74c3c';
        msgEl.textContent = 'کێشە لە پەیوەندیکردن بەگەڵ سێرڤەری هەەیە!';
    }
});
