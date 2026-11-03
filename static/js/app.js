/* ============================================================
   HISTORY MENU STYLES
   Injected directly so no separate history.css is required.
============================================================ */

(function injectHistoryStyles() {

    const oldStyle =
        document.getElementById(
            "history-menu-styles"
        );

    if (oldStyle) {
        oldStyle.remove();
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

            border: none !important;
            background: transparent !important;
        }


        /* =====================================================
           QUESTION
           hello                                  ⋯
        ===================================================== */

        .history-row .history-item {
            flex: 1 1 auto !important;

            min-width: 0 !important;

            width: auto !important;

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


        /* =====================================================
           THREE DOT BUTTON
        ===================================================== */

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


        /* =====================================================
           POPUP
        ===================================================== */

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

            border-radius:
                10px !important;

            background:
                var(--surface) !important;

            box-shadow:
                0 14px 34px
                rgba(0, 0, 0, 0.35) !important;
        }


        .history-menu.open {
            display: flex !important;

            flex-direction:
                column !important;

            gap: 1px !important;
        }


        /* =====================================================
           PIN / RENAME / DELETE
        ===================================================== */

        .history-menu button {
            display: block !important;

            width: 100% !important;

            height: auto !important;

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


        /* =====================================================
           DARK MODE
        ===================================================== */

        body[data-theme="dark"]
        .history-menu {
            background:
                #1d1f27 !important;

            border-color:
                rgba(
                    255,
                    255,
                    255,
                    0.10
                ) !important;

            box-shadow:
                0 14px 34px
                rgba(
                    0,
                    0,
                    0,
                    0.55
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
        .history-menu-button:hover {
            color:
                #ffffff !important;

            background:
                #242731 !important;
        }


        body[data-theme="dark"]
        .history-menu button.danger {
            color:
                #ff7d8d !important;
        }


        /* =====================================================
           LIGHT MODE
        ===================================================== */

        body[data-theme="light"]
        .history-menu {
            background:
                #ffffff !important;

            border-color:
                rgba(
                    24,
                    24,
                    27,
                    0.12
                ) !important;

            box-shadow:
                0 14px 30px
                rgba(
                    0,
                    0,
                    0,
                    0.15
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
        .history-menu-button:hover {
            color:
                #18181b !important;

            background:
                #ececf0 !important;
        }


        body[data-theme="light"]
        .history-menu button.danger {
            color:
                #d94d5d !important;
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


/* ============================================================
   INITIALS
============================================================ */

function getInitials(name) {

    if (!name) {
        return "U";
    }

    const parts =
        name
            .trim()
            .split(/\s+/)
            .filter(Boolean);

    if (!parts.length) {
        return "U";
    }

    if (parts.length === 1) {

        return parts[0]
            .charAt(0)
            .toUpperCase();
    }

    return (
        parts[0].charAt(0)
        +
        parts[1].charAt(0)
    ).toUpperCase();
}


/* ============================================================
   LOGOUT
============================================================ */

async function logoutAccount() {

    try {

        const response =
            await fetch(
                "/logout",
                {
                    method: "POST",
                    credentials:
                        "same-origin"
                }
            );

        if (!response.ok) {
            return;
        }

        window.location.href =
            "/";

    } catch (error) {

        console.error(
            "Logout failed:",
            error
        );
    }
}


/* ============================================================
   ACCOUNT
============================================================ */

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


        const profileAvatar =
            document.querySelector(
                ".profile-avatar"
            );

        const profileName =
            document.querySelector(
                ".profile-copy strong"
            );

        const profileStatus =
            document.querySelector(
                ".profile-copy span"
            );


        if (profileAvatar) {

            profileAvatar.textContent =
                getInitials(
                    user.name
                );
        }


        if (profileName) {

            profileName.textContent =
                user.name;
        }


        if (profileStatus) {

            profileStatus.textContent =
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


/* ============================================================
   LOAD CHATS
============================================================ */

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


        if (!data.chats.length) {

            container.innerHTML =
                '<div class="history-empty">No recent chats yet.</div>';

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


/* ============================================================
   CHAT ROW
============================================================ */

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


    /* QUESTION */

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


    /* THREE DOT WRAPPER */

    const menuWrapper =
        document.createElement(
            "div"
        );

    menuWrapper.className =
        "history-menu-wrapper";


    /* THREE DOT BUTTON */

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


    /* POPUP */

    const menu =
        document.createElement(
            "div"
        );

    menu.className =
        "history-menu";


    /* PIN */

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


    /* RENAME */

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


    /* DELETE */

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


            const alreadyOpen =
                menu.classList.contains(
                    "open"
                );


            closeAllChatMenus();


            if (!alreadyOpen) {

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


/* ============================================================
   CLOSE MENU
============================================================ */

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


/* ============================================================
   PIN
============================================================ */

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


/* ============================================================
   RENAME
============================================================ */

async function renameSavedChat(
    chatId,
    currentTitle
) {

    const newTitle =
        window.prompt(
            "Rename chat:",
            currentTitle
        );


    if (newTitle === null) {
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

    } catch (error) {

        console.error(
            "Rename error:",
            error
        );
    }
}


/* ============================================================
   DELETE
============================================================ */

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


        await loadDatabaseChats();

    } catch (error) {

        console.error(
            "Delete error:",
            error
        );
    }
}


/* ============================================================
   OPEN CHAT
============================================================ */

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


        console.log(
            "Saved chat:",
            data
        );

    } catch (error) {

        console.error(
            "Open chat error:",
            error
        );
    }
}


/* ============================================================
   EVENTS
============================================================ */

document.addEventListener(
    "click",
    closeAllChatMenus
);


document.addEventListener(
    "DOMContentLoaded",
    loadAccountStatus
);
