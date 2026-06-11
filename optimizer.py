import random
import math
import copy

# ---------------------------------------------------------------------------
# CONSTANTS  (adjust to match your problem)
# ---------------------------------------------------------------------------
TOTAL_TIMESLOTS = 40        # total available slots in the timetable
POPULATION_SIZE = 100       # number of chromosomes per generation
GENERATIONS     = 200       # GA iteration limit
ELITE_RATIO     = 0.10      # top 10 % preserved each generation
PARENT_POOL_RATIO = 0.20    # top 20 % eligible as crossover parents
MUTATION_RATE   = 0.05      # 5 % chance a child is mutated

SA_INITIAL_TEMP  = 100.0
SA_COOLING_RATE  = 0.95
SA_MIN_TEMP      = 0.1
SA_MAX_STAGNANT  = 50       # reheat after this many non-improving SA steps


# ---------------------------------------------------------------------------
# PLACEHOLDER STUBS  –  replace with your real implementations
# ---------------------------------------------------------------------------
class Gene:
    """Represents a single class/subject assignment."""
    def __init__(self, slot_id: int):
        self.slot_id = slot_id

    def clone(self) -> "Gene":
        return Gene(self.slot_id)


class TimetableChromosome:
    """
    A candidate timetable solution.

    Fitness is computed lazily and cached; call invalidate() after any
    in-place mutation so the cache is refreshed on next access.
    """

    def __init__(self, genes: list[Gene]):
        self.genes   = genes
        self._fitness: float | None = None
        self._clashes: int  | None = None

    # ---- lazy-cached fitness -----------------------------------------------

    @property
    def fitness(self) -> float:
        if self._fitness is None:
            self._compute()
        return self._fitness          # type: ignore[return-value]

    @property
    def clashes(self) -> int:
        if self._clashes is None:
            self._compute()
        return self._clashes          # type: ignore[return-value]

    def invalidate(self) -> None:
        """Call this whenever genes are changed so the cache is cleared."""
        self._fitness = None
        self._clashes = None

    # ---- internal computation ----------------------------------------------

    def _compute(self) -> None:
        """
        Replace this body with your real clash-detection + scoring logic.
        Higher fitness  →  better schedule.
        """
        # --- stub: count duplicate slot_ids as clashes ---------------------
        seen: set[int] = set()
        clashes = 0
        for gene in self.genes:
            if gene.slot_id in seen:
                clashes += 1
            seen.add(gene.slot_id)
        # -------------------------------------------------------------------
        self._clashes = clashes
        self._fitness = 1.0 / (1.0 + clashes)   # higher = fewer clashes


def generate_random_population(size: int) -> list[TimetableChromosome]:
    """Return `size` randomly initialised chromosomes."""
    population = []
    for _ in range(size):
        # stub: 10 genes per chromosome; adapt to your real gene count
        genes = [Gene(random.randint(1, TOTAL_TIMESLOTS)) for _ in range(10)]
        population.append(TimetableChromosome(genes))
    return population


def create_neighbor_schedule(solution: TimetableChromosome) -> TimetableChromosome:
    """
    Return a *new* chromosome that differs from `solution` by one gene tweak.
    Deep-copied so the original is never modified.
    """
    neighbor = TimetableChromosome(copy.deepcopy(solution.genes))
    gene = random.choice(neighbor.genes)
    gene.slot_id = random.randint(1, TOTAL_TIMESLOTS)
    neighbor.invalidate()
    return neighbor


# ---------------------------------------------------------------------------
# 1. GENETIC ALGORITHM
# ---------------------------------------------------------------------------

