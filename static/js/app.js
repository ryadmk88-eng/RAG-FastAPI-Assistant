if ("scrollRestoration" in history) {
    history.scrollRestoration = "manual";
}


/* ============================================================
   FASTAPI ASSISTANT - EXTERNAL JAVASCRIPT
   Stable restore version
============================================================ */

(function () {
    "use strict";

    /* ========================================================
       HISTORY / SAVED CHAT STYLES
    ======================================================== */

    (function injectHistoryStyles() {
        const previous =
            document.getElementById(
                "history-menu-styles"
            );

        if (previous) {
            previous.remove();
        }

        const style =
            document.createElement(
                "style"
            );

        style.id =
            "history-menu-styles";

        style.textContent = `
            #history-container {
                width: 100% !important;
                overflow: visible !important;
            }

            .history-row {
                position: relative !important;
                width: 100% !important;

                display: flex !important;
                align-items: center !important;

                gap: 2px !important;

                margin: 0 !important;
                padding: 0 !important;

                background: transparent !important;
            }

            .history-row .history-item {
                flex: 1 1 auto !important;
                min-width: 0 !important;

                margin: 0 !important;
                padding: 8px 5px !important;

                border: none !important;
                outline: none !important;

                border-radius: 7px !important;

                background: transparent !important;
                color: var(--text) !important;

                box-shadow: none !important;

                text-align: left !important;
                font-size: 12px !important;

                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;

                cursor: pointer !important;
            }

            .history-row .history-item:hover {
                background:
                    var(--surface-2) !important;
            }

            .history-menu-wrapper {
                position: relative !important;

                flex: 0 0 30px !important;

                width: 30px !important;
                height: 30px !important;

                margin-left: auto !important;
            }

            .history-menu-button {
                width: 30px !important;
                height: 30px !important;

                margin: 0 !important;
                padding: 0 !important;

                display: flex !important;
                align-items: center !important;
                justify-content: center !important;

                border: none !important;
                outline: none !important;

                border-radius: 7px !important;

                background: transparent !important;
                color: var(--muted) !important;

                box-shadow: none !important;

                font-size: 20px !important;
                font-weight: 600 !important;
                line-height: 1 !important;

                opacity: 1 !important;

                cursor: pointer !important;
            }

            .history-menu-button:hover {
                background:
                    var(--surface-2) !important;

                color:
                    var(--text) !important;
            }

            .history-menu {
                display: none !important;

                position: absolute !important;

                right: 0 !important;
                top: 32px !important;

                z-index: 99999 !important;

                width: 150px !important;

                margin: 0 !important;
                padding: 5px !important;

                border:
                    1px solid
                    var(--border) !important;

                border-radius: 10px !important;

                background:
                    var(--surface) !important;

                box-shadow:
                    0 14px 34px
                    rgba(0, 0, 0, .35) !important;
            }

            .history-menu.open {
                display: flex !important;

                flex-direction:
                    column !important;

                gap: 1px !important;
            }

            .history-menu button {
                display: block !important;

                width: 100% !important;

                margin: 0 !important;
                padding:
                    9px 10px !important;

                border: none !important;
                outline: none !important;

                border-radius:
                    7px !important;

                background:
                    transparent !important;

                color:
                    var(--text) !important;

                box-shadow:
                    none !important;

                text-align:
                    left !important;

                font-size:
                    12px !important;

                cursor:
                    pointer !important;
            }

            .history-menu button:hover {
                background:
                    var(--surface-2) !important;
            }

            .history-menu button.danger {
                color:
                    #e45868 !important;
            }

            body[data-theme="dark"]
            .history-menu {
                background:
                    #1d1f27 !important;

                border-color:
                    rgba(
                        255,
                        255,
                        255,
                        .10
                    ) !important;
            }

            body[data-theme="dark"]
            .history-menu button {
                color:
                    #f4f4f5 !important;
            }

            body[data-theme="dark"]
            .history-menu button:hover {
                background:
                    #292c35 !important;
            }

            body[data-theme="dark"]
            .history-menu-button {
                color:
                    #a5a7af !important;
            }

            body[data-theme="dark"]
            .history-menu button.danger {
                color:
                    #ff7d8d !important;
            }

            body[data-theme="light"]
            .history-menu {
                background:
                    #ffffff !important;

                border-color:
                    rgba(
                        24,
                        24,
                        27,
                        .12
                    ) !important;
            }

            body[data-theme="light"]
            .history-menu button {
                color:
                    #18181b !important;
            }

            body[data-theme="light"]
            .history-menu button:hover {
                background:
                    #f1f1f3 !important;
            }

            body[data-theme="light"]
            .history-menu-button {
                color:
                    #686b75 !important;
            }

            body[data-theme="light"]
            .history-menu button.danger {
                color:
                    #d94d5d !important;
            }

            .saved-chat-title {
                width:
                    min(
                        900px,
                        calc(
                            100% - 34px
                        )
                    );

                margin:
                    18px auto 10px;

                padding-bottom:
                    12px;

                border-bottom:
                    1px solid
                    var(--border);

                color:
                    var(--muted);

                font-size:
                    11px;
            }

            .saved-chat-title strong {
                color:
                    var(--text);

                font-size:
                    13px;
            }

            .saved-performance-row {
                display:
                    flex;

                flex-wrap:
                    wrap;

                gap:
                    8px;

                margin-top:
                    14px;

                color:
                    var(--muted);

                font-size:
                    10px;
            }

            .saved-source-empty {
                margin-top:
                    8px;

                color:
                    var(--muted);

                font-size:
                    11px;
            }

            .saved-source-list {
                display:
                    grid;

                gap:
                    7px;

                margin-top:
                    8px;
            }

            .saved-source-link {
                display:
                    block;

                padding:
                    10px;

                border:
                    1px solid
                    var(--border);

                border-radius:
                    9px;

                color:
                    var(--text);

                text-decoration:
                    none;

                font-size:
                    11px;
            }

            .saved-source-link:hover {
                background:
                    var(--surface-2);
            }

            .saved-source-link span {
                display:
                    block;

                margin-top:
                    3px;

                color:
                    var(--muted);

                font-size:
                    9px;
            }

            .history-empty {
                padding:
                    8px 5px !important;

                color:
                    var(--muted) !important;

                font-size:
                    11px !important;
            }
        `;

        document.head.appendChild(
            style
        );
    })();


    /* ========================================================
       STATE + HELPERS
    ======================================================== */

    const ACTIVE_CHAT_KEY =
        "fastapi_active_chat_id";


    let currentSavedChatId =
        null;


    window.currentSavedChatId =
        null;


    function escapeHtml(
        value
    ) {

        return String(
            value ?? ""
        )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
    }


    function getInitials(
        name
    ) {

        if (!name) {
            return "U";
        }


        const parts =
            name
                .trim()
                .split(
                    /\s+/
                )
                .filter(
                    Boolean
                );


        if (!parts.length) {
            return "U";
        }


        if (
            parts.length === 1
        ) {

            return parts[0]
                .charAt(0)
                .toUpperCase();
        }


        return (
            parts[0]
                .charAt(0)
            +
            parts[1]
                .charAt(0)
        ).toUpperCase();
    }


    /* ========================================================
       SAVED ANSWER FORMATTING
    ======================================================== */

    function formatSavedTextSection(
        text
    ) {

        let escaped =
            escapeHtml(
                text
            );


        escaped =
            escaped.replace(
                /`([^`\n]+)`/g,
                "<code>$1</code>"
            );


        escaped =
            escaped.replace(
                /\[Source\s+(\d+)\]/gi,
                '<span class="citation">'
                + 'Source $1'
                + '</span>'
            );


        const lines =
            escaped.split(
                /\r?\n/
            );


        const output =
            [];


        let inList =
            false;


        function closeList() {

            if (inList) {

                output.push(
                    "</ul>"
                );

                inList =
                    false;
            }
        }


        for (
            const originalLine
            of lines
        ) {

            let line =
                originalLine.trim();


            if (!line) {

                closeList();

                continue;
            }


            const heading =
                line.match(
                    /^#{1,4}\s+(.+)$/
                );


            if (heading) {

                closeList();


                output.push(
                    '<h3 class="answer-subheading">'
                    + heading[1]
                    + '</h3>'
                );


                continue;
            }


            line =
                line.replace(
                    /\*\*(.+?)\*\*/g,
                    "<strong>$1</strong>"
                );


            if (
                line.startsWith(
                    "- "
                )
                ||
                line.startsWith(
                    "* "
                )
            ) {

                if (!inList) {

                    output.push(
                        '<ul class="answer-list">'
                    );

                    inList =
                        true;
                }


                output.push(
                    "<li>"
                    + line.slice(2)
                    + "</li>"
                );


                continue;
            }


            const numbered =
                line.match(
                    /^\d+\.\s+(.+)$/
                );


            if (numbered) {

                if (!inList) {

                    output.push(
                        '<ul class="answer-list">'
                    );

                    inList =
                        true;
                }


                output.push(
                    "<li>"
                    + numbered[1]
                    + "</li>"
                );


                continue;
            }


            closeList();


            output.push(
                "<p>"
                + line
                + "</p>"
            );
        }


        closeList();


        return output.join(
            "\n"
        );
    }


    function formatSavedAnswer(
        answer
    ) {

        const text =
            String(
                answer ?? ""
            );


        const regex =
            /```(?:[\w+-]+)?\s*\n?([\s\S]*?)```/g;


        const output =
            [];


        let lastIndex =
            0;


        let match;


        while (
            (
                match =
                    regex.exec(
                        text
                    )
            )
            !== null
        ) {

            const before =
                text.slice(
                    lastIndex,
                    match.index
                );


            if (
                before.trim()
            ) {

                output.push(
                    formatSavedTextSection(
                        before
                    )
                );
            }


            const code =
                escapeHtml(
                    match[1].trim()
                );


            output.push(
                `
                <div class="code-wrapper">

                    <div class="code-header">

                        <span>
                            Code example
                        </span>

                        <button
                            type="button"
                            class="saved-copy-code"
                        >
                            Copy
                        </button>

                    </div>

                    <pre><code>${code}</code></pre>

                </div>
                `
            );


            lastIndex =
                regex.lastIndex;
        }


        const remaining =
            text.slice(
                lastIndex
            );


        if (
            remaining.trim()
        ) {

            output.push(
                formatSavedTextSection(
                    remaining
                )
            );
        }


        return output.join(
            "\n"
        );
    }


    function extractSavedCitationNumbers(
        answer
    ) {

        const numbers =
            new Set();


        const regex =
            /\[Source\s+(\d+)\]/gi;


        let match;


        while (
            (
                match =
                    regex.exec(
                        answer || ""
                    )
            )
            !== null
        ) {

            numbers.add(
                Number(
                    match[1]
                )
            );
        }


        return numbers;
    }


    function normaliseSavedSources(
        sources
    ) {

        if (!sources) {
            return [];
        }


        if (
            Array.isArray(
                sources
            )
        ) {
            return sources;
        }


        if (
            typeof sources
            === "object"
        ) {

            return Object.values(
                sources
            );
        }


        return [];
    }


    function getCitedSavedSources(
        message
    ) {

        const sources =
            normaliseSavedSources(
                message.sources
            );


        const cited =
            extractSavedCitationNumbers(
                message.content || ""
            );


        if (!cited.size) {
            return [];
        }


        return sources.filter(
            (
                source,
                index
            ) => {

                if (!source) {
                    return false;
                }


                const number =
                    Number(
                        source.number
                        ?? index + 1
                    );


                return cited.has(
                    number
                );
            }
        );
    }


    /* ========================================================
       ACCOUNT
    ======================================================== */

    async function logoutAccount() {

        try {

            const response =
                await fetch(
                    "/logout",
                    {
                        method:
                            "POST",

                        credentials:
                            "same-origin"
                    }
                );


            if (!response.ok) {
                return;
            }


            sessionStorage.removeItem(
                ACTIVE_CHAT_KEY
            );


            window.location.href =
                "/";


        } catch (error) {

            console.error(
                "Logout failed:",
                error
            );
        }
    }


    async function loadAccountStatus() {

        try {

            const response =
                await fetch(
                    "/api/me",
                    {
                        credentials:
                            "same-origin"
                    }
                );


            if (!response.ok) {
                return;
            }


            const user =
                await response.json();


            if (!user.authenticated) {
                return;
            }


            const topAccount =
                document.querySelector(
                    ".signin-top"
                );


            if (topAccount) {

                topAccount.textContent =
                    user.name;


                topAccount.href =
                    "/";


                topAccount.title =
                    user.email;
            }


            const topbar =
                document.querySelector(
                    ".topbar-right"
                );


            if (
                topbar
                &&
                !document.getElementById(
                    "logout-button"
                )
            ) {

                const logoutButton =
                    document.createElement(
                        "button"
                    );


                logoutButton.type =
                    "button";


                logoutButton.id =
                    "logout-button";


                logoutButton.className =
                    "top-button";


                logoutButton.textContent =
                    "Log out";


                logoutButton.onclick =
                    logoutAccount;


                topbar.appendChild(
                    logoutButton
                );
            }


            const avatar =
                document.querySelector(
                    ".profile-avatar"
                );


            const name =
                document.querySelector(
                    ".profile-copy strong"
                );


            const email =
                document.querySelector(
                    ".profile-copy span"
                );


            if (avatar) {

                avatar.textContent =
                    getInitials(
                        user.name
                    );
            }


            if (name) {

                name.textContent =
                    user.name;
            }


            if (email) {

                email.textContent =
                    user.email;
            }


            await loadDatabaseChats();


        } catch (error) {

            console.error(
                "Account error:",
                error
            );
        }
    }


    /* ========================================================
       CHAT HISTORY
    ======================================================== */

    async function loadDatabaseChats() {

        const container =
            document.getElementById(
                "history-container"
            );


        if (!container) {
            return;
        }


        try {

            const response =
                await fetch(
                    "/api/chats",
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


            if (!data.authenticated) {
                return;
            }


            container.innerHTML =
                "";


            if (
                !data.chats.length
            ) {

                container.innerHTML =
                    `
                    <div class="history-empty">
                        No recent chats yet.
                    </div>
                    `;


                return;
            }


            data.chats.forEach(
                chat => {

                    createHistoryRow(
                        container,
                        chat
                    );
                }
            );


        } catch (error) {

            console.error(
                "Chat history error:",
                error
            );
        }
    }


    function createHistoryRow(
        container,
        chat
    ) {

        const row =
            document.createElement(
                "div"
            );


        row.className =
            "history-row";


        const openButton =
            document.createElement(
                "button"
            );


        openButton.type =
            "button";


        openButton.className =
            "history-item";


        openButton.textContent =
            chat.pinned
            ? `📌 ${chat.title}`
            : chat.title;


        openButton.title =
            chat.title;


        openButton.onclick =
            () => {

                openSavedChat(
                    chat.id
                );
            };


        const menuWrapper =
            document.createElement(
                "div"
            );


        menuWrapper.className =
            "history-menu-wrapper";


        const menuButton =
            document.createElement(
                "button"
            );


        menuButton.type =
            "button";


        menuButton.className =
            "history-menu-button";


        menuButton.textContent =
            "⋯";


        menuButton.title =
            "Chat options";


        const menu =
            document.createElement(
                "div"
            );


        menu.className =
            "history-menu";


        const pinButton =
            document.createElement(
                "button"
            );


        pinButton.type =
            "button";


        pinButton.textContent =
            chat.pinned
            ? "Unpin"
            : "Pin";


        pinButton.onclick =
            async event => {

                event.stopPropagation();

                closeAllChatMenus();

                await togglePinChat(
                    chat.id
                );
            };


        const renameButton =
            document.createElement(
                "button"
            );


        renameButton.type =
            "button";


        renameButton.textContent =
            "Rename";


        renameButton.onclick =
            async event => {

                event.stopPropagation();

                closeAllChatMenus();

                await renameSavedChat(
                    chat.id,
                    chat.title
                );
            };


        const deleteButton =
            document.createElement(
                "button"
            );


        deleteButton.type =
            "button";


        deleteButton.className =
            "danger";


        deleteButton.textContent =
            "Delete";


        deleteButton.onclick =
            async event => {

                event.stopPropagation();

                closeAllChatMenus();

                await deleteSavedChat(
                    chat.id,
                    chat.title
                );
            };


        menu.appendChild(
            pinButton
        );


        menu.appendChild(
            renameButton
        );


        menu.appendChild(
            deleteButton
        );


        menuButton.onclick =
            event => {

                event.stopPropagation();


                const isOpen =
                    menu.classList.contains(
                        "open"
                    );


                closeAllChatMenus();


                if (!isOpen) {

                    menu.classList.add(
                        "open"
                    );
                }
            };


        menuWrapper.appendChild(
            menuButton
        );


        menuWrapper.appendChild(
            menu
        );


        row.appendChild(
            openButton
        );


        row.appendChild(
            menuWrapper
        );


        container.appendChild(
            row
        );
    }


    function closeAllChatMenus() {

        document
            .querySelectorAll(
                ".history-menu.open"
            )
            .forEach(
                menu => {

                    menu.classList.remove(
                        "open"
                    );
                }
            );
    }


    async function togglePinChat(
        chatId
    ) {

        try {

            const response =
                await fetch(
                    `/api/chats/${chatId}/pin`,
                    {
                        method:
                            "POST",

                        credentials:
                            "same-origin"
                    }
                );


            if (!response.ok) {
                return;
            }


            await loadDatabaseChats();


        } catch (error) {

            console.error(
                "Pin error:",
                error
            );
        }
    }


    async function renameSavedChat(
        chatId,
        currentTitle
    ) {

        const newTitle =
            window.prompt(
                "Rename chat:",
                currentTitle
            );


        if (
            newTitle === null
        ) {
            return;
        }


        const cleanTitle =
            newTitle.trim();


        if (!cleanTitle) {
            return;
        }


        const formData =
            new FormData();


        formData.append(
            "title",
            cleanTitle
        );


        try {

            const response =
                await fetch(
                    `/api/chats/${chatId}/rename`,
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
                return;
            }


            await loadDatabaseChats();


            if (
                currentSavedChatId
                === chatId
            ) {

                await openSavedChat(
                    chatId
                );
            }


        } catch (error) {

            console.error(
                "Rename error:",
                error
            );
        }
    }


    async function deleteSavedChat(
        chatId,
        title
    ) {

        const confirmed =
            window.confirm(
                `Delete "${title}"?`
            );


        if (!confirmed) {
            return;
        }


        try {

            const response =
                await fetch(
                    `/api/chats/${chatId}`,
                    {
                        method:
                            "DELETE",

                        credentials:
                            "same-origin"
                    }
                );


            if (!response.ok) {
                return;
            }


            if (
                currentSavedChatId
                === chatId
            ) {

                sessionStorage.removeItem(
                    ACTIVE_CHAT_KEY
                );


                currentSavedChatId =
                    null;


                window.currentSavedChatId =
                    null;


                window.location.href =
                    "/";


                return;
            }


            await loadDatabaseChats();


        } catch (error) {

            console.error(
                "Delete error:",
                error
            );
        }
    }


    /* ========================================================
       END OF PART 1
       DO NOT ADD ANYTHING ELSE YET
    ======================================================== *
        /* ========================================================
       SAVED USER MESSAGE
    ======================================================== */

    function createSavedUserMessage(
        message
    ) {

        const section =
            document.createElement(
                "section"
            );


        section.className =
            "user-block";


        const wrapper =
            document.createElement(
                "div"
            );


        wrapper.className =
            "user-message";


        const label =
            document.createElement(
                "div"
            );


        label.className =
            "user-label";


        label.textContent =
            "You";


        const bubble =
            document.createElement(
                "div"
            );


        bubble.className =
            "user-bubble";


        bubble.textContent =
            message.content || "";


        wrapper.appendChild(
            label
        );


        wrapper.appendChild(
            bubble
        );


        section.appendChild(
            wrapper
        );


        return section;
    }


    /* ========================================================
       SAVED ASSISTANT MESSAGE
    ======================================================== */

    function createSavedAssistantMessage(
        message
    ) {

        const section =
            document.createElement(
                "section"
            );


        section.className =
            "assistant-block";


        const assistantLabel =
            document.createElement(
                "div"
            );


        assistantLabel.className =
            "assistant-label";


        assistantLabel.textContent =
            "FastAPI Assistant";


        const card =
            document.createElement(
                "article"
            );


        card.className =
            "answer-card";


        /* ----------------------------------------------------
           HEADER
        ---------------------------------------------------- */

        const header =
            document.createElement(
                "div"
            );


        header.className =
            "answer-header";


        const methodBox =
            document.createElement(
                "div"
            );


        const smallLabel =
            document.createElement(
                "span"
            );


        smallLabel.className =
            "small-label";


        smallLabel.textContent =
            "Retrieval method";


        const method =
            document.createElement(
                "strong"
            );


        if (
            message.retrieval_method
            === "bm25"
        ) {

            method.textContent =
                "BM25 Keyword Search";

        } else {

            method.textContent =
                "Semantic / Vector Search";
        }


        methodBox.appendChild(
            smallLabel
        );


        methodBox.appendChild(
            method
        );


        header.appendChild(
            methodBox
        );


        /* ----------------------------------------------------
           ANSWER
        ---------------------------------------------------- */

        const answer =
            document.createElement(
                "div"
            );


        answer.className =
            "answer-content";


        answer.innerHTML =
            formatSavedAnswer(
                message.content || ""
            );


        /* ----------------------------------------------------
           TIMINGS
        ---------------------------------------------------- */

        const performance =
            document.createElement(
                "div"
            );


        performance.className =
            "saved-performance-row";


        if (
            message.retrieval_ms
            !== null
            &&
            message.retrieval_ms
            !== undefined
        ) {

            const span =
                document.createElement(
                    "span"
                );


            span.textContent =
                `Retrieval ${Number(
                    message.retrieval_ms
                ).toFixed(1)} ms`;


            performance.appendChild(
                span
            );
        }


        if (
            message.generation_ms
            !== null
            &&
            message.generation_ms
            !== undefined
        ) {

            const span =
                document.createElement(
                    "span"
                );


            span.textContent =
                `Generation ${(
                    Number(
                        message.generation_ms
                    )
                    / 1000
                ).toFixed(2)} s`;


            performance.appendChild(
                span
            );
        }


        if (
            message.total_ms
            !== null
            &&
            message.total_ms
            !== undefined
        ) {

            const span =
                document.createElement(
                    "span"
                );


            span.textContent =
                `Total ${(
                    Number(
                        message.total_ms
                    )
                    / 1000
                ).toFixed(2)} s`;


            performance.appendChild(
                span
            );
        }


        /* ----------------------------------------------------
           SOURCES
        ---------------------------------------------------- */

        const citedSources =
            getCitedSavedSources(
                message
            );


        const sourcesBlock =
            document.createElement(
                "div"
            );


        sourcesBlock.className =
            "sources-block";


        const heading =
            document.createElement(
                "div"
            );


        heading.className =
            "sources-heading";


        const headingTitle =
            document.createElement(
                "strong"
            );


        headingTitle.textContent =
            "Sources";


        const official =
            document.createElement(
                "span"
            );


        official.textContent =
            "Official FastAPI docs";


        heading.appendChild(
            headingTitle
        );


        heading.appendChild(
            official
        );


        sourcesBlock.appendChild(
            heading
        );


        if (
            !citedSources.length
        ) {

            const empty =
                document.createElement(
                    "div"
                );


            empty.className =
                "saved-source-empty";


            empty.textContent =
                "No cited sources.";


            sourcesBlock.appendChild(
                empty
            );

        } else {

            const list =
                document.createElement(
                    "div"
                );


            list.className =
                "saved-source-list";


            citedSources.forEach(
                (
                    source,
                    index
                ) => {

                    const link =
                        document.createElement(
                            "a"
                        );


                    link.className =
                        "saved-source-link";


                    link.target =
                        "_blank";


                    link.rel =
                        "noopener noreferrer";


                    if (
                        source.url
                    ) {

                        link.href =
                            source.url;

                    } else {

                        link.href =
                            "#";


                        link.onclick =
                            event => {

                                event.preventDefault();
                            };
                    }


                    const title =
                        document.createElement(
                            "strong"
                        );


                    const number =
                        source.number
                        ?? index + 1;


                    title.textContent =
                        `Source ${number}: ${
                            source.title
                            || "FastAPI Documentation"
                        }`;


                    const url =
                        document.createElement(
                            "span"
                        );


                    url.textContent =
                        source.url
                        || "FastAPI documentation";


                    link.appendChild(
                        title
                    );


                    link.appendChild(
                        url
                    );


                    list.appendChild(
                        link
                    );
                }
            );


            sourcesBlock.appendChild(
                list
            );
        }


        /* ----------------------------------------------------
           BUILD CARD
        ---------------------------------------------------- */

        card.appendChild(
            header
        );


        card.appendChild(
            answer
        );


        if (
            performance.children.length
        ) {

            card.appendChild(
                performance
            );
        }


        card.appendChild(
            sourcesBlock
        );


        section.appendChild(
            assistantLabel
        );


        section.appendChild(
            card
        );


        return section;
    }


    /* ========================================================
       DISPLAY SAVED CHAT
    ======================================================== */

    function displaySavedChat(
        data
    ) {

        const chatArea =
            document.querySelector(
                ".chat-area"
            );


        if (!chatArea) {
            return;
        }


        chatArea.innerHTML =
            "";


        document.body.classList.remove(
            "empty-chat"
        );


        const chat =
            data.chat || {};


        const title =
            document.createElement(
                "div"
            );


        title.className =
            "saved-chat-title";


        const strong =
            document.createElement(
                "strong"
            );


        strong.textContent =
            chat.title
            || "Saved chat";


        title.appendChild(
            strong
        );


        chatArea.appendChild(
            title
        );


        const messages =
            Array.isArray(
                data.messages
            )
            ? data.messages
            : [];


        messages.forEach(
            message => {

                if (
                    message.role
                    === "user"
                ) {

                    chatArea.appendChild(
                        createSavedUserMessage(
                            message
                        )
                    );

                } else if (
                    message.role
                    === "assistant"
                ) {

                    chatArea.appendChild(
                        createSavedAssistantMessage(
                            message
                        )
                    );
                }
            }
        );


        const topbarTitle =
            document.querySelector(
                ".topbar-title"
            );


        if (topbarTitle) {

            topbarTitle.textContent =
                chat.title
                || "FastAPI Assistant";
        }


        if (
            typeof window.closeSidebar
            === "function"
        ) {

            window.closeSidebar();
        }


        setTimeout(
    () => {
       
            window.scrollTo(
            {
                top: document.documentElement.scrollHeight,
                behavior: "smooth"
            }
        );
    },
    150
);
    }


    /* ========================================================
       OPEN SAVED CHAT
    ======================================================== */

    async function openSavedChat(
        chatId
    ) {

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


            currentSavedChatId =
                chatId;


            window.currentSavedChatId =
                chatId;


            sessionStorage.setItem(
                ACTIVE_CHAT_KEY,
                String(
                    chatId
                )
            );


            displaySavedChat(
                data
            );


        } catch (error) {

            console.error(
                "Open chat error:",
                error
            );
        }
    }


    /* ========================================================
       COPY CODE IN SAVED CHATS
    ======================================================== */

    document.addEventListener(
        "click",
        async event => {

            const button =
                event.target.closest(
                    ".saved-copy-code"
                );


            if (!button) {
                return;
            }


            const code =
                button
                    .closest(
                        ".code-wrapper"
                    )
                    ?.querySelector(
                        "code"
                    );


            if (!code) {
                return;
            }


            try {

                await navigator
                    .clipboard
                    .writeText(
                        code.innerText
                    );


                const original =
                    button.textContent;


                button.textContent =
                    "Copied";


                setTimeout(
                    () => {

                        button.textContent =
                            original;

                    },
                    1000
                );


            } catch (error) {

                console.error(
                    "Copy code error:",
                    error
                );
            }
        }
    );


    /* ========================================================
       CLOSE THREE-DOT MENUS
    ======================================================== */

    document.addEventListener(
        "click",
        event => {

            if (
                !event.target.closest(
                    ".history-menu-wrapper"
                )
            ) {

                closeAllChatMenus();
            }
        }
    );


    /* ========================================================
       RESTORE CURRENT CHAT ID
    ======================================================== */

    const storedChatId =
        sessionStorage.getItem(
            ACTIVE_CHAT_KEY
        );


    if (
        storedChatId
    ) {

        currentSavedChatId =
            Number(
                storedChatId
            );


        window.currentSavedChatId =
            currentSavedChatId;
    }


    /* ========================================================
       SEND ACTIVE CHAT ID WITH FOLLOW-UP QUESTION
    ======================================================== */

    document.addEventListener(
        "submit",
        event => {

            const form =
                event.target;


            if (
                !form
                ||
                form.id
                !== "question-form"
            ) {
                return;
            }


            const activeChatId =
                sessionStorage.getItem(
                    ACTIVE_CHAT_KEY
                );


            if (
                !activeChatId
            ) {
                return;
            }


            let hiddenInput =
                form.querySelector(
                    'input[name="chat_id"]'
                );


            if (
                !hiddenInput
            ) {

                hiddenInput =
                    document.createElement(
                        "input"
                    );


                hiddenInput.type =
                    "hidden";


                hiddenInput.name =
                    "chat_id";


                form.appendChild(
                    hiddenInput
                );
            }


            hiddenInput.value =
                activeChatId;
        }
    );


    /* ========================================================
       RESTORE FULL MULTI-TURN CHAT AFTER FOLLOW-UP
    ======================================================== */

    async function restoreConversation() {

        /*
         * An empty page means New Chat.
         * Do not reconnect it to an old chat.
         */

        if (
            document.body.classList.contains(
                "empty-chat"
            )
        ) {

            sessionStorage.removeItem(
                ACTIVE_CHAT_KEY
            );


            currentSavedChatId =
                null;


            window.currentSavedChatId =
                null;


            return;
        }


        const chatArea =
            document.querySelector(
                ".chat-area"
            );


        if (!chatArea) {
            return;
        }


        const savedId =
            sessionStorage.getItem(
                ACTIVE_CHAT_KEY
            );


        if (!savedId) {
            return;
        }


        const chatId =
            Number(
                savedId
            );


        if (
            !Number.isInteger(
                chatId
            )
            ||
            chatId <= 0
        ) {

            sessionStorage.removeItem(
                ACTIVE_CHAT_KEY
            );


            return;
        }


        await openSavedChat(
            chatId
        );
    }


    /* ========================================================
       START
    ======================================================== */

    document.addEventListener(
        "DOMContentLoaded",
        async () => {

            await loadAccountStatus();


            await restoreConversation();
        }
    );


    /* ========================================================
       EXPOSE REQUIRED FUNCTIONS
    ======================================================== */

    window.openSavedChat =
        openSavedChat;


    window.loadDatabaseChats =
        loadDatabaseChats;


    window.closeAllChatMenus =
        closeAllChatMenus;


    /* ========================================================
       END
    ======================================================== */

})();