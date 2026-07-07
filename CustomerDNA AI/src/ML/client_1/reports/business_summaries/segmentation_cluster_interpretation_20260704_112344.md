# Segmentation Cluster Interpretation

- Created at: `2026-07-04T11:23:44.347572+00:00`
- Use case: `segmentation`
- Source training metrics: `D:\github\Master_PFE_Project\CustomerDNA AI\src\ML\client_1\models\model_metadata\segmentation_kmeans_training_metrics_20260703_230056.json`
- Best cluster count: `4`
- Silhouette score: `0.559636`

## Business Segments

### Cluster 0 - Core Customers Under Watch

- Customer count: `2211`
- Customer share: `16.99%`
- Description: This segment represents 16.99% of the customer base (2211 customers). It is most strongly associated with the business segment 'Core Customer' (32.75% dominance), value tier 'Mid Value' (38.76%), and engagement tier 'Highly Engaged' (61.83%). Typical customers in this cluster are closest to the 'No Valid Orders' purchase pattern and the 'Unknown Geography' geography profile.
- Recommended action: Protect retention with loyalty messaging and moderate value reinforcement.

### Cluster 1 - Dormant Low-Value Base

- Customer count: `4860`
- Customer share: `37.35%`
- Description: This segment represents 37.35% of the customer base (4860 customers). It is most strongly associated with the business segment 'Dormant' (84.22% dominance), value tier 'Unclassified' (99.96%), and engagement tier 'Moderately Engaged' (47.22%). Typical customers in this cluster are closest to the 'No Valid Orders' purchase pattern and the 'Unknown Geography' geography profile.
- Recommended action: Use reactivation campaigns, low-friction offers, and simple reminder journeys.

### Cluster 2 - Extreme Outlier Customer

- Customer count: `1`
- Customer share: `0.01%`
- Description: This cluster contains a single customer and should be treated as an outlier or edge-case profile rather than a stable business segment.
- Recommended action: Review manually as a possible outlier before using it in standard campaign logic.

### Cluster 3 - High-Value Active Customers

- Customer count: `5941`
- Customer share: `45.65%`
- Description: This segment represents 45.65% of the customer base (5941 customers). It is most strongly associated with the business segment 'VIP Active' (40.85% dominance), value tier 'High Value' (44.86%), and engagement tier 'Low Engagement' (32.59%). Typical customers in this cluster are closest to the 'New Buyer' purchase pattern and the 'Single-Country Shopper' geography profile.
- Recommended action: Prioritize premium retention, exclusivity campaigns, and high-touch relationship management.
