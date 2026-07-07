from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from eda_common import (  # noqa: E402
    MODEL_METADATA_DIR,
    apply_plot_style,
    ensure_use_case_directories,
    find_latest_file,
    read_json,
    save_figure,
    utc_slug,
    write_text,
)


USE_CASE = "segmentation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ML EDA plots and a markdown summary for the segmentation model.",
    )
    parser.add_argument(
        "--training-metrics-path",
        default=None,
        help="Optional explicit segmentation training metrics JSON path.",
    )
    parser.add_argument(
        "--interpretation-metadata-path",
        default=None,
        help="Optional explicit segmentation interpretation metadata JSON path.",
    )
    return parser.parse_args()


def find_latest_training_metrics() -> Path:
    return find_latest_file(
        MODEL_METADATA_DIR,
        "segmentation_kmeans_training_metrics_*.json",
    )


def find_latest_interpretation_metadata() -> Path:
    return find_latest_file(
        MODEL_METADATA_DIR,
        "segmentation_cluster_interpretation_*.json",
    )


def plot_silhouette_by_k(candidate_df: pd.DataFrame, output_path: Path) -> int:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        candidate_df["k"],
        candidate_df["silhouette_score"],
        marker="o",
        linewidth=2,
        color="#4C78A8",
    )
    best_row = candidate_df.loc[candidate_df["silhouette_score"].idxmax()]
    ax.scatter(best_row["k"], best_row["silhouette_score"], s=120, color="#E45756", zorder=5)
    ax.annotate(
        f"Best k = {int(best_row['k'])}\nSilhouette = {best_row['silhouette_score']:.3f}",
        xy=(best_row["k"], best_row["silhouette_score"]),
        xytext=(10, 10),
        textcoords="offset points",
    )
    ax.set_title("Silhouette Score by Cluster Count")
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Silhouette Score")
    ax.set_xticks(candidate_df["k"].tolist())
    save_figure(fig, output_path)
    return int(best_row["k"])


def plot_inertia_by_k(candidate_df: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        candidate_df["k"],
        candidate_df["inertia"],
        marker="o",
        linewidth=2,
        color="#F58518",
    )
    ax.set_title("Inertia by Cluster Count")
    ax.set_xlabel("Number of Clusters (k)")
    ax.set_ylabel("Inertia")
    ax.set_xticks(candidate_df["k"].tolist())
    save_figure(fig, output_path)


def plot_cluster_size_distribution(summary_df: pd.DataFrame, output_path: Path) -> tuple[str, str]:
    plot_df = summary_df.copy().sort_values("customer_count", ascending=False)
    labels = [
        f"{row['cluster_name']}\n(ID {int(row['cluster_id'])})"
        for _, row in plot_df.iterrows()
    ]
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(labels, plot_df["customer_count"], color="#54A24B")
    ax.set_title("Cluster Size Distribution")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Customer Count")
    ax.tick_params(axis="x", rotation=18)
    for bar, share in zip(bars, plot_df["customer_share"].tolist()):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{int(bar.get_height()):,}\n{share:.2%}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    save_figure(fig, output_path)
    largest = str(plot_df.iloc[0]["cluster_name"])
    smallest = str(plot_df.iloc[-1]["cluster_name"])
    return largest, smallest


def plot_distance_distribution(assignments_df: pd.DataFrame, output_path: Path) -> dict[str, float]:
    plot_df = assignments_df.copy()
    cluster_order = (
        plot_df.groupby("cluster_name", dropna=False)["distance_to_assigned_centroid"]
        .mean()
        .sort_values()
        .index
        .tolist()
    )
    grouped_values = [
        plot_df.loc[plot_df["cluster_name"] == cluster_name, "distance_to_assigned_centroid"].tolist()
        for cluster_name in cluster_order
    ]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.boxplot(grouped_values, labels=cluster_order, patch_artist=True)
    ax.set_title("Distance to Assigned Centroid by Cluster")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Distance to Centroid")
    ax.tick_params(axis="x", rotation=18)
    save_figure(fig, output_path)

    return (
        plot_df.groupby("cluster_name", dropna=False)["distance_to_assigned_centroid"]
        .mean()
        .sort_values()
        .to_dict()
    )


def plot_dominant_business_segment(summary_df: pd.DataFrame, output_path: Path) -> None:
    plot_df = summary_df.copy().sort_values("customer_count", ascending=False)
    labels = [
        f"{row['cluster_name']}\n({row['reference_final_customer_segment_dominant_value']})"
        for _, row in plot_df.iterrows()
    ]
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(
        labels,
        plot_df["reference_final_customer_segment_dominant_share"],
        color="#7A5195",
    )
    ax.set_title("Dominant Business Segment Share by Cluster")
    ax.set_xlabel("Cluster / Dominant Segment")
    ax.set_ylabel("Dominant Segment Share")
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="x", rotation=18)
    for bar, value in zip(bars, plot_df["reference_final_customer_segment_dominant_share"].tolist()):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.2%}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    save_figure(fig, output_path)


