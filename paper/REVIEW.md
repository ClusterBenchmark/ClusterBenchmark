# Remaining Review Action Items — `manuscript_natcomm.tex`

**Target Venue:** *Nature Communications*  
**Last Updated:** 2026-11-23  
*(All completed non-compute fixes—M1 matched-$k$ Protocol S rerun & per-epoch speedups, M2 best-by-$Q$ aggregation + variance reporting, M3 ARI replacing edge-restricted Pairwise F1, `DMoN`/`UCoDe` added to Table 2, `VieClus` timing rule, exact 6-decimal DIMACS optima counts, GNNS DIMACS count, ADC-SBM binned-number alignment, BibTeX/ISSN/dataset citations, Table 1/2/10–15 fixes, and Figure 1–4 polish—have been applied and removed from this list.)*

---

## 1. Compute-Dependent Items (In Progress / Queued)

### M4.1. `Bayan` with Unrestricted Academic Gurobi License — *Queued Next*
- [ ] Re-run `Bayan` on DIMACS (`celegansneural`, `celegans-metabolic`, `netscience`, `jazz`, etc.) using an unrestricted Academic Gurobi license (eliminating the `ERR` license-size failures).
- [ ] Re-run `python3 paper/scripts/process_results.py`, update Tables~13–14, Figure~2 (right), and Section~2.2 accordingly.

### M5. Feature-Only & Synthetic Statistical Rigor (Recommended before Submission)
- [ ] Add a **feature-only $k$-means** baseline on ADC-SBM (Figure~5) and `Ground-Truth` (NMI/ARI) so readers can separate genuine graph+attribute fusion from pure attribute clustering.
- [ ] Discuss (or include) attributed classical baselines (e.g., `I-Louvain`, `EVA`, or `Leiden` on graph + kNN feature edges).
- [ ] Re-run ADC-SBM with 5–10 independent graph seeds per parameter point and add shaded $\pm 1\text{ SD}$ uncertainty bands to Figure~5.

### M4.4. Optional Fairness / Compute-Budget Polish
- [ ] Consider a brief time-matched multi-start `Leiden` sanity check (e.g., 10 s / 60 s vs. `VieClus`) or explicitly note `Leiden`'s default 2-iteration budget in Discussion.
- [ ] Clarify in Figure~4 (right) / text that "single-threaded classical solvers" reflects the evaluated wrappers (`igraph`, etc.), while parallel classical implementations (`NetworKit`, `GVE-Leiden`, `cuGraph`, OpenMP `Infomap`, multi-threaded `Gurobi`) exist.

---

## 2. Final Polish & Submission Checklist

- [ ] Remove the main-text footnote on Page 2 (inline the companion website URL or keep it in Data/Code Availability).
- [ ] Move Appendices A–D into a separate **Supplementary Information** file (`Supplementary Tables 1–10`) rather than `\appendix` after References (if required at submission).
- [ ] Split `Data and Code Availability` into dedicated `Data Availability` and `Code Availability` sections and mint a persistent archival DOI (e.g., Zenodo) once all final numbers are stable.
