"""
timetable_demo.py  –  Self-contained runnable demo
====================================================
Schedules 12 university courses across 5 halls and 40 timeslots using
the hybrid GA + SA algorithm. No external libraries required.

Run:
    python timetable_demo.py
    python timetable_demo.py --seed 99        # reproducible run
    python timetable_demo.py --fast           # fewer generations (quicker)
    python timetable_demo.py --hard           # harder problem (more courses)
"""

import argparse
import copy
import math
import random
import sys
from dataclasses import dataclass

# ===========================================================================
# 0. SAMPLE UNIVERSITY DATA
# ===========================================================================

# --- Halls (venue, capacity) ------------------------------------------------
HALLS = [
    {"id": 1, "name": "Lecture Theatre A", "capacity": 300},
    {"id": 2, "name": "Lecture Theatre B", "capacity": 200},
    {"id": 3, "name": "Seminar Room 1",    "capacity":  80},
    {"id": 4, "name": "Seminar Room 2",    "capacity":  60},
    {"id": 5, "name": "Computer Lab",      "capacity":  40},
]

# --- Timeslots: Mon–Fri, 8 slots/day = 40 slots total ----------------------
DAYS  = ["Mon", "Tue", "Wed", "Thu", "Fri"]
TIMES = ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"]
# slot_id = (day_index * 8) + time_index + 1  →  1 … 40
TOTAL_TIMESLOTS = len(DAYS) * len(TIMES)   # 40

