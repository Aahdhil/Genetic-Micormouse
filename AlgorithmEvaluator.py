from env import Board
import time
import random
from Maze import Maze
from Algorithm import Dijkstra, BFS, A_search, Q_Learning
from collections import deque

class AlgorithmEvaluator:
    def __init__(self, board, num_mazes=1, train_q=1):
        self.board = board
        self.num_mazes = num_mazes
        self.train_q = train_q
        self.results = {
            'Dijkstra': [],
            'BFS': [],
            'A*': [],
            'Q-Learning': []
        }

    def evaluate_algorithms(self):
        print("\nRunning Genetic Algorithm to find best strategy across randomized mazes...")
        ga = GeneticAlgorithmOptimizer(self.board)
        best_config = ga.evolve()
        print(f"\n Best Strategy Found: {best_config}")


    def _get_path_len(self, algo):
        node = algo.target_node
        length = 0
        while node and node.parent:
            length += 1
            node = node.parent
        return length


class GeneticAlgorithmOptimizer:
    def __init__(self, board, population_size=10, generations=3):
        self.board = board
        self.population_size = population_size
        self.generations = generations
        self.algorithms = ["Dijkstra", "BFS", "A*", "Q-Learning"]

    def _find_nearest_passage(self, board, pos):
        visited = set()
        queue = deque([pos])
        while queue:
            r, c = queue.popleft()
            if (r, c) not in board.wall:
                return (r, c)
            visited.add((r, c))
            for _, (nr, nc) in board.neighbors((r, c), wall_included=True):
                if (nr, nc) not in visited:
                    queue.append((nr, nc))
        return pos

    def initialize_population(self):
        population = []
        for _ in range(self.population_size):
            algo = random.choice(self.algorithms)
            if algo == "Q-Learning":
                population.append({
                    "algorithm": algo,
                    "alpha": round(random.uniform(0.3, 0.9), 2),
                    "epsilon": round(random.uniform(0.1, 0.5), 2)
                })
            else:
                population.append({"algorithm": algo})
        return population

    def fitness(self, config):
        total_score = 0
        successful_runs = 0
        num_mazes = 1

        for _ in range(num_mazes):
            maze_board = Board(
                v_cells=self.board.v_cells,
                h_cells=self.board.h_cells,
                origin_x=self.board.origin_x,
                origin_y=self.board.origin_y,
                cell_size=self.board.cell_size,
                screen=self.board.screen,
                colors=self.board.colors
            )
            maze_board.start = self.board.start
            maze_board.target = self.board.target

            maze_gen = Maze(maze_board)
            maze_gen.initialize()
            maze_gen.generate()

            # Fix start and target if in wall
            if maze_board.start in maze_board.wall:
                maze_board.start = self._find_nearest_passage(maze_board, maze_board.start)
            if maze_board.target in maze_board.wall:
                maze_board.target = self._find_nearest_passage(maze_board, maze_board.target)

            algo = config["algorithm"]
            if algo == "Dijkstra":
                agent = Dijkstra(maze_board)
            elif algo == "BFS":
                agent = BFS(maze_board)
            elif algo == "A*":
                agent = A_search(maze_board)
            elif algo == "Q-Learning":
                agent = Q_Learning(maze_board, alpha=config["alpha"], epsilon=config["epsilon"])
            else:
                return 0

            try:
                start_time = time.time()
                if algo == "Q-Learning":
                    agent.solver(30)
                else:
                    agent.initialize()
                    agent.solver()
                end_time = time.time()

                if not agent.find:
                    continue

                path_len = len(maze_board.path) or self._get_path_len(agent)
                duration = end_time - start_time
                fitness_val = 1 / (path_len + duration + 1)
                total_score += fitness_val
                successful_runs += 1

            except:
                continue

        return total_score / successful_runs if successful_runs > 0 else 0

    def _get_path_len(self, algo):
        node = algo.target_node if hasattr(algo, "target_node") else None
        length = 0
        while node and node.parent:
            length += 1
            node = node.parent
        return length

    def evolve(self):
        population = self.initialize_population()
        for gen in range(self.generations):
            print(f"\nGeneration {gen+1}/{self.generations}")
            fitness_scores = [(self.fitness(ind), ind) for ind in population]
            fitness_scores.sort(key=lambda x: x[0], reverse=True)
            population = [ind for _, ind in fitness_scores[:self.population_size // 2]]

            children = []
            while len(children) < self.population_size - len(population):
                parent1, parent2 = random.sample(population, 2)
                child = self.crossover(parent1, parent2)
                self.mutate(child)
                children.append(child)
            population.extend(children)

        best_fit = max([(self.fitness(ind), ind) for ind in population], key=lambda x: x[0])
        return best_fit[1]

    def crossover(self, p1, p2):
        if p1["algorithm"] != "Q-Learning" or p2["algorithm"] != "Q-Learning":
            return random.choice([p1, p2])
        return {
            "algorithm": "Q-Learning",
            "alpha": round((p1["alpha"] + p2["alpha"]) / 2, 2),
            "epsilon": round((p1["epsilon"] + p2["epsilon"]) / 2, 2)
        }

    def mutate(self, config):
        if config["algorithm"] == "Q-Learning":
            if random.random() < 0.2:
                config["alpha"] = round(min(1.0, max(0.1, config["alpha"] + random.uniform(-0.1, 0.1))), 2)
            if random.random() < 0.2:
                config["epsilon"] = round(min(1.0, max(0.0, config["epsilon"] + random.uniform(-0.1, 0.1))), 2)

