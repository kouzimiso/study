// フローチャートのデータ
const flowchartData = {
    "nodes": [
        {"id": "A", "label": "Node A", "noRepel": false},
        {"id": "B", "label": "Node B", "noRepel": false},
        {"id": "C", "label": "Node C", "noRepel": false},
        {"id": "D", "label": "Node D", "noRepel": false},
        {"id": "E", "label": "Node E", "noRepel": false},
        {"id": "F", "label": "Node F", "noRepel": false}
    ],
    "flows": [
        {"source": "A", "target": "B"},
        {"source": "A", "target": "C"},
    ]
};

// JSONファイル読み込み処理
document.getElementById("fileInput").addEventListener("change", function (e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (event) {
            try {
                flowchartData = JSON.parse(event.target.result);
                displayFlowchart(flowchartData);
            } catch (error) {
                alert("Invalid JSON format: " + error);
            }
        };
        reader.readAsText(file);
    }
});

// チャートの表示処理
function displayFlowchart(data) {


// SVG要素の幅と高さを設定
const width = window.innerWidth;
const height = window.innerHeight;

// D3.jsの力学的なシミュレーションを作成
const simulation = d3.forceSimulation()
.force("link", d3.forceLink().id(d => d.id).strength(0.1)) // リンクの強度を調整
    .force("charge", d3.forceManyBody().strength(d => d.noRepel ? 0:-100))
    .force("center", d3.forceCenter(width / 2, height / 2));

// ノードとフローをシミュレーションに結びつける
simulation.nodes(flowchartData.nodes)
    .on("tick", ticked);

simulation.force("link")
    .links(flowchartData.flows);

// SVG要素を選択
const svg = d3.select("#flowchart")
    .attr("width", width)
    .attr("height", height);

// ノードとフローの描画
const link = svg.append("g")
    .selectAll("line")
    .data(flowchartData.flows)
    .enter()
    .append("line")
    .style("stroke", "gray");

const node = svg.append("g")
    .selectAll("circle")
    .data(Object.values(flowchartData.nodes))
    .enter()
    .append("circle")
    .attr("r", 40)
    .style("fill", "red") // ノードの色を赤色に変更
    .call(d3.drag()
        .on("start", dragStarted)
        .on("drag", dragging)
        .on("end", dragEnded));

const text = svg.append("g")
    .selectAll("text")
    .data(Object.values(flowchartData.nodes))
    .enter()
    .append("text")
    .text(d => d.label)
    .style("text-anchor", "middle")
    .style("dominant-baseline", "middle")
    .style("fill", "black");

// ノードとフローをシミュレーションに結びつける
simulation.nodes(Object.values(flowchartData.nodes))
    .on("tick", ticked);

simulation.force("link")
    .links(flowchartData.flows);

// シミュレーションが進行するたびに呼ばれる関数
function ticked() {
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

    node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);

    text
        .attr("x", d => d.x)
        .attr("y", d => d.y);
}

// ドラッグ操作のコールバック関数
function dragStarted(d) {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragging(d) {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
}

function dragEnded(d) {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}




    // チャート表示のロジックをここに追加
    // data変数を使用してデータを図示
}

// "Load JSON"ボタンのクリックイベント
document.getElementById("loadButton").addEventListener("click", function () {
    if (flowchartData) {
        displayFlowchart(flowchartData);
    } else {
        alert("No JSON data loaded.");
    }
});

// Printボタンのクリックイベント
document.getElementById("printButton").addEventListener("click", function () {
    if (flowchartData) {
        // チャートコンテナを一時的に非表示にし、HTML2Canvasを使用して画像に変換
        const chartContainer = document.getElementById("chart");
        chartContainer.style.display = "none";

        html2canvas(chartContainer, { scale: 2 }).then(canvas => {
            const image = canvas.toDataURL("image/png");

            // 画像を新しいウィンドウで開いて印刷
            const printWindow = window.open("", "", "width=800,height=600");
            printWindow.document.open();
            printWindow.document.write("<img src='" + image + "'>");
            printWindow.document.close();
            printWindow.print();
            printWindow.close();

            // チャートコンテナを再表示
            chartContainer.style.display = "block";
        });
    } else {
        alert("No chart data available for printing.");
    }
});

// JSONファイル読み込み処理
document.getElementById("fileInput").addEventListener("change", function (e) {
    // 以前のデータをクリア
    d3.select("#chart").selectAll("*").remove();
    
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (event) {
            try {
                flowchartData = JSON.parse(event.target.result);
                displayFlowchart(flowchartData);
            } catch (error) {
                alert("Invalid JSON format: " + error);
            }
        };
        reader.readAsText(file);
    }
});

// 初回表示時の処理
displayFlowchart(flowchartData);