def slot_label(slot_id: int) -> str:
    """Convert a 1-based slot_id to a human-readable label."""
    idx  = slot_id - 1
    day  = DAYS[idx // len(TIMES)]
    time = TIMES[idx % len(TIMES)]
    return f"{day} {time}"

# --- Courses ----------------------------------------------------------------
COURSES_NORMAL = [
    {"id":  1, "code": "CS101",  "name": "Intro to Programming",      "students": 280, "lecturer": "Dr. Eze"},
    {"id":  2, "code": "CS201",  "name": "Data Structures",           "students": 190, "lecturer": "Dr. Bello"},
    {"id":  3, "code": "CS301",  "name": "Algorithms",                "students": 150, "lecturer": "Dr. Okafor"},
    {"id":  4, "code": "CS401",  "name": "Operating Systems",         "students":  70, "lecturer": "Dr. Eze"},
    {"id":  5, "code": "CS205",  "name": "Database Systems",          "students":  55, "lecturer": "Dr. Adeyemi"},
    {"id":  6, "code": "CS305",  "name": "Computer Networks",         "students":  35, "lecturer": "Dr. Bello"},
    {"id":  7, "code": "MATH101","name": "Calculus I",                "students": 260, "lecturer": "Prof. Nwosu"},
    {"id":  8, "code": "MATH201","name": "Linear Algebra",            "students": 170, "lecturer": "Prof. Nwosu"},
    {"id":  9, "code": "MATH301","name": "Probability & Statistics",  "students":  75, "lecturer": "Dr. Chukwu"},
    {"id": 10, "code": "ENG101", "name": "Technical Writing",         "students":  50, "lecturer": "Dr. Adeyemi"},
    {"id": 11, "code": "PHY101", "name": "Physics I",                 "students": 230, "lecturer": "Dr. Okafor"},
    {"id": 12, "code": "PHY201", "name": "Physics II",                "students":  38, "lecturer": "Dr. Chukwu"},
]

COURSES_HARD = COURSES_NORMAL + [
    {"id": 13, "code": "CS302",  "name": "Software Engineering",      "students":  90, "lecturer": "Dr. Eze"},
    {"id": 14, "code": "CS402",  "name": "Artificial Intelligence",   "students":  60, "lecturer": "Dr. Bello"},
    {"id": 15, "code": "MATH401","name": "Numerical Methods",         "students":  45, "lecturer": "Prof. Nwosu"},
    {"id": 16, "code": "ENG201", "name": "Research Methods",          "students":  30, "lecturer": "Dr. Adeyemi"},
]


# ===========================================================================
# 1. DOMAIN-SPECIFIC GENE & CHROMOSOME
# ===========================================================================

@dataclass
class CourseGene:
    """One scheduling decision: assign course → slot + hall."""
    course_id: int
    slot_id:   int
    hall_id:   int

    def clone(self) -> "CourseGene":
        return CourseGene(self.course_id, self.slot_id, self.hall_id)


class TimetableChromosome:
    """
    A complete candidate timetable.
    genes  = one CourseGene per course (same order as COURSES list).
    """

    def __init__(self, genes: list[CourseGene], courses: list[dict], halls: list[dict]):
        self.genes   = genes
        self.courses = courses
        self.halls   = halls
        self._fitness: float | None = None
        self._clashes: int   | None = None
        self._clash_detail: list[str] = []

    # ---- lazy cache --------------------------------------------------------

    @property
    def fitness(self) -> float:
        if self._fitness is None:
            self._compute()
        return self._fitness  # type: ignore[return-value]

    @property
    def clashes(self) -> int:
        if self._clashes is None:
            self._compute()
        return self._clashes  # type: ignore[return-value]

    @property
    def clash_detail(self) -> list[str]:
        if self._clashes is None:
            self._compute()
        return self._clash_detail

    def invalidate(self) -> None:
        self._fitness = None
        self._clashes = None
        self._clash_detail = []

    # ---- clash detection ---------------------------------------------------

    def _compute(self) -> None:
        clash_count = 0
        details: list[str] = []

        course_map = {c["id"]: c for c in self.courses}
        hall_map   = {h["id"]: h for h in self.halls}

        # Index genes by slot for quick lookup
        slot_index: dict[int, list[CourseGene]] = {}
        for g in self.genes:
            slot_index.setdefault(g.slot_id, []).append(g)

        for slot_id, genes_in_slot in slot_index.items():
            label = slot_label(slot_id)

            # Rule 1 – Hall double-booking: two courses in the same hall & slot
            hall_counts: dict[int, list[int]] = {}
            for g in genes_in_slot:
                hall_counts.setdefault(g.hall_id, []).append(g.course_id)
            for hall_id, cids in hall_counts.items():
                if len(cids) > 1:
                    names = " & ".join(course_map[c]["code"] for c in cids)
                    details.append(
                        f"  HALL CLASH  @ {label} in {hall_map[hall_id]['name']}: {names}"
                    )
                    clash_count += len(cids) - 1

            # Rule 2 – Lecturer double-booking: same lecturer in two courses same slot
            lect_counts: dict[str, list[int]] = {}
            for g in genes_in_slot:
                lec = course_map[g.course_id]["lecturer"]
                lect_counts.setdefault(lec, []).append(g.course_id)
            for lec, cids in lect_counts.items():
                if len(cids) > 1:
                    names = " & ".join(course_map[c]["code"] for c in cids)
                    details.append(
                        f"  LECT CLASH  @ {label} — {lec} assigned to {names}"
                    )
                    clash_count += len(cids) - 1

            # Rule 3 – Overcrowding: course assigned to hall too small
            for g in genes_in_slot:
                students = course_map[g.course_id]["students"]
                capacity = hall_map[g.hall_id]["capacity"]
                if students > capacity:
                    details.append(
                        f"  CAPACITY    @ {label}: {course_map[g.course_id]['code']} "
                        f"needs {students} seats but {hall_map[g.hall_id]['name']} "
                        f"holds {capacity}"
                    )
                    clash_count += 1

        self._clashes      = clash_count
        self._clash_detail = details
        self._fitness      = 1.0 / (1.0 + clash_count)


# ===========================================================================
# 2. POPULATION & NEIGHBOUR HELPERS
# ===========================================================================

def _random_gene(course: dict, halls: list[dict]) -> CourseGene:
    """Pick a slot + a hall large enough for this course (best-effort)."""
    viable_halls = [h for h in halls if h["capacity"] >= course["students"]]
    if not viable_halls:
        viable_halls = halls          # fall back to any hall
    return CourseGene(
        course_id = course["id"],
        slot_id   = random.randint(1, TOTAL_TIMESLOTS),
        hall_id   = random.choice(viable_halls)["id"],
    )


def generate_random_population(
    size: int,
    courses: list[dict],
    halls: list[dict],
) -> list[TimetableChromosome]:
    population = []
    for _ in range(size):
        genes = [_random_gene(c, halls) for c in courses]
        population.append(TimetableChromosome(genes, courses, halls))
    return population


def create_neighbor_schedule(solution: TimetableChromosome) -> TimetableChromosome:
    """Tweak one random gene (change its slot OR its hall)."""
    neighbor = TimetableChromosome(
        copy.deepcopy(solution.genes),
        solution.courses,
        solution.halls,
    )
    gene   = random.choice(neighbor.genes)
    course = next(c for c in neighbor.courses if c["id"] == gene.course_id)

    if random.random() < 0.5:
        gene.slot_id = random.randint(1, TOTAL_TIMESLOTS)
    else:
        viable = [h for h in neighbor.halls if h["capacity"] >= course["students"]]
        if viable:
            gene.hall_id = random.choice(viable)["id"]

    neighbor.invalidate()
    return neighbor


# ===========================================================================
# 3. GA + SA  (unchanged algorithm, now wired to real domain objects)
# ===========================================================================

def genetic_algorithm(
    population: list[TimetableChromosome],
    generations: int,
    elite_ratio: float      = 0.10,
    parent_pool_ratio: float = 0.20,
    mutation_rate: float    = 0.05,
    verbose: bool           = True,
) -> TimetableChromosome:

    for gen in range(generations):
        population.sort(key=lambda x: x.fitness, reverse=True)
        best = population[0]

        if verbose and gen % 25 == 0:
            print(f"  [GA] gen {gen:>4}  |  best clashes: {best.clashes}")

        if best.clashes == 0:
            print(f"  [GA] ✓ Perfect solution at generation {gen}!")
            return best

        elite_n  = max(1, int(elite_ratio * len(population)))
        pool_n   = max(2, int(parent_pool_ratio * len(population)))
        pool     = population[:pool_n]
        next_gen: list[TimetableChromosome] = list(population[:elite_n])

        while len(next_gen) < len(population):
            pa = random.choice(pool)
            pb = random.choice(pool)
            split      = len(pa.genes) // 2
            child_genes = (
                copy.deepcopy(pa.genes[:split])
                + copy.deepcopy(pb.genes[split:])
            )
            child = TimetableChromosome(child_genes, pa.courses, pa.halls)
            if random.random() < mutation_rate:
                g      = random.choice(child.genes)
                course = next(c for c in child.courses if c["id"] == g.course_id)
                if random.random() < 0.5:
                    g.slot_id = random.randint(1, TOTAL_TIMESLOTS)
                else:
                    viable = [h for h in child.halls if h["capacity"] >= course["students"]]
                    if viable:
                        g.hall_id = random.choice(viable)["id"]
                child.invalidate()
            next_gen.append(child)

        population = next_gen

    population.sort(key=lambda x: x.fitness, reverse=True)
    print(f"  [GA] Finished {generations} gens. Best clashes: {population[0].clashes}")
    return population[0]


def simulated_annealing(
    solution: TimetableChromosome,
    initial_temp: float  = 100.0,
    cooling_rate: float  = 0.95,
    min_temp: float      = 0.1,
    max_stagnant: int    = 50,
    verbose: bool        = True,
) -> TimetableChromosome:

    current          = solution
    current_clashes  = current.clashes
    best             = current
    best_clashes     = current_clashes
    temp             = initial_temp
    stagnant         = 0
    prev_clashes     = current_clashes
    step             = 0

    while temp > min_temp and best_clashes > 0:
        neighbor         = create_neighbor_schedule(current)
        neighbor_clashes = neighbor.clashes

        if neighbor_clashes < current_clashes:
            current, current_clashes = neighbor, neighbor_clashes
        else:
            delta = neighbor_clashes - current_clashes
            if random.random() < math.exp(-delta / temp):
                current, current_clashes = neighbor, neighbor_clashes

        if current_clashes < best_clashes:
            best, best_clashes = current, current_clashes

        stagnant = stagnant + 1 if current_clashes == prev_clashes else 0
        if stagnant >= max_stagnant:
            temp     = min(temp * 2.0, initial_temp * 0.5)
            stagnant = 0
            if verbose:
                print(f"  [SA] Reheat @ step {step:>5}  temp→{temp:.3f}  "
                      f"best clashes: {best_clashes}")

        prev_clashes  = current_clashes
        temp         *= cooling_rate
        step         += 1

    print(f"  [SA] Done after {step} steps. Best clashes: {best_clashes}")
    return best


# ===========================================================================
# 4. PRETTY-PRINT THE FINAL TIMETABLE
# ===========================================================================

def print_timetable(t: TimetableChromosome) -> None:
    course_map = {c["id"]: c for c in t.courses}
    hall_map   = {h["id"]: h for h in t.halls}

    # Group by day
    by_day: dict[str, list[tuple[str, CourseGene]]] = {d: [] for d in DAYS}
    for g in sorted(t.genes, key=lambda x: x.slot_id):
        idx  = g.slot_id - 1
        day  = DAYS[idx // len(TIMES)]
        time = TIMES[idx % len(TIMES)]
        by_day[day].append((time, g))

    sep = "─" * 90
    print(f"\n{'═'*90}")
    print(f"  FINAL TIMETABLE   (clashes: {t.clashes})")
    print(f"{'═'*90}")

    for day in DAYS:
        entries = by_day[day]
        if not entries:
            continue
        print(f"\n  ▌ {day}")
        print(f"  {sep}")
        print(f"  {'Time':<8}  {'Course':<10}  {'Title':<30}  {'Hall':<22}  {'Lecturer':<18}  Students")
        print(f"  {sep}")
        for time, g in entries:
            c    = course_map[g.course_id]
            hall = hall_map[g.hall_id]
            cap_warn = " ⚠" if c["students"] > hall["capacity"] else ""
            print(
                f"  {time:<8}  {c['code']:<10}  {c['name']:<30}  "
                f"{hall['name']:<22}  {c['lecturer']:<18}  "
                f"{c['students']}/{hall['capacity']}{cap_warn}"
            )
        print(f"  {sep}")

    if t.clashes > 0:
        print(f"\n  ⚠  {t.clashes} unresolved clash(es):")
        for d in t.clash_detail:
            print(d)
    else:
        print("\n  ✓  Zero clashes — schedule is conflict-free!")
    print()


# ===========================================================================
# 5. MAIN ENTRY POINT
# ===========================================================================

def parse_args():
    p = argparse.ArgumentParser(description="Timetable Scheduler Demo")
    p.add_argument("--seed",  type=int, default=None,  help="Random seed for reproducibility")
    p.add_argument("--fast",  action="store_true",     help="Use smaller population/gens (faster)")
    p.add_argument("--hard",  action="store_true",     help="Use 16 courses (harder problem)")
    return p.parse_args()


def main():
    args   = parse_args()
    courses = COURSES_HARD if args.hard else COURSES_NORMAL
    halls   = HALLS

    pop_size    = 50  if args.fast else 150
    generations = 50  if args.fast else 300

    if args.seed is not None:
        random.seed(args.seed)
        print(f"  Seed: {args.seed}")

    mode = "HARD (16 courses)" if args.hard else "NORMAL (12 courses)"
    speed = "FAST" if args.fast else "FULL"
    print(f"\n{'='*60}")
    print(f"  Timetable Scheduler Demo  [{mode}] [{speed}]")
    print(f"  Courses: {len(courses)}  |  Halls: {len(halls)}  "
          f"|  Slots: {TOTAL_TIMESLOTS}")
    print(f"  Population: {pop_size}  |  Generations: {generations}")
    print(f"{'='*60}\n")

    # --- show what we're scheduling -----------------------------------------
    print("  COURSES TO SCHEDULE:")
    print(f"  {'Code':<10}  {'Title':<30}  {'Students':>8}  Lecturer")
    print("  " + "─"*65)
    for c in courses:
        print(f"  {c['code']:<10}  {c['name']:<30}  {c['students']:>8}  {c['lecturer']}")

    print(f"\n  AVAILABLE HALLS:")
    print(f"  {'Hall':<24}  Capacity")
    print("  " + "─"*35)
    for h in halls:
        print(f"  {h['name']:<24}  {h['capacity']}")
    print()

    # --- Step 1: Random population ------------------------------------------
    print("► Step 1: Generating random population …")
    pop = generate_random_population(pop_size, courses, halls)
    init_clashes = min(c.clashes for c in pop)
    print(f"  Best initial clashes: {init_clashes}\n")

    # --- Step 2: Genetic Algorithm ------------------------------------------
    print("► Step 2: Running Genetic Algorithm …")
    best_ga = genetic_algorithm(pop, generations=generations)
    print(f"  GA result — clashes: {best_ga.clashes}\n")

    # --- Step 3: Simulated Annealing (if needed) ----------------------------
    if best_ga.clashes > 0:
        print("► Step 3: Running Simulated Annealing to resolve remaining clashes …")
        final = simulated_annealing(best_ga)
    else:
        print("► Step 3: GA already found a perfect schedule — SA skipped.")
        final = best_ga

    # --- Print the timetable ------------------------------------------------
    print_timetable(final)


if __name__ == "__main__":
    main()