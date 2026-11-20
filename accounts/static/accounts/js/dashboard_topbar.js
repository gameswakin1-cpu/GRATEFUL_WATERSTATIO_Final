(function () {
    const bell = document.querySelector('[data-dashboard-notification-bell]');
    const panel = document.querySelector('[data-dashboard-notification-panel]');
    const settingsToggle = document.querySelector('[data-dashboard-settings-toggle]');
    const settingsMenu = document.querySelector('[data-dashboard-settings-menu]');

    function positionMobilePopup(toggle, popup) {
        if (window.innerWidth > 520) {
            popup.style.removeProperty('top');
            return;
        }

        const toggleRect = toggle.getBoundingClientRect();
        const popupHeight = popup.getBoundingClientRect().height;
        const top = Math.max(
            12,
            Math.min(toggleRect.bottom + 8, window.innerHeight - popupHeight - 12)
        );
        popup.style.top = `${top}px`;
    }

    if (settingsToggle && settingsMenu) {
        settingsToggle.addEventListener('click', event => {
            event.stopPropagation();
            const isOpen = !settingsMenu.hidden;
            settingsMenu.hidden = isOpen;
            settingsToggle.setAttribute('aria-expanded', String(!isOpen));
            if (!isOpen) positionMobilePopup(settingsToggle, settingsMenu);
        });
        document.addEventListener('click', event => {
            if (!settingsMenu.hidden && !settingsMenu.contains(event.target) && event.target !== settingsToggle) {
                settingsMenu.hidden = true;
                settingsToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    if (!bell || !panel) return;

    const list = panel.querySelector('[data-dashboard-notification-list]');
    const countBadge = bell.querySelector('[data-dashboard-notification-count]');
    const markAllButton = panel.querySelector('[data-dashboard-mark-all-read]');
    const storageKey = `gws-dashboard-notifications-${bell.dataset.userKey}`;
    const csrfToken = decodeURIComponent(
        (document.cookie.match(/(?:^|; )csrftoken=([^;]+)/) || [])[1] || ''
    );
    const syncKey = `${storageKey}-sync`;
    const notificationChannel = 'BroadcastChannel' in window
        ? new BroadcastChannel(storageKey)
        : null;
    let serverItems = [];
    let serverUnreadCount = 0;
    let serverReadAllAt = 0;
    let notificationStateLoaded = false;

    function readLiveItems() {
        try {
            const items = JSON.parse(localStorage.getItem(storageKey) || '[]');
            return Array.isArray(items) ? items : [];
        } catch (error) {
            console.error('Unable to read dashboard notifications:', error);
            return [];
        }
    }

    function writeLiveItems(items) {
        try {
            localStorage.setItem(storageKey, JSON.stringify(items.slice(0, 30)));
        } catch (error) {
            console.error('Unable to save dashboard notifications:', error);
        }
    }

    function broadcastReadState() {
        const message = { type: 'notifications-read', timestamp: Date.now() };
        if (notificationChannel) notificationChannel.postMessage(message);
        try {
            localStorage.setItem(syncKey, JSON.stringify(message));
        } catch (error) {
            console.error('Unable to broadcast notification state:', error);
        }
    }

    function applyReadState() {
        serverItems = serverItems.map(item => ({ ...item, is_read: true }));
        serverUnreadCount = 0;
        writeLiveItems(readLiveItems().map(item => ({ ...item, is_read: true })));
        render();
    }

    function importFlashMessages() {
        const container = document.querySelector('[data-dashboard-flash-messages]');
        if (!container) return;
        const items = readLiveItems();
        const timestamp = new Date().toISOString();
        container.querySelectorAll('[data-flash-message]').forEach((message, index) => {
            items.unshift({
                id: `flash-${Date.now()}-${index}`,
                source: 'live',
                title: message.dataset.flashTags.includes('success') ? 'Success' : 'Notice',
                description: message.dataset.flashMessage,
                category: 'system',
                severity: message.dataset.flashTags.includes('error') ? 'warning' : 'info',
                target_url: '',
                is_read: false,
                created_at: timestamp,
            });
        });
        writeLiveItems(items);
        container.remove();
    }

    function safeTargetUrl(value) {
        if (!value) return '#';
        try {
            const target = new URL(value, window.location.origin);
            return target.origin === window.location.origin ? target.href : '#';
        } catch (error) {
            return '#';
        }
    }

    function addText(parent, tag, className, text) {
        const element = document.createElement(tag);
        if (className) element.className = className;
        element.textContent = text || '';
        parent.appendChild(element);
        return element;
    }

    function render() {
        const liveItems = readLiveItems();
        const visibleLiveItems = liveItems.map(item => ({
            ...item,
            is_read: item.is_read || (
                serverReadAllAt > 0 &&
                Date.parse(item.created_at) <= serverReadAllAt
            ),
        }));
        const items = [...visibleLiveItems, ...serverItems]
            .sort((left, right) => new Date(right.created_at) - new Date(left.created_at))
            .slice(0, 20);
        const liveUnread = notificationStateLoaded
            ? visibleLiveItems.filter(item => !item.is_read).length
            : 0;
        const unreadCount = serverUnreadCount + liveUnread;

        if (unreadCount > 0) {
            countBadge.textContent = unreadCount > 99 ? '99+' : String(unreadCount);
            countBadge.hidden = false;
            countBadge.style.display = 'inline-flex';
        } else {
            countBadge.textContent = '';
            countBadge.hidden = true;
            countBadge.style.display = 'none';
        }
        list.replaceChildren();

        if (!items.length) {
            addText(list, 'p', 'dashboard-notification-empty', 'You’re all caught up.');
            return;
        }

        items.forEach(item => {
            const anchor = document.createElement('a');
            anchor.className = `dashboard-notification-item${item.is_read ? '' : ' is-unread'}`;
            anchor.href = safeTargetUrl(item.target_url);
            anchor.dataset.notificationId = String(item.id);
            anchor.dataset.notificationSource = item.source || 'server';
            const dot = document.createElement('span');
            dot.className = 'dashboard-notification-dot';
            anchor.appendChild(dot);

            const copy = document.createElement('span');
            copy.className = 'dashboard-notification-copy';
            addText(copy, 'strong', '', item.title);
            addText(copy, 'span', '', item.description);
            addText(copy, 'span', 'dashboard-notification-category', item.category_label || '');
            const timestamp = new Date(item.created_at);
            addText(copy, 'time', '', Number.isNaN(timestamp.getTime()) ? '' : timestamp.toLocaleString());
            anchor.appendChild(copy);

            anchor.addEventListener('click', event => {
                if (anchor.getAttribute('href') === '#') {
                    event.preventDefault();
                    if (item.source === 'live') {
                        const updatedItems = readLiveItems().map(liveItem =>
                            liveItem.id === item.id ? { ...liveItem, is_read: true } : liveItem
                        );
                        writeLiveItems(updatedItems);
                        render();
                    }
                    return;
                }
                if (item.source === 'live') {
                    event.preventDefault();
                    const updatedItems = readLiveItems().map(liveItem =>
                        liveItem.id === item.id ? { ...liveItem, is_read: true } : liveItem
                    );
                    writeLiveItems(updatedItems);
                    render();
                    window.location.href = anchor.href;
                    return;
                }
                if (/^\d+$/.test(String(item.id))) {
                    event.preventDefault();
                    fetch(`${panel.dataset.notificationDetailUrl}${item.id}/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken,
                        },
                        body: JSON.stringify({ action: 'read' }),
                    }).then(response => {
                        if (!response.ok) throw new Error('Could not mark notification as read.');
                        broadcastReadState();
                        window.location.href = anchor.href;
                    }).catch(error => console.error('Unable to update notification:', error));
                }
            });
            list.appendChild(anchor);
        });
    }

    function loadNotifications() {
        fetch(bell.dataset.notificationsApi, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(response => {
                if (!response.ok) throw new Error('Could not load notifications.');
                return response.json();
            })
            .then(data => {
                serverItems = Array.isArray(data.notifications) ? data.notifications : [];
                serverUnreadCount = Number(data.unread_count || 0);
                serverReadAllAt = data.read_all_at ? Date.parse(data.read_all_at) : 0;
                notificationStateLoaded = true;
                render();
            })
            .catch(error => {
                console.error('Unable to load dashboard notifications:', error);
                if (!list.children.length) {
                    addText(list, 'p', 'dashboard-notification-empty', 'Notifications are temporarily unavailable.');
                }
            });
    }

    markAllButton.addEventListener('click', () => {
        markAllButton.disabled = true;
        fetch(markAllButton.dataset.markAllUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ action: 'read' }),
        }).then(response => {
            if (!response.ok) throw new Error('Could not mark notifications as read.');
            return response.json();
        }).then(() => {
            applyReadState();
            broadcastReadState();
        }).catch(error => {
            console.error('Unable to mark all notifications as read:', error);
        }).finally(() => {
            markAllButton.disabled = false;
        });
    });

    bell.addEventListener('click', () => {
        const opening = panel.hidden;
        panel.hidden = !opening;
        bell.setAttribute('aria-expanded', String(opening));
        if (opening) {
            positionMobilePopup(bell, panel);
            loadNotifications();
        }
    });

    document.addEventListener('click', event => {
        if (!panel.hidden && !panel.contains(event.target) && !bell.contains(event.target)) {
            panel.hidden = true;
            bell.setAttribute('aria-expanded', 'false');
        }
    });

    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && !panel.hidden) {
            panel.hidden = true;
            bell.setAttribute('aria-expanded', 'false');
            bell.focus();
        }
    });

    window.addEventListener('resize', () => {
        if (settingsMenu && !settingsMenu.hidden) {
            positionMobilePopup(settingsToggle, settingsMenu);
        }
        if (!panel.hidden) positionMobilePopup(bell, panel);
    });

    window.addEventListener('storage', event => {
        if (event.key === syncKey) {
            applyReadState();
        } else if (event.key === storageKey) {
            render();
        }
    });

    if (notificationChannel) {
        notificationChannel.addEventListener('message', event => {
            if (event.data && event.data.type === 'notifications-read') {
                applyReadState();
            }
        });
    }

    window.addEventListener('focus', loadNotifications);
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) loadNotifications();
    });

    document.addEventListener('gws:dashboard-notification', event => {
        const incoming = event.detail;
        if (!incoming || !incoming.id) return;
        const items = readLiveItems().filter(item => item.id !== incoming.id);
        items.unshift({ ...incoming, source: 'live', is_read: false });
        writeLiveItems(items);
        render();
    });

    importFlashMessages();
    render();
    loadNotifications();
    window.setInterval(loadNotifications, 5000);
}());
