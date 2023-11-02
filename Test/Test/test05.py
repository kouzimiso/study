import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random

# 初期状態のグラフを作成
G = nx.Graph()
G.add_node(0)
pos = {0: (0, 0)}

# グラフの描画
nx.draw(G, pos)

# 新しいノードを追加する関数
def add_node(G):
    n = G.number_of_nodes()
    G.add_node(n)
    pos[n] = (random.uniform(-1, 1), random.uniform(-1, 1))

# 新しいエッジを追加する関数
def add_edge(G):
    if G.number_of_nodes() >= 2:
        u, v = random.sample(G.nodes(), 2)
        G.add_edge(u, v)

# ノードとエッジを増やしながらグラフをアニメーション表示する関数
def animate(i):
    if i % 2 == 0:
        add_node(G)
    else:
        add_edge(G)
    plt.clf()
    nx.draw(G, pos)

# アニメーションの作成
ani = animation.FuncAnimation(plt.gcf(), animate, frames=20, interval=500)
plt.show()