def plot_cluster_average_distance(summary_df: pd.DataFrame, output_path: Path) -> tuple[str, str]:
    plot_df = summary_df.copy().sort_values("avg_distance_to_centroid")
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(plot_df["cluster_name"], plot_df["avg_distance_to_centroid"], color="#E45756")
    ax.set_title("Average Distance to Centroid by Cluster")
    ax.set_xlabel("Cluster")
    ax.set_ylabel("Average Distance")
    ax.tick_params(axis="x", rotation=18)
    for bar, value in zip(bars, plot_df["avg_distance_to_centroid"].tolist()):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    save_figure(fig, output_path)
    most_compact = str(plot_df.iloc[0]["cluster_name"])
    least_compact = str(plot_df.iloc[-1]["cluster_name"])
    return most_compact, least_compact


def build_markdown_report(
    *,
    metrics_payload: dict,
    interpretation_payload: dict,
    summary_df: pd.DataFrame,
    output_paths: dict[str, Path],
    best_k: int,
    largest_cluster: str,
    smallest_cluster: str,
    most_compact_cluster: str,
    least_compact_cluster: str,
    mean_distance_map: dict[str, float],
) -> str:
    selected_model = metrics_payload["selected_model"]
    candidate_df = pd.DataFrame(metrics_payload["candidate_results"]).sort_values("k")
    candidate_lines = []
    for _, row in candidate_df.iterrows():
        candidate_lines.append(
            f"- `k={int(row['k'])}`: silhouette `{row['silhouette_score']:.6f}`, inertia `{row['inertia']:.3f}`"
        )

    outlier_rows = summary_df.loc[summary_df["customer_count"] <= 1]
    observations: list[str] = []
    observations.append(
        f"The selected solution uses `k={best_k}` with silhouette `{selected_model['silhouette_score']:.6f}`, which is the strongest score in the tested range."
    )
    observations.append(
        f"The largest cluster is '{largest_cluster}', while the smallest is '{smallest_cluster}'."
    )
    observations.append(
        f"The most compact cluster by average centroid distance is '{most_compact_cluster}', while '{least_compact_cluster}' is the most dispersed."
    )
    if not outlier_rows.empty:
        outlier_name = str(outlier_rows.iloc[0]["cluster_name"])
        observations.append(
            f"'{outlier_name}' behaves like an outlier cluster because it contains only {int(outlier_rows.iloc[0]['customer_count'])} customer."
        )

    lines = [
        "# Segmentation ML EDA Report",
        "",
        f"- Training metrics source: `{metrics_payload['artifacts']['metrics_path']}`",
        f"- Cluster assignments source: `{metrics_payload['artifacts']['assignments_path']}`",
        f"- Cluster summary source: `{metrics_payload['artifacts']['summary_path']}`",
        f"- Interpreted summary source: `{interpretation_payload['artifacts']['interpreted_summary_path']}`",
        f"- Rows in modeled dataset: `{metrics_payload['row_count']}`",
        f"- Encoded feature count: `{metrics_payload['feature_count']}`",
        "",
        "## Selected Clustering Result",
        "",
        f"- Best `k`: `{selected_model['best_k']}`",
        f"- Silhouette score: `{selected_model['silhouette_score']:.6f}`",
        f"- Inertia: `{selected_model['inertia']:.6f}`",
        f"- Cluster sizes: `{selected_model['cluster_sizes']}`",
        "",
        "## Candidate Cluster Results",
        "",
    ]
    lines.extend(candidate_lines)
    lines.extend(
        [
            "",
            "## Business Cluster Summary",
            "",
        ]
    )

    for _, row in summary_df.sort_values("customer_count", ascending=False).iterrows():
        lines.extend(
            [
                f"### {row['cluster_name']} (Cluster {int(row['cluster_id'])})",
                "",
                f"- Customer count: `{int(row['customer_count'])}`",
                f"- Customer share: `{float(row['customer_share']):.2%}`",
                f"- Avg distance to centroid: `{float(row['avg_distance_to_centroid']):.4f}`",
                f"- Dominant business segment: `{row['reference_final_customer_segment_dominant_value']}` (`{float(row['reference_final_customer_segment_dominant_share']):.2%}`)",
                f"- Dominant value tier: `{row['reference_customer_value_tier_dominant_value']}` (`{float(row['reference_customer_value_tier_dominant_share']):.2%}`)",
                f"- Dominant engagement tier: `{row['reference_engagement_tier_dominant_value']}` (`{float(row['reference_engagement_tier_dominant_share']):.2%}`)",
                f"- Recommended action: {row['recommended_action']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Distance Ranking",
            "",
        ]
    )
    lines.extend(
        [
            f"- `{cluster_name}`: `{mean_distance:.4f}`"
            for cluster_name, mean_distance in mean_distance_map.items()
        ]
    )
    lines.extend(
        [
            "",
            "## Main Findings",
            "",
        ]
    )
    lines.extend([f"- {observation}" for observation in observations])
    lines.extend(
        [
            "",
            "## Generated Plots",
            "",
        ]
    )
    lines.extend([f"- `{path}`" for path in output_paths.values()])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    apply_plot_style()
    directories = ensure_use_case_directories(USE_CASE)
    slug = utc_slug()

    metrics_path = Path(args.training_metrics_path) if args.training_metrics_path else find_latest_training_metrics()
    interpretation_path = (
        Path(args.interpretation_metadata_path)
        if args.interpretation_metadata_path
        else find_latest_interpretation_metadata()
    )

    metrics_payload = read_json(metrics_path)
    interpretation_payload = read_json(interpretation_path)

    summary_path = Path(interpretation_payload["artifacts"]["interpreted_summary_path"])
    assignments_path = Path(interpretation_payload["artifacts"]["interpreted_assignments_path"])
    if not summary_path.exists():
        raise FileNotFoundError(f"Interpreted segmentation summary file not found: {summary_path}")
    if not assignments_path.exists():
        raise FileNotFoundError(f"Interpreted segmentation assignments file not found: {assignments_path}")

    summary_df = pd.read_csv(summary_path, low_memory=False)
    assignments_df = pd.read_csv(assignments_path, low_memory=False)

    required_summary_columns = {
        "cluster_id",
        "cluster_name",
        "customer_count",
        "customer_share",
        "avg_distance_to_centroid",
        "reference_final_customer_segment_dominant_value",
        "reference_final_customer_segment_dominant_share",
        "reference_customer_value_tier_dominant_value",
        "reference_customer_value_tier_dominant_share",
        "reference_engagement_tier_dominant_value",
        "reference_engagement_tier_dominant_share",
        "recommended_action",
    }
    missing_summary_columns = required_summary_columns.difference(summary_df.columns)
    if missing_summary_columns:
        raise ValueError(
            "Missing expected segmentation summary columns: " + ", ".join(sorted(missing_summary_columns))
        )

    required_assignment_columns = {
        "cluster_name",
        "distance_to_assigned_centroid",
    }
    missing_assignment_columns = required_assignment_columns.difference(assignments_df.columns)
    if missing_assignment_columns:
        raise ValueError(
            "Missing expected segmentation assignment columns: " + ", ".join(sorted(missing_assignment_columns))
        )

    candidate_df = pd.DataFrame(metrics_payload["candidate_results"]).sort_values("k")
    output_paths = {
        "silhouette_by_k": directories["plot_dir"] / f"segmentation_silhouette_by_k_{slug}.png",
        "inertia_by_k": directories["plot_dir"] / f"segmentation_inertia_by_k_{slug}.png",
        "cluster_sizes": directories["plot_dir"] / f"segmentation_cluster_sizes_{slug}.png",
        "cluster_distances": directories["plot_dir"] / f"segmentation_cluster_distances_{slug}.png",
        "dominant_segments": directories["plot_dir"] / f"segmentation_dominant_segments_{slug}.png",
        "average_distance": directories["plot_dir"] / f"segmentation_average_distance_{slug}.png",
    }

    best_k = plot_silhouette_by_k(candidate_df, output_paths["silhouette_by_k"])
    plot_inertia_by_k(candidate_df, output_paths["inertia_by_k"])
    largest_cluster, smallest_cluster = plot_cluster_size_distribution(summary_df, output_paths["cluster_sizes"])
    mean_distance_map = plot_distance_distribution(assignments_df, output_paths["cluster_distances"])
    plot_dominant_business_segment(summary_df, output_paths["dominant_segments"])
    most_compact_cluster, least_compact_cluster = plot_cluster_average_distance(
        summary_df,
        output_paths["average_distance"],
    )

    report_text = build_markdown_report(
        metrics_payload=metrics_payload,
        interpretation_payload=interpretation_payload,
        summary_df=summary_df,
        output_paths=output_paths,
        best_k=best_k,
        largest_cluster=largest_cluster,
        smallest_cluster=smallest_cluster,
        most_compact_cluster=most_compact_cluster,
        least_compact_cluster=least_compact_cluster,
        mean_distance_map=mean_distance_map,
    )
    report_path = directories["report_dir"] / f"segmentation_ml_eda_report_{slug}.md"
    write_text(report_path, report_text)

    print("=" * 80)
    print("CUSTOMERDNA AI - SEGMENTATION ML EDA")
    print("=" * 80)
    print(f"Training metrics: {metrics_path}")
    print(f"Interpretation metadata: {interpretation_path}")
    print(f"Interpreted summary: {summary_path}")
    print(f"Interpreted assignments: {assignments_path}")
    print(f"Report: {report_path}")
    for label, path in output_paths.items():
        print(f"{label}: {path}")
    print("Segmentation ML EDA completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
