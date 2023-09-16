// 方程式を解析し、結果を計算する関数
function parseAndCalculateEquation() {
    const equationInput = document.getElementById("equationInput");
    const resultDiv = document.getElementById("result");
    const equation = equationInput.value;

    try {
        const parseResult = equationParser().parse(equation);
        const result = parseResult.result;
        resultDiv.innerText = `解: ${result}`;
    } catch (error) {
        resultDiv.innerText = `エラー: ${error.message}`;
    }
}

// 解析と計算を実行する関数をボタンのクリックイベントに追加
function solveEquation() {
    parseAndCalculateEquation();
}
