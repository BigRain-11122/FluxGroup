#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["mesa>=3.0", "networkx>=3.0"]
# ///
"""mesa_census_demo.py - sandbox population-projection demo on the real census.

Adoption: Mesa (Apache-2.0, LICENSE verified) -> R-20260929-gov-2 immediate
wiring ticket. Consumer: BigLife/city-lab 10k census registry (birth/death/
migration projection engine, pure local, zero LLM).

Sandbox law: read-only on the real census export; results NEVER write back to
census (04:37 stop-order respected). Honored seats / handwritten anchors are
exempt from dynamics (real-person source, no narrative simulation).

Census raw fields (per 40-line probe): age = numeric years (None for honored/
anchors/narrative-age residents), district = code tokens (GM/MD/QT/NS/...),
species = carbon/silicon/sprite/...

Usage:
  uv run --python 3.12 Tools/mesa_census_demo.py [--years 10] [--seed 7]
      [--census PATH] [--synthetic N] [--out PATH]
Rates below are PLACEHOLDER demo parameters (engine proof, NOT calibrated
demography). Keep them explicit and tunable at the top.
"""
import argparse
import json
import random
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# --- demo parameters (placeholders, tune per city-lab calibration) ----------
SENIOR_MORTALITY = 0.040      # per-year death prob at age >= 60
BASE_MORTALITY = 0.001        # per-year death prob below 60
BIRTH_PER_1000_ADULTS = 12.0  # per-year births per 1000 adults (18-59)
MIGRATION_RATE = 0.015        # per-year district-move prob
ADULT_BIRTH_RANGE = (18, 59)  # ages that produce births
BANDS = {"junior": (0, 17), "young": (18, 39), "mid": (40, 59), "senior": (60, 200)}
EXEMPT_FACTIONS = {"honored"}  # honored seats + anchors exempt from dynamics
DEFAULT_AGE = 45              # for age=None non-exempt (narrative-age) residents


def band_of(age):
    for name, (lo, hi) in BANDS.items():
        if lo <= age <= hi:
            return name
    return "mid"


def load_census(path):
    people, exempt = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            is_exempt = (d.get("faction") in EXEMPT_FACTIONS or d.get("anchor")
                         or d.get("id", "").startswith("C-A"))
            age = d.get("age")
            rec = {
                "id": d.get("id", "?"),
                "age": int(age) if isinstance(age, (int, float)) else DEFAULT_AGE,
                "district": d.get("district") or "?",
                "species": d.get("species", "?"),
            }
            (exempt if is_exempt else people).append(rec)
    return people, exempt


def synthetic(n, seed):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        out.append({"id": "S-%05d" % i, "age": rng.randint(1, 90),
                    "district": rng.choice(["GM", "MD", "QT", "NS", "GB", "JB"]),
                    "species": "carbon"})
    return out, []


def run(people, years, seed):
    import mesa

    class Citizen(mesa.Agent):
        def __init__(self, model, rec):
            super().__init__(model)
            self.rec = rec

    class Population(mesa.Model):
        def __init__(self, pop):
            super().__init__()
            self.yearly = []
            self.births = self.deaths = self.moves = 0
            self.rng = random.Random(seed)
            for rec in pop:
                Citizen(self, rec)

        def step(self):
            districts = sorted({a.rec["district"] for a in self.agents} - {"?"})
            adults = [a for a in self.agents
                      if ADULT_BIRTH_RANGE[0] <= a.rec["age"] <= ADULT_BIRTH_RANGE[1]]
            died = []
            for a in list(self.agents):
                r = a.rec
                r["age"] += 1
                p_death = SENIOR_MORTALITY if r["age"] >= BANDS["senior"][0] else BASE_MORTALITY
                if self.rng.random() < p_death:
                    died.append(a)
                    continue
                if self.rng.random() < MIGRATION_RATE:
                    r["district"] = self.rng.choice(
                        [d for d in districts if d != r["district"]] or districts)
                    self.moves += 1
            n_births = int(len(adults) * BIRTH_PER_1000_ADULTS / 1000)
            for i in range(n_births):
                Citizen(self, {"id": "B%06d-%d" % (len(self.agents), i), "age": 0,
                               "district": self.rng.choice(districts),
                               "species": "carbon"})
                self.births += 1
            for a in died:
                self.agents.remove(a)
                self.deaths += 1
            self.yearly.append({
                "total": len(self.agents),
                "by_band": {b: sum(1 for x in self.agents if band_of(x.rec["age"]) == b)
                            for b in BANDS},
            })

    model = Population([dict(p) for p in people])
    for _ in range(years):
        model.step()
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=10)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--census", default="life/BigLife/census/export/citizens-light.jsonl")
    ap.add_argument("--synthetic", type=int, default=0)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    if a.synthetic:
        people, exempt = synthetic(a.synthetic, a.seed)
    else:
        people, exempt = load_census(a.census)
    if not people:
        print("ERR empty population", file=sys.stderr)
        return 1
    m = run(people, a.years, a.seed)
    by_dist, by_spec = {}, {}
    for x in m.agents:
        by_dist[x.rec["district"]] = by_dist.get(x.rec["district"], 0) + 1
        by_spec[x.rec["species"]] = by_spec.get(x.rec["species"], 0) + 1
    result = {
        "engine": "mesa", "input_population": len(people),
        "exempt_honored_anchors": len(exempt), "years": a.years, "seed": a.seed,
        "params": {"senior_mortality": SENIOR_MORTALITY,
                   "base_mortality": BASE_MORTALITY,
                   "birth_per_1000_adults": BIRTH_PER_1000_ADULTS,
                   "migration_rate": MIGRATION_RATE},
        "final_total": len(m.agents), "births": m.births, "deaths": m.deaths,
        "moves": m.moves, "final_by_band": m.yearly[-1]["by_band"],
        "final_by_district": dict(sorted(by_dist.items())),
        "final_by_species": dict(sorted(by_spec.items())),
        "yearly_totals": [y["total"] for y in m.yearly],
    }
    print(json.dumps(result, ensure_ascii=False, indent=1))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
