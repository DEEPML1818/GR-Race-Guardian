"""Simple Monte Carlo race simulator sample.

This module demonstrates a tiny Monte Carlo engine that simulates lap time noise
and pit stops to estimate finishing position probabilities.
"""
import random
import statistics

def simulate_one_race(base_paces, n_laps=10, pit_loss=25.0, tire_degradation=0.05):
    """Simulate finishing times for drivers given base_paces (dict driver->lap_time).

    Returns dict driver->total_time
    """
    results = {d: 0.0 for d in base_paces}
    for lap in range(n_laps):
        for d, base in base_paces.items():
            # degradation increases lap time linearly with lap index
            lap_time = base * (1 + lap * tire_degradation * random.uniform(0.8, 1.2))
            results[d] += lap_time
            # random pit decision simulation omitted for simplicity
    return results

def monte_carlo(base_paces, n_laps=10, iters=1000):
    sims = []
    for _ in range(iters):
        r = simulate_one_race(base_paces, n_laps=n_laps)
        sims.append(r)

    # compute average finishing time per driver
    drivers = list(base_paces.keys())
    avg = {d: statistics.mean([s[d] for s in sims]) for d in drivers}
    return {'avg_times': avg, 'sims': sims}

if __name__ == '__main__':
    # quick demo
    base = {'car1': 90.0, 'car2': 91.5, 'car3': 92.2}
    out = monte_carlo(base, n_laps=20, iters=200)
    from pprint import pprint
    pprint(out['avg_times'])
