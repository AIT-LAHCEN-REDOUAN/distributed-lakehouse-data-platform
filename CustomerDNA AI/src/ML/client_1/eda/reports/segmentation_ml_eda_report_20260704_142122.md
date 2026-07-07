# Segmentation ML EDA Report

- Training metrics source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\models\model_metadata\segmentation_kmeans_training_metrics_20260703_230056.json`
- Cluster assignments source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\reports\business_summaries\segmentation_cluster_assignments_20260703_230056.csv`
- Cluster summary source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\reports\business_summaries\segmentation_cluster_summary_20260703_230056.csv`
- Interpreted summary source: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\reports\business_summaries\segmentation_interpreted_cluster_summary_20260704_112344.csv`
- Rows in modeled dataset: `13013`
- Encoded feature count: `95`

## Selected Clustering Result

- Best `k`: `4`
- Silhouette score: `0.559636`
- Inertia: `212755.942886`
- Cluster sizes: `[2211, 4860, 1, 5941]`

## Candidate Cluster Results

- `k=2`: silhouette `0.502743`, inertia `461915.327`
- `k=3`: silhouette `0.558719`, inertia `247696.505`
- `k=4`: silhouette `0.559636`, inertia `212755.943`
- `k=5`: silhouette `0.448504`, inertia `190597.139`
- `k=6`: silhouette `0.419094`, inertia `172600.734`
- `k=7`: silhouette `0.333348`, inertia `158851.284`
- `k=8`: silhouette `0.327108`, inertia `147131.505`
- `k=9`: silhouette `0.362261`, inertia `136074.479`
- `k=10`: silhouette `0.290773`, inertia `129959.319`

## Business Cluster Summary

### High-Value Active Customers (Cluster 3)

- Customer count: `5941`
- Customer share: `45.65%`
- Avg distance to centroid: `2.7843`
- Dominant business segment: `VIP Active` (`40.85%`)
- Dominant value tier: `High Value` (`44.86%`)
- Dominant engagement tier: `Low Engagement` (`32.59%`)
- Recommended action: Prioritize premium retention, exclusivity campaigns, and high-touch relationship management.

### Dormant Low-Value Base (Cluster 1)

- Customer count: `4860`
- Customer share: `37.35%`
- Avg distance to centroid: `3.2656`
- Dominant business segment: `Dormant` (`84.22%`)
- Dominant value tier: `Unclassified` (`99.96%`)
- Dominant engagement tier: `Moderately Engaged` (`47.22%`)
- Recommended action: Use reactivation campaigns, low-friction offers, and simple reminder journeys.

### Core Customers Under Watch (Cluster 0)

- Customer count: `2211`
- Customer share: `16.99%`
- Avg distance to centroid: `5.5511`
- Dominant business segment: `Core Customer` (`32.75%`)
- Dominant value tier: `Mid Value` (`38.76%`)
- Dominant engagement tier: `Highly Engaged` (`61.83%`)
- Recommended action: Protect retention with loyalty messaging and moderate value reinforcement.

### Extreme Outlier Customer (Cluster 2)

- Customer count: `1`
- Customer share: `0.01%`
- Avg distance to centroid: `0.0000`
- Dominant business segment: `VIP Active` (`100.00%`)
- Dominant value tier: `High Value` (`100.00%`)
- Dominant engagement tier: `Highly Engaged` (`100.00%`)
- Recommended action: Review manually as a possible outlier before using it in standard campaign logic.

## Distance Ranking

- `Extreme Outlier Customer`: `0.0000`
- `High-Value Active Customers`: `2.7843`
- `Dormant Low-Value Base`: `3.2656`
- `Core Customers Under Watch`: `5.5511`

## Main Findings

- The selected solution uses `k=4` with silhouette `0.559636`, which is the strongest score in the tested range.
- The largest cluster is 'High-Value Active Customers', while the smallest is 'Extreme Outlier Customer'.
- The most compact cluster by average centroid distance is 'Extreme Outlier Customer', while 'Core Customers Under Watch' is the most dispersed.
- 'Extreme Outlier Customer' behaves like an outlier cluster because it contains only 1 customer.

## Generated Plots

- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\segmentation\segmentation_silhouette_by_k_20260704_142122.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\segmentation\segmentation_inertia_by_k_20260704_142122.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\segmentation\segmentation_cluster_sizes_20260704_142122.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\segmentation\segmentation_cluster_distances_20260704_142122.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\segmentation\segmentation_dominant_segments_20260704_142122.png`
- `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\eda\plots\segmentation\segmentation_average_distance_20260704_142122.png`
