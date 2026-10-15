#!/usr/bin/env python3
"""
All report plots from the ChampSim output files in text-files-dir/.

Usage: put this file in the directory that contains text-files-dir/ and run
           python3 plot_all.py
       The plots are written to a new directory out/ next to this script.
File names expected:
  baseline_N  no prefetcher + LRU        base2_N  no prefetcher + SRRIP
  task1a_N    IP-stride + LRU            task1b_N SPP + LRU
  task2a_N    I-RRIP                     task2b_N Dynamic I-RRIP
  task3_N     SPP + prefetch-aware Dynamic I-RRIP
"""
import os, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "text-files-dir")
OUT = os.path.join(HERE, "out")
TRACES = [1, 2, 3]
os.makedirs(OUT, exist_ok=True)


def parse(path):
    t = open(path).read()
    g = lambda r, c=float: c(re.search(r, t).group(1))
    m = re.search(r"L1D USEFUL LOAD PREFETCHES:\s+(\d+)\s+PREFETCH ISSUED TO LOWER LEVEL:\s+(\d+)", t)
    return dict(
        ipc=g(r"CPU 0 cumulative IPC:\s+([\d.]+)"),
        l1d_miss=g(r"L1D LOAD\s+ACCESS:\s+\d+\s+HIT:\s+\d+\s+MISS:\s+(\d+)", int),
        l1d_mpki=g(r"L1D LOAD\s+ACCESS:.*MPKI:\s+([\d.]+)"),
        acc=100.0 * int(m.group(1)) / int(m.group(2)) if m and int(m.group(2)) else np.nan,
        l2_mpki=g(r"L2C LOAD\s+ACCESS:.*MPKI:\s+([\d.]+)"),
        l2i=g(r"L2C INSTRUCTION LOAD MPKI:\s+([\d.]+)"),
        l2d=g(r"L2C DATA LOAD MPKI:\s+([\d.]+)"),
    )


def load(prefix, n):
    return parse(os.path.join(SRC, f"{prefix}_{n}.txt"))


base = {n: load("baseline", n) for n in TRACES}


def derive(d, n):
    d["speedup"] = d["ipc"] / base[n]["ipc"]
    d["coverage"] = 100.0 * (base[n]["l1d_miss"] - d["l1d_miss"]) / base[n]["l1d_miss"]
    return d


def get(prefix):
    return {n: derive(load(prefix, n), n) for n in TRACES}


def bars(series, metric, ylabel, title, fname, hline=None):
    """series: list of (label, {trace: dict})"""
    x = np.arange(len(TRACES))
    w = 0.8 / len(series)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    allv = []
    for i, (label, data) in enumerate(series):
        v = [data[n][metric] for n in TRACES]
        allv += [a for a in v if not np.isnan(a)]
        ax.bar(x + (i - (len(series) - 1) / 2) * w, v, w, label=label, edgecolor="grey")
    if hline is not None:
        ax.axhline(hline, color="red", linestyle="--", linewidth=1, label="Baseline")
        allv.append(hline)
    lo, hi = min(allv), max(allv)
    pad = max((hi - lo) * 0.25, abs(hi) * 0.002)
    ax.set_ylim(max(lo - pad, 0), hi + pad)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Trace{n}" for n in TRACES])
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=200)
    plt.close(fig)
    print("wrote", fname)


def mpki_split(series, title, fname):
    """L2 instruction and data load MPKI side by side."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    x = np.arange(len(TRACES))
    w = 0.8 / len(series)
    for ax, metric, name in [(axes[0], "l2i", "L2 instruction load MPKI"), (axes[1], "l2d", "L2 data load MPKI")]:
        for i, (label, data) in enumerate(series):
            ax.bar(x + (i - (len(series) - 1) / 2) * w, [data[n][metric] for n in TRACES], w,
                   label=label, edgecolor="grey")
        ax.set_xticks(x)
        ax.set_xticklabels([f"Trace{n}" for n in TRACES])
        ax.set_ylabel(name)
    axes[0].legend()
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=200)
    plt.close(fig)
    print("wrote", fname)


lru = {n: derive(dict(base[n]), n) for n in TRACES}
srrip, ips, spp = get("base2"), get("task1a"), get("task1b")
irrip, dyn, t3 = get("task2a"), get("task2b"), get("task3")

# ---------------- Task 1B ----------------
bars([("IP-stride", ips), ("SPP", spp)], "speedup", "Speedup",
     "Speedup of L1D prefetchers over baseline (no prefetching)", "1B_speedup.png", hline=1.0)
bars([("Baseline", lru), ("IP-stride", ips), ("SPP", spp)], "l1d_mpki", "L1D load MPKI",
     "L1D load MPKI", "1B_mpki.png")
bars([("IP-stride", ips), ("SPP", spp)], "acc", "L1D prefetch accuracy (%)",
     "L1D prefetch accuracy", "1B_accuracy.png")
bars([("IP-stride", ips), ("SPP", spp)], "coverage", "L1D prefetch coverage (%)",
     "L1D prefetch coverage", "1B_coverage.png")

# ---------------- Task 2A ----------------
bars([("SRRIP", srrip), ("I-RRIP", irrip)], "speedup", "Speedup",
     "Speedup over LRU at the L2C", "2A_speedup.png", hline=1.0)
mpki_split([("LRU", lru), ("SRRIP", srrip), ("I-RRIP", irrip)],
           "L2 load MPKI by line type", "2A_mpki.png")

# ---------------- Task 2B ----------------
bars([("SRRIP", srrip), ("I-RRIP", irrip), ("Dynamic I-RRIP", dyn)], "speedup", "Speedup",
     "Speedup over LRU at the L2C", "2B_speedup.png", hline=1.0)
mpki_split([("SRRIP", srrip), ("I-RRIP", irrip), ("Dynamic I-RRIP", dyn)],
           "L2 load MPKI by line type", "2B_mpki.png")

# ---------------- Task 3 ----------------
bars([("SPP + LRU", spp), ("Dynamic I-RRIP", dyn), ("SPP + Task 3", t3)], "speedup", "Speedup",
     "Speedup over baseline (no prefetching, LRU)", "3_speedup.png", hline=1.0)
mpki_split([("SPP + LRU", spp), ("Dynamic I-RRIP", dyn), ("SPP + Task 3", t3)],
           "L2 load MPKI by line type", "3_mpki.png")
bars([("Baseline", lru), ("SPP + LRU", spp), ("Dynamic I-RRIP", dyn), ("SPP + Task 3", t3)],
     "l1d_mpki", "L1D load MPKI", "L1D load MPKI", "3_l1d_mpki.png")
bars([("SPP + LRU", spp), ("SPP + Task 3", t3)], "acc", "L1D prefetch accuracy (%)",
     "L1D prefetch accuracy", "3_accuracy.png")
bars([("SPP + LRU", spp), ("SPP + Task 3", t3)], "coverage", "L1D prefetch coverage (%)",
     "L1D prefetch coverage", "3_coverage.png")