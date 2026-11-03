/* ============================================================
   FASTAPI ASSISTANT
   NEW CHAT MODULE
============================================================ */

(function () {
    "use strict";


    const ACTIVE_CHAT_KEY =
        "fastapi_active_chat_id";


    /* ========================================================
       START A COMPLETELY NEW CHAT
    ======================================================== */

    function startNewChat() {

        /*
         * Remove the saved active conversation.
         * The next submitted question will therefore
         * create a brand-new database chat.
         */
        sessionStorage.removeItem(
            ACTIVE_CHAT_KEY
        );


        /*
         * Clear the active chat reference used
         * by the existing chat interface.
         */
        window.currentSavedChatId =
            null;


        /*
         * Remove any existing hidden chat_id
         * from the question form as an extra safeguard.
         */
        const form =
            document.getElementById(
                "question-form"
            );


        const hiddenChatId =
            form?.querySelector(
                'input[name="chat_id"]'
            );


        if (hiddenChatId) {

            hiddenChatId.remove();
        }


        /*
         * Return to the clean assistant page.
         */
        window.location.href =
            "/";
    }


    /* ========================================================
       REPLACE OLD NEW CHAT FUNCTION
    ======================================================== */

    window.newChat =
        startNewChat;

})();