# ============================================================
# FASTAPI ASSISTANT
# SIMPLE RESULTS PAGE
# ============================================================

import json


def load_results(results_file):

    if not results_file.exists():
        return None

    try:
        return json.loads(
            results_file.read_text(
                encoding="utf-8"
            )
        )

    except Exception as exc:
        print(
            "Could not load results:",
            repr(exc),
        )
        return None


def get_results_content(
    results_file,
    graphs_dir,
):

    data = load_results(
        results_file
    )

    if not data:

        return """
        <section class="page">

            <h1>
                Evaluation Results
            </h1>

            <div class="error-card">
                Evaluation results could not be loaded.
            </div>

        </section>
        """


    semantic = (
        data["retrieval_results"]["semantic"]
    )

    bm25 = (
        data["retrieval_results"]["bm25"]
    )

    semantic_answer = (
        data["answer_quality_results"]["semantic"]
    )

    bm25_answer = (
        data["answer_quality_results"]["bm25"]
    )


    semantic_top1 = (
        semantic["hit_at_1"] * 100
    )

    semantic_top3 = (
        semantic["hit_at_3"] * 100
    )

    semantic_top5 = (
        semantic["hit_at_5"] * 100
    )

    bm25_top1 = (
        bm25["hit_at_1"] * 100
    )

    bm25_top3 = (
        bm25["hit_at_3"] * 100
    )

    bm25_top5 = (
        bm25["hit_at_5"] * 100
    )

    semantic_mrr = (
        semantic["mean_reciprocal_rank"]
    )

    bm25_mrr = (
        bm25["mean_reciprocal_rank"]
    )

    semantic_correctness = (
        semantic_answer[
            "correctness_percentage"
        ]
    )

    bm25_correctness = (
        bm25_answer[
            "correctness_percentage"
        ]
    )


    graph_files = [
        "retrieval_accuracy.png",
        "mean_reciprocal_rank.png",
        "answer_correctness.png",
        "retrieval_response_time.png",
        "total_response_time.png",
    ]

    graph_html = ""

    for filename in graph_files:

        if (
            graphs_dir
            / filename
        ).exists():

            graph_html += f"""
            <div class="graph-card">

                <img
                    src="/graphs/{filename}"
                    alt="Evaluation graph"
                >

            </div>
            """


    return f"""
    <section class="page">

        <div class="page-heading">

            <span class="small-label">
                Candidate Evaluation
            </span>

            <h1>
                Semantic vs BM25 Results
            </h1>

            <p>
                Evaluation of semantic retrieval
                and BM25 retrieval using the same
                FastAPI documentation corpus.
            </p>

        </div>


        <h2>
            Retrieval Accuracy
        </h2>

        <div class="metric-grid">

            <div class="metric-card">
                <span>Semantic Top-1</span>
                <strong>
                    {semantic_top1:.0f}%
                </strong>
            </div>

            <div class="metric-card">
                <span>BM25 Top-1</span>
                <strong>
                    {bm25_top1:.0f}%
                </strong>
            </div>

            <div class="metric-card">
                <span>Semantic Top-3</span>
                <strong>
                    {semantic_top3:.0f}%
                </strong>
            </div>

            <div class="metric-card">
                <span>BM25 Top-3</span>
                <strong>
                    {bm25_top3:.0f}%
                </strong>
            </div>

            <div class="metric-card">
                <span>Semantic Top-5</span>
                <strong>
                    {semantic_top5:.0f}%
                </strong>
            </div>

            <div class="metric-card">
                <span>BM25 Top-5</span>
                <strong>
                    {bm25_top5:.0f}%
                </strong>
            </div>

        </div>


        <h2>
            Ranking and Answer Quality
        </h2>

        <div class="metric-grid">

            <div class="metric-card">
                <span>Semantic MRR</span>
                <strong>
                    {semantic_mrr:.3f}
                </strong>
            </div>

            <div class="metric-card">
                <span>BM25 MRR</span>
                <strong>
                    {bm25_mrr:.3f}
                </strong>
            </div>

            <div class="metric-card">
                <span>Semantic Correctness</span>
                <strong>
                    {semantic_correctness:.1f}%
                </strong>
            </div>

            <div class="metric-card">
                <span>BM25 Correctness</span>
                <strong>
                    {bm25_correctness:.1f}%
                </strong>
            </div>

        </div>


        <h2>
            Evaluation Graphs
        </h2>

        <div class="graph-grid">
            {graph_html}
        </div>


        <div class="info-card">

            <h2>
                Current Result
            </h2>

            <p>
                In the current candidate evaluation,
                semantic retrieval performed better
                than BM25 for retrieval accuracy,
                ranking quality and answer correctness.
            </p>

        </div>

    </section>
    """