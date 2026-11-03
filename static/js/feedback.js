/* ============================================================
   FASTAPI ASSISTANT
   FEEDBACK MODULE
============================================================ */

(function () {
    "use strict";


    const ACTIVE_CHAT_KEY =
        "fastapi_active_chat_id";


    /* ========================================================
       CREATE FEEDBACK ROW
    ======================================================== */

    function createFeedbackRow(
        messageId
    ) {

        const row =
            document.createElement(
                "div"
            );


        row.className =
            "feedback-row";


        row.dataset.messageId =
            String(
                messageId
            );


        const label =
            document.createElement(
                "span"
            );


        label.textContent =
            "Was this answer useful?";


        const yesButton =
            document.createElement(
                "button"
            );


        yesButton.type =
            "button";


        yesButton.className =
            "feedback-button";


        yesButton.textContent =
            "👍 Yes";


        yesButton.dataset.helpful =
            "1";


        const noButton =
            document.createElement(
                "button"
            );


        noButton.type =
            "button";


        noButton.className =
            "feedback-button";


        noButton.textContent =
            "👎 No";


        noButton.dataset.helpful =
            "0";


        const thanks =
            document.createElement(
                "span"
            );


        thanks.className =
            "feedback-thanks";


        row.appendChild(
            label
        );


        row.appendChild(
            yesButton
        );


        row.appendChild(
            noButton
        );


        row.appendChild(
            thanks
        );


        return row;
    }


    /* ========================================================
       LOAD MESSAGE IDS FOR CURRENT CHAT
    ======================================================== */

    async function attachFeedbackToSavedChat() {

        const chatId =
            sessionStorage.getItem(
                ACTIVE_CHAT_KEY
            );


        if (!chatId) {
            return;
        }


        const cards =
            document.querySelectorAll(
                ".chat-area .assistant-block .answer-card"
            );


        if (!cards.length) {
            return;
        }


        try {

            const response =
                await fetch(
                    `/api/chats/${chatId}`,
                    {
                        credentials:
                            "same-origin"
                    }
                );


            if (!response.ok) {
                return;
            }


            const data =
                await response.json();


            const assistantMessages =
                (
                    data.messages
                    || []
                )
                .filter(
                    message =>
                        message.role
                        === "assistant"
                );


            cards.forEach(
                (
                    card,
                    index
                ) => {

                    const message =
                        assistantMessages[
                            index
                        ];


                    if (
                        !message
                        ||
                        !message.id
                    ) {
                        return;
                    }


                    card.dataset.messageId =
                        String(
                            message.id
                        );


                    let feedback =
                        card.querySelector(
                            ".feedback-row"
                        );


                    if (!feedback) {

                        feedback =
                            createFeedbackRow(
                                message.id
                            );


                        card.appendChild(
                            feedback
                        );

                    } else {

                        feedback.dataset.messageId =
                            String(
                                message.id
                            );
                    }
                }
            );


        } catch (error) {

            console.error(
                "Feedback setup error:",
                error
            );
        }
    }


    /* ========================================================
       SAVE FEEDBACK
    ======================================================== */

    async function saveFeedback(
        button
    ) {

        const row =
            button.closest(
                ".feedback-row"
            );


        if (!row) {
            return;
        }


        const card =
            button.closest(
                ".answer-card"
            );


        const messageId =
            row.dataset.messageId
            ||
            card?.dataset.messageId;


        if (!messageId) {

            console.error(
                "No message ID for feedback."
            );

            return;
        }


        const helpful =
            button.dataset.helpful;


        if (
            helpful !== "0"
            &&
            helpful !== "1"
        ) {
            return;
        }


        const formData =
            new FormData();


        formData.append(
            "helpful",
            helpful
        );


        const thanks =
            row.querySelector(
                ".feedback-thanks"
            );


        try {

            const response =
                await fetch(
                    `/api/messages/${messageId}/feedback`,
                    {
                        method:
                            "POST",

                        body:
                            formData,

                        credentials:
                            "same-origin"
                    }
                );


            if (!response.ok) {

                throw new Error(
                    "Could not save feedback."
                );
            }


            row
                .querySelectorAll(
                    ".feedback-button"
                )
                .forEach(
                    item => {

                        item.classList.remove(
                            "active"
                        );
                    }
                );


            button.classList.add(
                "active"
            );


            if (thanks) {

                thanks.textContent =
                    helpful === "1"
                    ? "Thanks for your feedback ✓"
                    : "Thanks — this helps improve the assistant.";
            }


        } catch (error) {

            console.error(
                "Feedback save error:",
                error
            );


            if (thanks) {

                thanks.textContent =
                    "Could not save feedback.";
            }
        }
    }


    /* ========================================================
       CLICK HANDLER
    ======================================================== */

    document.addEventListener(
        "click",
        event => {

            const button =
                event.target.closest(
                    ".feedback-button"
                );


            if (!button) {
                return;
            }


            if (
                button.dataset.helpful
                === undefined
            ) {

                if (
                    button.textContent
                        .includes(
                            "Yes"
                        )
                ) {

                    button.dataset.helpful =
                        "1";

                } else {

                    button.dataset.helpful =
                        "0";
                }
            }


            event.preventDefault();


            saveFeedback(
                button
            );
        }
    );


    /* ========================================================
       WATCH SAVED CHAT CHANGES

       app.js can rebuild the conversation after
       opening a saved chat. This observer detects
       that and attaches feedback afterwards.
    ======================================================== */

    const observer =
        new MutationObserver(
            () => {

                attachFeedbackToSavedChat();
            }
        );


    document.addEventListener(
        "DOMContentLoaded",
        () => {

            const chatArea =
                document.querySelector(
                    ".chat-area"
                );


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


            attachFeedbackToSavedChat();
        }
    );

})();