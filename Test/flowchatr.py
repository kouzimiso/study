import tkinter as tk
import json

def on_node_click(event):
    global current_node
    node_id = event.widget.find_closest(event.x, event.y)[0]
    if node_id in nodes:
        current_node = node_id
        update_status_label(node_id)
        process_Graph()

def update_status_label(node_id):
    status_label.config(text=f"Current Node: {node_data[node_id]['label']}")

def create_arrow(canvas, start_node, end_node):
    x1, y1, x2, y2 = canvas.coords(start_node)
    x3, y3, x4, y4 = canvas.coords(end_node)
    return canvas.create_line(x1, y1, x3, y3, arrow=tk.LAST)

def process_Graph():
    global current_node
    for arrow in arrows:
        canvas.itemconfig(arrow, fill="black")

    for edge in edge_data:
        if edge["start"] == node_data[current_node]["id"]:
            if edge["condition"]:
                target_node = edge["end"]
                break

    for arrow in arrows:
        if arrow_data[arrow]["start"] == node_data[current_node]["id"] and arrow_data[arrow]["end"] == target_node:
            canvas.itemconfig(arrow, fill="green")
            current_node = target_node
            update_status_label(target_node)
            break
    else:
        if target_node in node_id_to_canvas_id:
            canvas.itemconfig(node_id_to_canvas_id[target_node], fill="green")
            current_node = target_node
            update_status_label(target_node)

def auto_layout(nodes_data, edges):
    node_positions = {}
    node_counts = {}
    vertical_spacing = 100
    horizontal_spacing = 150

    for edge in edges:
        node_counts[edge["start"]] = node_counts.get(edge["start"], 0) + 1
        node_counts[edge["end"]] = node_counts.get(edge["end"], 0)

    for node in nodes_data:
        node_id = node["id"]
        start_count = node_counts.get(node_id, 0)
        x = start_count * horizontal_spacing
        y = node_counts.get(node_id, 0) * vertical_spacing
        node_positions[node_id] = (x, y)

    return node_positions

root = tk.Tk()
root.title("Graph GUI")

canvas = tk.Canvas(root, width=800, height=600)
canvas.pack()

current_node = None
nodes = {}
node_data = {}
arrows = []
arrow_data = {}
edge_data = []
node_id_to_canvas_id = {}

# Load data from JSON file
with open("flowchart.json", "r") as json_file:
    data = json.load(json_file)
    nodes_data = data["nodes"]
    edge_data = data["edges"]

# Auto-layout nodes
node_positions = auto_layout(nodes_data, edge_data)

# Create nodes
for node_info in nodes_data:
    x, y = node_positions.get(node_info["id"], (0, 0))
    node = canvas.create_rectangle(x - 50, y - 25, x + 50, y + 25, fill="lightblue")
    node_id = node_info["id"]
    nodes[node] = node_id
    node_data[node] = node_info
    node_id_to_canvas_id[node_id] = node

# Create arrows (connections)
for edge in edge_data:
    start_node_id = edge["start"]
    end_node_id = edge["end"]
    start_node = node_id_to_canvas_id[start_node_id]
    end_node = node_id_to_canvas_id[end_node_id]
    arrow = create_arrow(canvas, start_node, end_node)
    arrow_data[arrow] = {"start": start_node_id, "end": end_node_id}
    arrows.append(arrow)

# Create event binding
for node in nodes:
    canvas.tag_bind(node, '<Button-1>', on_node_click)

status_label = tk.Label(root, text="Current Node: None")
status_label.pack()

root.mainloop()
