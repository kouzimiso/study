def generate_html(Graph_data, output_file):
    # ノードの位置を自動的に設定
    node_positions = auto_layout(Graph_data["edges"])

    # HTMLのヘッダー
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Graph</title>
    <style>
        /* スタイルを追加することができます */
    </style>
</head>
<body>
    <svg width="1000" height="800">
"""

    # ノードを生成
    for node_id, node in Graph_data["nodes"].items():
        x, y = node_positions[node_id]
        label = node["label"]
        html_content += f'        <rect x="{x}" y="{y}" width="100" height="50" fill="lightblue" />\n'
        html_content += f'        <text x="{x + 10}" y="{y + 30}">{label}</text>\n'

    # フローを生成
    for edge in Graph_data["edges"]:
        start_node = edge["start"]
        end_node = edge["end"]
        # フローの開始ノードと終了ノードの座標を取得し、線を描画
        x1 = node_positions[start_node][0] + 100
        y1 = node_positions[start_node][1] + 25
        x2 = node_positions[end_node][0]
        y2 = node_positions[end_node][1] + 25
        html_content += f'        <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" />\n'

    # HTMLのフッター
    html_content += """
    </svg>
</body>
</html>
"""

    # HTMLをファイルに書き込む
    with open(output_file, "w") as file:
        file.write(html_content)

def auto_layout(edges):
    node_positions = {}
    position_x = 1
    position_y = 1

    for edge in edges:
        start_node = edge["start"]
        end_node = edge["end"]
        
        if start_node not in node_positions:
            node_positions[start_node] = (position_x, position_y)
            position_x += 1
        if end_node not in node_positions:
            node_positions[end_node] = (position_x, position_y)
            position_x += 1

    return node_positions

if __name__ == "__main__":
    Graph_data = {
        "nodes": {
            "A": {"label": "Node A"},
            "B": {"label": "Node B"},
            "C": {"label": "Node C"},
        },
        "edges": [
            {"start": "A", "end": "B"},
            {"start": "A", "end": "C"},
        ]
    }

    generate_html(Graph_data, "Graph.html")
