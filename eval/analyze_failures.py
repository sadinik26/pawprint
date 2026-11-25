
import pandas as pd
from pathlib import Path

# ==========================================
# File paths
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = PROJECT_ROOT / "eval" / "dinov2_baseline_results.csv"

OUTPUT_PATH = PROJECT_ROOT / "eval" / "dinov2_failure_analysis.csv"


# ==========================================
# Load evaluation results
# ==========================================

results = pd.read_csv(INPUT_PATH)

print("=" * 60)
print("DINOV2 FAILURE ANALYSIS")
print("=" * 60)

total_queries = len(results)

# ==========================================
# Identify failure categories
# ==========================================

top1_failures = results[
    results["top1_correct"] == False
].copy()

top5_failures = results[
    results["top5_correct"] == False
].copy()

top1_wrong_but_top5_correct = results[
    (results["top1_correct"] == False)
    & (results["top5_correct"] == True)
].copy()


# ==========================================
# Calculate failure statistics
# ==========================================

top1_failure_count = len(top1_failures)
top5_failure_count = len(top5_failures)

top1_failure_rate = (
    top1_failure_count / total_queries
) * 100

top5_failure_rate = (
    top5_failure_count / total_queries
) * 100


# ==========================================
# Display failure summary
# ==========================================

print("\n1. FAILURE SUMMARY")
print("-" * 60)

print("Total evaluated queries:", total_queries)

print(
    "Top-1 failures:",
    top1_failure_count,
    f"({top1_failure_rate:.2f}%)"
)

print(
    "Top-5 failures:",
    top5_failure_count,
    f"({top5_failure_rate:.2f}%)"
)

print(
    "Top-1 wrong but correct identity in Top-5:",
    len(top1_wrong_but_top5_correct)
)


# ==========================================
# Analyze incorrect Top-1 matches
# ==========================================

print("\n2. TOP-1 FAILURE SIMILARITY ANALYSIS")
print("-" * 60)

if not top1_failures.empty:

    print(
        "Average incorrect Top-1 similarity:",
        round(top1_failures["top1_similarity"].mean(), 4)
    )

    print(
        "Highest incorrect Top-1 similarity:",
        round(top1_failures["top1_similarity"].max(), 4)
    )

    print(
        "Lowest incorrect Top-1 similarity:",
        round(top1_failures["top1_similarity"].min(), 4)
    )

    print("\nTop 10 incorrect matches:")

    print(
        top1_failures.sort_values(
            by="top1_similarity",
            ascending=False
        )[
            [
                "query_dog_id",
                "top1_retrieved_dog_id",
                "top1_similarity",
                "top5_correct"
            ]
        ].head(10).to_string(index=False)
    )


# ==========================================
# Most frequently confused identities
# ==========================================

print("\n3. MOST FREQUENTLY CONFUSED IDENTITIES")
print("-" * 60)

if not top1_failures.empty:

    confusion = (
        top1_failures.groupby(
            ["query_dog_id", "top1_retrieved_dog_id"]
        )
        .size()
        .reset_index(name="failure_count")
        .sort_values(
            by="failure_count",
            ascending=False
        )
    )

    print(confusion.head(10).to_string(index=False))


# ==========================================
# Save failure records
# ==========================================

top1_failures.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\n4. OUTPUT")
print("-" * 60)

print("Failure records saved to:")
print(OUTPUT_PATH)

print("\nFailure analysis completed!")
