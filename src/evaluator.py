"""
LLM Regression Detection System
Phase 3: Evaluation Engine
Phase 3B: Evaluation History
Phase 3C: Versioned Evaluations

Usage:

    python -m src.evaluator v1
    python -m src.evaluator v2

Examples:

    v1 -> prompts/v1.yaml -> reports/evaluation_v1.json
    v2 -> prompts/v2.yaml -> reports/evaluation_v2.json
"""

import json
import sys
import time
from pathlib import Path

import yaml

from src.classifier import classify_email
from src.history import save_evaluation_run


# ============================================================
# Project Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GOLDEN_DATASET_PATH = (
    PROJECT_ROOT / "data" / "golden_dataset.json"
)

PROMPTS_DIR = PROJECT_ROOT / "prompts"

REPORTS_DIR = PROJECT_ROOT / "reports"


# ============================================================
# Load Golden Dataset
# ============================================================

def load_golden_dataset():
    """
    Load our trusted test cases.
    """

    with open(
        GOLDEN_DATASET_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# Load Prompt Version
# ============================================================

def load_prompt_config(prompt_version):
    """
    Load a specific prompt version.

    Example:

        v1 -> prompts/v1.yaml
        v2 -> prompts/v2.yaml
    """

    prompt_path = (
        PROMPTS_DIR / f"{prompt_version}.yaml"
    )

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_path}"
        )

    with open(
        prompt_path,
        "r",
        encoding="utf-8"
    ) as file:

        return yaml.safe_load(file)


# ============================================================
# Summary Evaluation
# ============================================================

def calculate_summary_score(
    expected_summary,
    predicted_summary
):
    """
    Simple word-overlap scoring system.

    Score:
        5 = excellent
        4 = good
        3 = acceptable
        2 = weak
        1 = poor
    """

    expected_words = set(
        expected_summary.lower().split()
    )

    predicted_words = set(
        predicted_summary.lower().split()
    )

    if not expected_words:
        return 1

    common_words = expected_words.intersection(
        predicted_words
    )

    similarity = (
        len(common_words)
        / len(expected_words)
    )

    if similarity >= 0.80:
        return 5

    elif similarity >= 0.60:
        return 4

    elif similarity >= 0.40:
        return 3

    elif similarity >= 0.20:
        return 2

    else:
        return 1


# ============================================================
# Evaluate One Test Case
# ============================================================

def evaluate_test_case(
    test_case,
    prompt_config
):
    """
    Run one golden test case through the LLM.
    """

    start_time = time.perf_counter()

    prediction = classify_email(
        test_case["email"],
        prompt_config
    )

    end_time = time.perf_counter()

    latency_ms = round(
        (end_time - start_time) * 1000,
        2
    )

    expected_category = (
        test_case["expected_category"]
    )

    predicted_category = prediction.category

    category_correct = (
        predicted_category.lower().strip()
        ==
        expected_category.lower().strip()
    )

    summary_score = calculate_summary_score(
        test_case["expected_summary"],
        prediction.summary
    )

    return {
        "test_id": test_case["id"],
        "difficulty": test_case["difficulty"],
        "email": test_case["email"],

        "expected_category":
            expected_category,

        "predicted_category":
            predicted_category,

        "category_correct":
            category_correct,

        "expected_summary":
            test_case["expected_summary"],

        "predicted_summary":
            prediction.summary,

        "summary_score":
            summary_score,

        "latency_ms":
            latency_ms,

        # We can add real token tracking later.
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None
    }


# ============================================================
# Run Full Evaluation
# ============================================================

