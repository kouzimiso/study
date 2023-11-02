import networkx as nx
import matplotlib.pyplot as plt
import random

# グローバル変数
G = nx.Graph()
pos = nx.spring_layout(G)
fig, ax = plt.subplots()

def update_network():
    # ネットワークを更新する処理をここに書く
    global G, pos
    G = nx.erdos_renyi_graph(10, 0.3)
    pos = nx.spring_layout(G)

def redraw_plot():
    # プロットを更新する処理をここに書く
    global G, pos
    ax.clear()
    nx.draw(G, pos, with_labels=True)
    plt.pause(0.01)

def animate():
    while True:
        # ネットワークが更新されたかどうかをチェックする
        update_network_flag = random.choice([True, False])
        if update_network_flag:
            update_network()

        redraw_plot()

if __name__ == '__main__':
    animate()