def genetic_algorithm(
    population: list[TimetableChromosome],
    generations: int = GENERATIONS,
) -> TimetableChromosome:
    """
    Evolve `population` for up to `generations` generations.

    Improvements over the original:
      • Parent pool is a % of population (not a hardcoded 50).
      • Child genes are deep-copied before mutation so parents are never
        corrupted.
      • Fitness is cached on each chromosome (O(1) repeated access).
      • Generation number is logged when a perfect solution is found early.
    """
    for generation in range(generations):

        # --- sort by cached fitness (calculate_fitness called once each) ---
        population.sort(key=lambda x: x.fitness, reverse=True)

        best = population[0]
        if best.clashes == 0:
            print(f"[GA] Perfect solution found at generation {generation}.")
            return best

        elite_count   = max(1, int(ELITE_RATIO      * len(population)))
        parent_pool_n = max(2, int(PARENT_POOL_RATIO * len(population)))
        parent_pool   = population[:parent_pool_n]

        next_generation: list[TimetableChromosome] = list(population[:elite_count])

        while len(next_generation) < len(population):
            parent_a = random.choice(parent_pool)
            parent_b = random.choice(parent_pool)

            # Crossover: deep-copy genes so parents are never mutated
            split = len(parent_a.genes) // 2
            child_genes = (
                copy.deepcopy(parent_a.genes[:split])
                + copy.deepcopy(parent_b.genes[split:])
            )
            child = TimetableChromosome(child_genes)

            # Mutation: change one random gene's slot
            if random.random() < MUTATION_RATE:
                random.choice(child.genes).slot_id = random.randint(
                    1, TOTAL_TIMESLOTS
                )
                child.invalidate()

            next_generation.append(child)

        population = next_generation

    population.sort(key=lambda x: x.fitness, reverse=True)
    print(f"[GA] Finished {generations} generations. "
          f"Best clashes: {population[0].clashes}")
    return population[0]


# ---------------------------------------------------------------------------
# 2. SIMULATED ANNEALING
# ---------------------------------------------------------------------------

def simulated_annealing(
    best_ga_timetable: TimetableChromosome,
    initial_temp: float = SA_INITIAL_TEMP,
    cooling_rate: float = SA_COOLING_RATE,
) -> TimetableChromosome:
    """
    Refine a GA solution with SA.

    Improvements over the original:
      • Tracks the global best separately so regression is impossible.
      • Adaptive reheat: if SA stagnates for SA_MAX_STAGNANT steps the
        temperature is partially restored to escape new local minima.
    """
    current_solution = best_ga_timetable
    current_clashes  = current_solution.clashes

    # Track the best solution seen across ALL SA steps
    best_solution = current_solution
    best_clashes  = current_clashes

    temp            = initial_temp
    stagnant_iters  = 0
    prev_clashes    = current_clashes

    step = 0
    while temp > SA_MIN_TEMP and best_clashes > 0:
        neighbor         = create_neighbor_schedule(current_solution)
        neighbor_clashes = neighbor.clashes

        if neighbor_clashes < current_clashes:
            # Strictly better → always accept
            current_solution = neighbor
            current_clashes  = neighbor_clashes
        else:
            # Worse → accept probabilistically
            delta       = neighbor_clashes - current_clashes
            probability = math.exp(-delta / temp)
            if random.random() < probability:
                current_solution = neighbor
                current_clashes  = neighbor_clashes

        # Update global best
        if current_clashes < best_clashes:
            best_solution = current_solution
            best_clashes  = current_clashes

        # Stagnation detection & adaptive reheat
        if current_clashes == prev_clashes:
            stagnant_iters += 1
        else:
            stagnant_iters = 0

        if stagnant_iters >= SA_MAX_STAGNANT:
            temp           = min(temp * 2.0, initial_temp * 0.5)
            stagnant_iters = 0
            print(f"[SA] Reheat at step {step}  |  temp → {temp:.4f}  "
                  f"|  best clashes: {best_clashes}")

        prev_clashes = current_clashes
        temp        *= cooling_rate
        step        += 1

    print(f"[SA] Finished after {step} steps. Best clashes: {best_clashes}")
    return best_solution   # guaranteed ≤ the GA result


# ---------------------------------------------------------------------------
# 3. HYBRID EXECUTION
# ---------------------------------------------------------------------------

def main() -> None:
    # Step 1: random starting population
    initial_population = generate_random_population(size=POPULATION_SIZE)

    # Step 2: GA produces a strong candidate
    best_from_ga = genetic_algorithm(initial_population, generations=GENERATIONS)

    # Step 3: SA polishes the result if it still has clashes
    if best_from_ga.clashes > 0:
        final_timetable = simulated_annealing(best_from_ga)
    else:
        final_timetable = best_from_ga

    print(f"\nFinal clashes: {final_timetable.clashes}")
    print("Slot assignments:",
          [g.slot_id for g in final_timetable.genes])


if __name__ == "__main__":
    main()