def run_evaluation(prompt_version):
    """
    Evaluate one prompt version against
    the complete golden dataset.
    """

    print("\n========================================")
    print("      LLM REGRESSION EVALUATION")
    print("========================================")

    print(
        f"\nPrompt version: {prompt_version}\n"
    )

    # ----------------------------------------
    # Load data
    # ----------------------------------------

    golden_dataset = load_golden_dataset()

    prompt_config = load_prompt_config(
        prompt_version
    )

    results = []

    total_tests = len(golden_dataset)

    # ----------------------------------------
    # Run all test cases
    # ----------------------------------------

    for index, test_case in enumerate(
        golden_dataset,
        start=1
    ):

        print(
            f"Running {index}/{total_tests} "
            f"- {test_case['id']}..."
        )

        try:

            result = evaluate_test_case(
                test_case,
                prompt_config
            )

            results.append(result)

            if result["category_correct"]:

                print(
                    f"   PASS ✓ "
                    f"{result['predicted_category']}"
                )

            else:

                print(
                    "   FAIL ✗ "
                    f"Expected: "
                    f"{result['expected_category']} | "
                    f"Predicted: "
                    f"{result['predicted_category']}"
                )

        except Exception as error:

            print(
                f"   ERROR ✗ {error}"
            )

            results.append(
                {
                    "test_id": test_case["id"],
                    "error": str(error),
                    "category_correct": False
                }
            )


    # ========================================================
    # Calculate Metrics
    # ========================================================

    correct_tests = sum(
        1
        for result in results
        if result.get(
            "category_correct"
        ) is True
    )

    incorrect_tests = (
        total_tests - correct_tests
    )

    accuracy = (
        correct_tests
        / total_tests
        * 100
        if total_tests > 0
        else 0
    )


    # Only successful API results contain latency.
    successful_results = [
        result
        for result in results
        if "latency_ms" in result
    ]


    if successful_results:

        average_latency = sum(
            result["latency_ms"]
            for result in successful_results
        ) / len(successful_results)


        average_summary_score = sum(
            result["summary_score"]
            for result in successful_results
        ) / len(successful_results)

    else:

        average_latency = 0

        average_summary_score = 0


    # ========================================================
    # Build Evaluation Report
    # ========================================================

    report = {

        "prompt_version":
            prompt_version,

        "model":
            "gpt-4o-mini",

        "metrics": {

            "total_tests":
                total_tests,

            "correct":
                correct_tests,

            "incorrect":
                incorrect_tests,

            "accuracy_percent":
                round(accuracy, 2),

            "average_summary_score":
                round(
                    average_summary_score,
                    2
                ),

            "average_latency_ms":
                round(
                    average_latency,
                    2
                )
        },

        "results":
            results
    }


    # ========================================================
    # Save JSON Report
    # ========================================================

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results_path = (
        REPORTS_DIR
        / f"evaluation_{prompt_version}.json"
    )

    with open(
        results_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False
        )


    # ========================================================
    # Save Evaluation History to SQLite
    # ========================================================

    save_evaluation_run(

        prompt_version=
            prompt_version,

        model=
            "gpt-4o-mini",

        total_tests=
            total_tests,

        correct=
            correct_tests,

        incorrect=
            incorrect_tests,

        accuracy_percent=
            round(accuracy, 2),

        average_summary_score=
            round(
                average_summary_score,
                2
            ),

        average_latency_ms=
            round(
                average_latency,
                2
            ),
    )


    # ========================================================
    # Print Final Results
    # ========================================================

    print("\n========================================")
    print("            FINAL RESULTS")
    print("========================================")

    print(
        f"\nPrompt version : "
        f"{prompt_version}"
    )

    print(
        f"Tests executed : "
        f"{total_tests}"
    )

    print(
        f"Correct        : "
        f"{correct_tests}"
    )

    print(
        f"Incorrect      : "
        f"{incorrect_tests}"
    )

    print(
        f"Accuracy       : "
        f"{accuracy:.2f}%"
    )

    print(
        f"Summary score  : "
        f"{average_summary_score:.2f}/5"
    )

    print(
        f"Avg latency    : "
        f"{average_latency:.2f} ms"
    )

    print(
        f"\nReport saved to:\n"
        f"{results_path}"
    )

    print(
        "\n========================================\n"
    )


# ============================================================
# Command-Line Entry Point
# ============================================================

if __name__ == "__main__":

    # Require the user to specify the version.
    #
    # Example:
    # python -m src.evaluator v2

    if len(sys.argv) != 2:

        print(
            "\nUsage:"
            "\n"
            "python -m src.evaluator <version>"
            "\n\nExample:"
            "\n"
            "python -m src.evaluator v2\n"
        )

        sys.exit(1)

    prompt_version = sys.argv[1]

    run_evaluation(prompt_version)