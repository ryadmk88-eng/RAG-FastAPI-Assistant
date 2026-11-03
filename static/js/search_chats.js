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
       FILTER DATABASE CHAT ROWS
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
       REMOVE OLD LOCALSTORAGE SEARCH LISTENER
    ======================================================== */

    function replaceSearchInput() {

        const oldInput =
            document.getElementById(
                SEARCH_INPUT_ID
            );


        if (!oldInput) {
            return;
        }


        /*
         * Cloning the input removes the old JavaScript
         * event listener that searched localStorage.
         *
         * The ID, classes, placeholder and styling remain.
         */
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


    /* ========================================================
       WATCH DATABASE HISTORY RELOADS

       Pin, rename and delete can rebuild the Recents list.
       When that happens, keep the current search applied.
    ======================================================== */

    function watchHistory() {

        const container =
            document.getElementById(
                HISTORY_CONTAINER_ID
            );


        if (!container) {
            return;
        }


        const observer =
            new MutationObserver(
                mutations => {

                    const importantChange =
                        mutations.some(
                            mutation => {

                                return Array.from(
                                    mutation.addedNodes
                                )
                                .some(
                                    node => {

                                        return (
                                            node.nodeType === 1
                                            &&
                                            (
                                                node.classList
                                                    ?.contains(
                                                        "history-row"
                                                    )
                                                ||
                                                node.querySelector
                                                    ?.(
                                                        ".history-row"
                                                    )
                                            )
                                        );
                                    }
                                );
                            }
                        );


                    if (importantChange) {

                        filterChats();
                    }
                }
            );


        observer.observe(
            container,
            {
                childList:
                    true
            }
        );
    }


    /* ========================================================
       START
    ======================================================== */

    function initialiseChatSearch() {

        replaceSearchInput();

        watchHistory();

        filterChats();
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