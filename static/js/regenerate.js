/* ============================================================
   FASTAPI ASSISTANT
   REGENERATE MODULE
============================================================ */

(function () {
    "use strict";


    /* ========================================================
       FIND QUESTION FOR THE CLICKED ANSWER
    ======================================================== */

    function findQuestionForCard(
        card
    ) {

        const assistantBlock =
            card.closest(
                ".assistant-block"
            );


        if (!assistantBlock) {
            return "";
        }


        let previous =
            assistantBlock
                .previousElementSibling;


        while (previous) {

            if (
                previous.classList
                    .contains(
                        "user-block"
                    )
            ) {

                const bubble =
                    previous.querySelector(
                        ".user-bubble"
                    );


                return (
                    bubble?.textContent
                    || ""
                ).trim();
            }


            previous =
                previous
                    .previousElementSibling;
        }


        return "";
    }


    /* ========================================================
       FIND RETRIEVAL METHOD
    ======================================================== */

    function findMethodForCard(
        card
    ) {

        const methodElement =
            card.querySelector(
                ".answer-header strong"
            )
            ||
            card.querySelector(
                ".answer-heading h2"
            );


        const methodText =
            (
                methodElement
                    ?.textContent
                || ""
            )
            .trim()
            .toLowerCase();


        if (
            methodText.includes(
                "bm25"
            )
        ) {

            return "bm25";
        }


        return "semantic";
    }


    /* ========================================================
       REGENERATE EXACT ANSWER
    ======================================================== */

    function regenerateAnswer(
        button
    ) {

        const card =
            button.closest(
                ".answer-card"
            );


        if (!card) {
            return;
        }


        const question =
            findQuestionForCard(
                card
            );


        if (!question) {

            console.error(
                "Could not find question for regeneration."
            );

            return;
        }


        const method =
            findMethodForCard(
                card
            );


        const form =
            document.getElementById(
                "question-form"
            );


        const questionInput =
            document.getElementById(
                "question-input"
            );


        const methodSelect =
            document.getElementById(
                "retrieval-method"
            );


        if (
            !form
            ||
            !questionInput
        ) {
            return;
        }


        questionInput.value =
            question;


        if (methodSelect) {

            methodSelect.value =
                method;
        }


        button.disabled =
            true;


        button.textContent =
            "Regenerating...";


        form.requestSubmit();
    }


    /* ========================================================
       ADD BUTTON TO SAVED ANSWERS IF MISSING
    ======================================================== */

    function attachRegenerateButtons() {

        const cards =
            document.querySelectorAll(
                ".answer-card"
            );


        cards.forEach(
            card => {

                let actions =
                    card.querySelector(
                        ".answer-actions"
                    );


                if (!actions) {

                    const header =
                        card.querySelector(
                            ".answer-header"
                        );


                    if (!header) {
                        return;
                    }


                    actions =
                        document.createElement(
                            "div"
                        );


                    actions.className =
                        "answer-actions";


                    header.appendChild(
                        actions
                    );
                }


                const existing =
                    Array.from(
                        actions.querySelectorAll(
                            "button"
                        )
                    )
                    .find(
                        button =>
                            button.textContent
                                .trim()
                                .toLowerCase()
                            === "regenerate"
                    );


                if (existing) {
                    return;
                }


                const button =
                    document.createElement(
                        "button"
                    );


                button.type =
                    "button";


                button.textContent =
                    "Regenerate";


                button.dataset.regenerate =
                    "true";


                actions.appendChild(
                    button
                );
            }
        );
    }


    /* ========================================================
       INTERCEPT REGENERATE CLICK

       Capture mode stops the old inline regenerate function.
    ======================================================== */

    document.addEventListener(
        "click",
        event => {

            const button =
                event.target.closest(
                    ".answer-actions button"
                );


            if (!button) {
                return;
            }


            const isRegenerate =
                button.dataset.regenerate
                === "true"
                ||
                button.textContent
                    .trim()
                    .toLowerCase()
                === "regenerate";


            if (!isRegenerate) {
                return;
            }


            event.preventDefault();

            event.stopImmediatePropagation();


            regenerateAnswer(
                button
            );

        },
        true
    );


    /* ========================================================
       WATCH SAVED CHAT CONTENT
    ======================================================== */

    const observer =
        new MutationObserver(
            () => {

                attachRegenerateButtons();
            }
        );


    function initialiseRegenerate() {

        const chatArea =
            document.querySelector(
                ".chat-area"
            );


        attachRegenerateButtons();


        if (chatArea) {

            observer.observe(
                chatArea,
                {
                    childList:
                        true,

                    subtree:
                        true
                }
            );
        }
    }


    if (
        document.readyState
        === "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initialiseRegenerate
        );

    } else {

        initialiseRegenerate();
    }

})();