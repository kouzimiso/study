// ランダムなスワップデータを生成する関数
function generateRandomSwapData() {
    const pairs = ['USD/JPY', 'EUR/USD', 'GBP/USD', 'AUD/USD', 'USD/CAD']; // 仮想の通貨ペア
    const data = [];
    const today = new Date();
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      const swapData = pairs.map(pair => ({
        pair: pair,
        swap: parseFloat((Math.random() * 5).toFixed(2)) // ランダムなスワップポイント（0～5の範囲）
      }));
      data.push({ date: date.toDateString(), swaps: swapData });
    }
    return data;
  }
  
  // チャートを描画する関数
  function drawChart() {
    const data = generateRandomSwapData();
  
    const labels = data.map(item => item.date);
    const datasets = data[0].swaps.map(pairData => ({
      label: pairData.pair,
      data: data.map(item => item.swaps.find(data => data.pair === pairData.pair).swap),
      borderColor: getRandomColor(),
      fill: false
    }));
  
    const ctx = document.getElementById('swapChart').getContext('2d');
    const swapChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: datasets
      },
      options: {
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });
  }
  
  // ランダムな色を取得する関数
  function getRandomColor() {
    return `#${Math.floor(Math.random()*16777215).toString(16)}`;
  }
  
  // チャートを描画
  drawChart();
  