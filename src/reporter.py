"""
LLM Regression Detection System
Phase 4: HTML Report Generator

Generates a professional HTML regression report from
the output produced by comparator.py.
"""

import html
from pathlib import Path
from datetime import datetime


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

HTML_REPORT_PATH = REPORTS_DIR / "evaluation_report.html"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def escape(value):
    """
    Safely display values inside HTML.
    """
    return html.escape(str(value))


def status_class(status):
    """
    Convert regression status into Bootstrap classes.
    """

    classes = {
        "PASS": "success",
        "WARNING": "warning",
        "CRITICAL": "danger",
    }

    return classes.get(status, "secondary")


# ============================================================
# BUILD REGRESSION ROWS
# ============================================================

def build_regression_rows(regressions):

    if not regressions:
        return """
        <tr>
            <td colspan="4"
                class="text-center text-success py-4">
                No regressions detected.
            </td>
        </tr>
        """

    rows = ""

    for regression in regressions:

        rows += f"""
        <tr>
            <td>
                <strong>{escape(regression["test_id"])}</strong>
            </td>

            <td>
                {escape(regression.get("expected_category", "N/A"))}
            </td>

            <td>
                {escape(regression.get("baseline_category", "N/A"))}
            </td>

            <td class="text-danger fw-bold">
                {escape(regression.get("current_category", "N/A"))}
            </td>
        </tr>
        """

    return rows


# ============================================================
# BUILD IMPROVEMENT ROWS
# ============================================================

def build_improvement_rows(improvements):

    if not improvements:
        return """
        <tr>
            <td colspan="4"
                class="text-center text-muted py-4">
                No improvements detected.
            </td>
        </tr>
        """

    rows = ""

    for improvement in improvements:

        rows += f"""
        <tr>
            <td>
                <strong>{escape(improvement["test_id"])}</strong>
            </td>

            <td>
                {escape(improvement.get("expected_category", "N/A"))}
            </td>

            <td>
                {escape(improvement.get("baseline_category", "N/A"))}
            </td>

            <td class="text-success fw-bold">
                {escape(improvement.get("current_category", "N/A"))}
            </td>
        </tr>
        """

    return rows


# ============================================================
# GENERATE HTML REPORT
# ============================================================

