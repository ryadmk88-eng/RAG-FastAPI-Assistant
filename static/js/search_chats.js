/* ============================================================
   FASTAPI ASSISTANT
   DATABASE CHAT SEARCH
============================================================ */

(function () {
    "use strict";


    const SEARCH_INPUT_ID =
        "history-search-input";


    const HISTORY_CONTAINER_ID =
        "history-container";


    let searchInput = null;


    /* ========================================================
       FILTER DATABASE CHATS
    ======================================================== */

    function filterChats() {

        const container =
            document.getElementById(
                HISTORY_CONTAINER_ID
            );


        if (
            !container
            ||
            !searchInput
        ) {
            return;
        }


        const query =
            searchInput
                .value
                .trim()
                .toLowerCase();


        const rows =
            container.querySelectorAll(
                ".history-row"
            );


        let visibleCount = 0;


        rows.forEach(
            row => {

                const chatButton =
                    row.querySelector(
                        ".history-item"
                    );


                const title =
                    (
                        chatButton?.title
                        ||
                        chatButton?.textContent
                        ||
                        ""
                    )
                    .trim()
                    .toLowerCase();


                const matches =
                    !query
                    ||
                    title.includes(
                        query
                    );


                row.style.setProperty(
                    "display",
                    matches
                        ? "flex"
                        : "none",
                    "important"
                );


                if (matches) {
                    visibleCount += 1;
                }
            }
        );


        let emptyMessage =
            container.querySelector(
                ".database-search-empty"
            );


        if (
            query
            &&
            rows.length
            &&
            visibleCount === 0
        ) {

            if (!emptyMessage) {

                emptyMessage =
                    document.createElement(
                        "div"
                    );


                emptyMessage.className =
                    "history-empty database-search-empty";


                emptyMessage.textContent =
                    "No matching chats.";


                container.appendChild(
                    emptyMessage
                );
            }

        } else if (emptyMessage) {

            emptyMessage.remove();
        }
    }


    /* ========================================================
       REPLACE OLD LOCALSTORAGE SEARCH INPUT
    ======================================================== */

    function initialiseChatSearch() {

        const oldInput =
            document.getElementById(
                SEARCH_INPUT_ID
            );


        if (!oldInput) {
            return;
        }


        const newInput =
            oldInput.cloneNode(
                true
            );


        oldInput.replaceWith(
            newInput
        );


        searchInput =
            newInput;


        searchInput.addEventListener(
            "input",
            filterChats
        );


        searchInput.addEventListener(
            "keydown",
            event => {

                if (
                    event.key
                    === "Escape"
                ) {

                    searchInput.value =
                        "";


                    filterChats();


                    searchInput.blur();
                }
            }
        );
    }


    if (
        document.readyState
        === "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initialiseChatSearch
        );

    } else {

        initialiseChatSearch();
    }

})();