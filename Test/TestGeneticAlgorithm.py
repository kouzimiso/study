import random

# ジョブ数と機械数
num_jobs = 3
num_machines = 2

# 各ジョブの実行時間
job_times = [5, 3, 2]

# 遺伝子の長さ（ジョブ数）
gene_length = num_jobs



# 遺伝子をランダムに生成する関数
def generate_random_gene():
    return [random.randint(1, num_machines) for _ in range(gene_length)]  # 各ジョブにランダムに機械を割り当てる

# 遺伝子を評価する関数（適応度関数）
def evaluate_gene(gene):
    machine_times = [0] * num_machines  # 各機械の実行時間を初期化
    for i in range(num_jobs):
        machine = gene[i] - 1  # 機械番号は1から始まるため、0から始まるインデックスに変換
        machine_times[machine] += job_times[i]
    return max(machine_times)  # 最も遅い機械の実行時間を返す

# 遺伝的アルゴリズムのパラメータ
population_size = 100
mutation_rate = 0.01
num_generations = 100

# 初期集団を生成
population = [generate_random_gene() for _ in range(population_size)]

# 開始時の目的を表示
print("ジョブスケジューリング問題を解決します。最も遅い機械の実行時間を最小化します。")
print(f"num_jobs = {num_jobs}: num_machines = {num_machines}, job_times  {job_times}")
# 遺伝的アルゴリズムのメインループ
for generation in range(num_generations):
    # 適応度に基づいて集団をソート
    population = sorted(population, key=evaluate_gene)
    
    # 最良の個体を表示
    best_gene = population[0]
    best_fitness = evaluate_gene(best_gene)
    print(f"Generation {generation+1}: Best Gene = {best_gene}, Best Fitness = {best_fitness}")
    # 世代数、最良の遺伝子、最良の適応度を表示

    # 次世代の集団を生成
    new_population = [best_gene]  # 最良個体を次世代に追加
    while len(new_population) < population_size:
        parent1 = random.choice(population)
        parent2 = random.choice(population)
        crossover_point = random.randint(1, gene_length - 1)
        child = parent1[:crossover_point] + parent2[crossover_point:]
        
        # 突然変異を適用
        if random.random() < mutation_rate:
            mutation_point = random.randint(0, gene_length - 1)
            child[mutation_point] = random.randint(1, num_machines)
        
        new_population.append(child)
    
    population = new_population

# 最終的な最良の遺伝子と適応度を表示
best_gene = population[0]
best_fitness = evaluate_gene(best_gene)
print(f"Final Best Gene = {best_gene}, Final Best Fitness = {best_fitness}")
# 最終的な最良の遺伝子とその適応度を表示