def generate_html_report(comparison_report):
    """
    Generate reports/evaluation_report.html
    """

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    status = comparison_report["status"]
    bootstrap_status = status_class(status)

    baseline_accuracy = comparison_report[
        "baseline_accuracy"
    ]

    current_accuracy = comparison_report[
        "current_accuracy"
    ]

    delta = comparison_report[
        "accuracy_delta"
    ]

    regressions = comparison_report[
        "regressions"
    ]

    improvements = comparison_report[
        "improvements"
    ]

    generated_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    regression_rows = build_regression_rows(
        regressions
    )

    improvement_rows = build_improvement_rows(
        improvements
    )

    reasons_html = "".join(
        f"<li>{escape(reason)}</li>"
        for reason in comparison_report["reasons"]
    )

    report_html = f"""<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>LLM Regression Report</title>

    <!-- Bootstrap -->
    <link
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
        rel="stylesheet"
    >

</head>

<body class="bg-light">

    <!-- ================================================== -->
    <!-- HEADER -->
    <!-- ================================================== -->

    <header class="bg-dark text-white py-4 mb-4">

        <div class="container">

            <h1 class="fw-bold mb-1">
                LLM Regression Detection
            </h1>

            <p class="mb-0 text-white-50">
                AI Evaluation Report
            </p>

        </div>

    </header>


    <main class="container pb-5">


        <!-- ============================================== -->
        <!-- STATUS -->
        <!-- ============================================== -->

        <section class="mb-4">

            <div class="card shadow-sm border-0">

                <div class="card-body p-4">

                    <div
                        class="
                            d-flex
                            justify-content-between
                            align-items-center
                            flex-wrap
                            gap-3
                        "
                    >

                        <div>

                            <p class="text-muted mb-1">
                                Evaluation Status
                            </p>

                            <h2 class="fw-bold mb-0">
                                {escape(status)}
                            </h2>

                        </div>

                        <span
                            class="
                                badge
                                text-bg-{bootstrap_status}
                                fs-5
                                px-4
                                py-3
                            "
                        >
                            {escape(status)}
                        </span>

                    </div>

                </div>

            </div>

        </section>


        <!-- ============================================== -->
        <!-- METRICS -->
        <!-- ============================================== -->

        <section class="mb-4">

            <div class="row g-3">

                <div class="col-md-3">

                    <div class="card shadow-sm border-0 h-100">

                        <div class="card-body">

                            <p class="text-muted">
                                Baseline
                            </p>

                            <h3 class="fw-bold">
                                {baseline_accuracy:.2f}%
                            </h3>

                            <small>
                                {escape(
                                    comparison_report[
                                        "baseline_prompt"
                                    ]
                                )}
                            </small>

                        </div>

                    </div>

                </div>


                <div class="col-md-3">

                    <div class="card shadow-sm border-0 h-100">

                        <div class="card-body">

                            <p class="text-muted">
                                Current
                            </p>

                            <h3 class="fw-bold">
                                {current_accuracy:.2f}%
                            </h3>

                            <small>
                                {escape(
                                    comparison_report[
                                        "current_prompt"
                                    ]
                                )}
                            </small>

                        </div>

                    </div>

                </div>


                <div class="col-md-3">

                    <div class="card shadow-sm border-0 h-100">

                        <div class="card-body">

                            <p class="text-muted">
                                Accuracy Delta
                            </p>

                            <h3 class="fw-bold">
                                {delta:+.2f}%
                            </h3>

                        </div>

                    </div>

                </div>


                <div class="col-md-3">

                    <div class="card shadow-sm border-0 h-100">

                        <div class="card-body">

                            <p class="text-muted">
                                Regressions
                            </p>

                            <h3 class="fw-bold text-danger">
                                {
                                    comparison_report[
                                        "regression_count"
                                    ]
                                }
                            </h3>

                        </div>

                    </div>

                </div>

            </div>

        </section>


        <!-- ============================================== -->
        <!-- THRESHOLD RESULT -->
        <!-- ============================================== -->

        <section class="mb-4">

            <div
                class="
                    alert
                    alert-{bootstrap_status}
                    shadow-sm
                "
            >

                <h4 class="alert-heading">
                    Threshold Analysis
                </h4>

                <ul class="mb-0">
                    {reasons_html}
                </ul>

            </div>

        </section>


        <!-- ============================================== -->
        <!-- REGRESSIONS -->
        <!-- ============================================== -->

        <section class="mb-4">

            <div class="card shadow-sm border-0">

                <div class="card-header bg-white py-3">

                    <h4 class="mb-0">
                        Regressions
                    </h4>

                </div>

                <div class="table-responsive">

                    <table
                        class="
                            table
                            table-hover
                            align-middle
                            mb-0
                        "
                    >

                        <thead class="table-light">

                            <tr>
                                <th>Test</th>
                                <th>Expected</th>
                                <th>Previous</th>
                                <th>Current</th>
                            </tr>

                        </thead>

                        <tbody>
                            {regression_rows}
                        </tbody>

                    </table>

                </div>

            </div>

        </section>


        <!-- ============================================== -->
        <!-- IMPROVEMENTS -->
        <!-- ============================================== -->

        <section class="mb-4">

            <div class="card shadow-sm border-0">

                <div class="card-header bg-white py-3">

                    <h4 class="mb-0">
                        Improvements
                    </h4>

                </div>

                <div class="table-responsive">

                    <table
                        class="
                            table
                            table-hover
                            align-middle
                            mb-0
                        "
                    >

                        <thead class="table-light">

                            <tr>
                                <th>Test</th>
                                <th>Expected</th>
                                <th>Previous</th>
                                <th>Current</th>
                            </tr>

                        </thead>

                        <tbody>
                            {improvement_rows}
                        </tbody>

                    </table>

                </div>

            </div>

        </section>


        <!-- ============================================== -->
        <!-- FOOTER INFORMATION -->
        <!-- ============================================== -->

        <section>

            <div class="card border-0 shadow-sm">

                <div class="card-body">

                    <small class="text-muted">

                        Generated:
                        {escape(generated_at)}

                    </small>

                </div>

            </div>

        </section>


    </main>

</body>

</html>
"""

    with open(
        HTML_REPORT_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(report_html)

    print(
        "\nHTML report generated:"
    )

    print(
        HTML_REPORT_PATH
    )

    return HTML_REPORT_PATH