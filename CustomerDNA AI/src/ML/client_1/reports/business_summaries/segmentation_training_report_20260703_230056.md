# Segmentation Clustering Training Report

- Created at: `2026-07-03T23:00:56.111160+00:00`
- Use case: `segmentation`
- Processed matrix path: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\datasets\processed\segmentation_feature_base_processed_20260703_225332.csv`
- Row count: `13013`
- Feature count: `95`

## Selected Model

- Best cluster count: `4`
- Silhouette score: `0.559636`
- Inertia: `212755.942886`
- Random state: `42`
- n_init: `20`

## Candidate Results

| k | Silhouette | Inertia | Cluster Sizes |
|---|---:|---:|---|
| 2 | 0.502743 | 461915.327346 | 10802, 2211 |
| 3 | 0.558719 | 247696.505030 | 4860, 5942, 2211 |
| 4 | 0.559636 | 212755.942886 | 2211, 4860, 1, 5941 |
| 5 | 0.448504 | 190597.139049 | 4859, 4101, 2211, 1841, 1 |
| 6 | 0.419094 | 172600.734343 | 4859, 4095, 578, 1633, 1847, 1 |
| 7 | 0.333348 | 158851.283577 | 1355, 4095, 578, 1847, 3504, 1, 1633 |
| 8 | 0.327108 | 147131.504646 | 4096, 903, 3504, 464, 1, 1846, 844, 1355 |
| 9 | 0.362261 | 136074.478798 | 4094, 4032, 843, 903, 1, 1798, 112, 765, 465 |
| 10 | 0.290773 | 129959.319332 | 903, 2142, 3504, 464, 1355, 1, 816, 844, 110, 2874 |
