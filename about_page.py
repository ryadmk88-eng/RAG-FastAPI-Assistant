# ============================================================
# FASTAPI DOCUMENTATION ASSISTANT
# ABOUT PAGE CONTENT
# ============================================================


def get_about_content():
    """
    Return the HTML content used by the About page.

    Keeping this content outside main.py helps separate
    page presentation from the main application logic.
    """

    return """
    <section class="page">

        <div class="page-heading">

            <span class="small-label">
                Final Year Project
            </span>

            <h1>
                RAG-Based Technical Documentation Assistant
            </h1>

            <p>
                This project investigates how effectively a
                Retrieval-Augmented Generation system can
                retrieve relevant information from official
                FastAPI documentation and generate accurate,
                source-supported answers.
            </p>

        </div>


        <div class="info-grid">

            <article class="info-card">

                <h2>
                    Documentation Corpus
                </h2>

                <p>
                    The system uses official English FastAPI
                    documentation. Pages are collected,
                    cleaned and divided into searchable
                    chunks while preserving their original
                    source URLs.
                </p>

            </article>


            <article class="info-card">

                <h2>
                    Semantic Retrieval
                </h2>

                <p>
                    Semantic search uses pretrained sentence
                    embeddings to retrieve documentation
                    chunks according to meaning and contextual
                    similarity with the user's question.
                </p>

            </article>


            <article class="info-card">

                <h2>
                    BM25 Retrieval
                </h2>

                <p>
                    BM25 provides a keyword-based retrieval
                    baseline over the same FastAPI
                    documentation corpus, allowing direct
                    comparison with semantic retrieval.
                </p>

            </article>


            <article class="info-card">

                <h2>
                    Grounded Generation
                </h2>

                <p>
                    Retrieved documentation is provided to a
                    pretrained language model. The assistant
                    generates an answer using the retrieved
                    context and displays supporting FastAPI
                    documentation sources.
                </p>

            </article>


            <article class="info-card">

                <h2>
                    Retrieval Comparison
                </h2>

                <p>
                    Semantic and BM25 retrieval are evaluated
                    using the same FastAPI questions so their
                    retrieval accuracy, answer quality and
                    response performance can be compared
                    fairly.
                </p>

            </article>


            <article class="info-card">

                <h2>
                    Evaluation
                </h2>

                <p>
                    The project evaluates retrieval accuracy,
                    answer correctness, source support,
                    unsupported claims, response time and
                    observed failure cases.
                </p>

            </article>

        </div>


        <div class="about-section">

            <span class="small-label">
                Main Research Question
            </span>

            <h2>
                Research focus
            </h2>

            <p>
                How effectively can a RAG documentation
                assistant retrieve relevant FastAPI
                information and generate accurate,
                source-supported answers?
            </p>

        </div>


        <div class="about-section">

            <span class="small-label">
                Secondary Research Question
            </span>

            <h2>
                Retrieval comparison
            </h2>

            <p>
                How does semantic/vector retrieval compare
                with BM25 keyword retrieval when searching
                the same FastAPI documentation corpus?
            </p>

        </div>


        <div class="about-section">

            <span class="small-label">
                System Workflow
            </span>

            <h2>
                How the assistant works
            </h2>

            <div class="workflow-row">

                <div class="workflow-step">
                    <strong>1</strong>
                    <span>User question</span>
                </div>

                <div class="workflow-arrow">
                    →
                </div>

                <div class="workflow-step">
                    <strong>2</strong>
                    <span>Document retrieval</span>
                </div>

                <div class="workflow-arrow">
                    →
                </div>

                <div class="workflow-step">
                    <strong>3</strong>
                    <span>Relevant FastAPI chunks</span>
                </div>

                <div class="workflow-arrow">
                    →
                </div>

                <div class="workflow-step">
                    <strong>4</strong>
                    <span>Grounded generation</span>
                </div>

                <div class="workflow-arrow">
                    →
                </div>

                <div class="workflow-step">
                    <strong>5</strong>
                    <span>Answer + sources</span>
                </div>

            </div>

        </div>

    </section>
    """