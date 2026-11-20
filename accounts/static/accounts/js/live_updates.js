(function () {
    'use strict';

    if (!document.body) return;

    function openAccountProfileModal(profileUrl, trigger) {
        if (document.getElementById('gws-profile-modal')) return;

        const modal = document.createElement('div');
        modal.id = 'gws-profile-modal';
        modal.setAttribute('role', 'presentation');
        modal.style.cssText = [
            'position:fixed',
            'inset:0',
            'z-index:10000',
            'display:grid',
            'place-items:center',
            'padding:20px',
            'background:rgba(9,24,42,.58)',
            'backdrop-filter:blur(7px)',
            '-webkit-backdrop-filter:blur(7px)'
        ].join(';');

        const panel = document.createElement('section');
        panel.setAttribute('role', 'dialog');
        panel.setAttribute('aria-modal', 'true');
        panel.setAttribute('aria-labelledby', 'gws-profile-modal-title');
        panel.style.cssText = [
            'display:flex',
            'flex-direction:column',
            'width:min(900px,100%)',
            'height:min(850px,92vh)',
            'overflow:hidden',
            'border:1px solid rgba(255,255,255,.7)',
            'border-radius:22px',
            'background:#f4f8fc',
            'box-shadow:0 28px 90px rgba(0,0,0,.3)'
        ].join(';');

        const titlebar = document.createElement('header');
        titlebar.style.cssText = [
            'display:flex',
            'align-items:center',
            'justify-content:space-between',
            'gap:16px',
            'padding:14px 20px',
            'background:#fff',
            'border-bottom:1px solid #e5edf5',
            'font:700 15px/1.3 Segoe UI,sans-serif',
            'color:#19344d'
        ].join(';');

        const title = document.createElement('span');
        title.id = 'gws-profile-modal-title';
        title.textContent = 'My Profile';

        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.setAttribute('aria-label', 'Close profile');
        closeButton.innerHTML = '&times;';
        closeButton.style.cssText = [
            'display:grid',
            'place-items:center',
            'width:36px',
            'height:36px',
            'border:0',
            'border-radius:50%',
            'background:#edf4fa',
            'color:#47627b',
            'font:400 26px/1 Segoe UI,sans-serif',
            'cursor:pointer'
        ].join(';');

        const frame = document.createElement('iframe');
        frame.title = 'Profile';
        frame.src = `${profileUrl}${profileUrl.includes('?') ? '&' : '?'}floating=1`;
        frame.style.cssText = 'width:100%;flex:1;border:0;background:#f4f8fc;';
        frame.addEventListener('load', () => {
            frame.contentWindow.addEventListener('keydown', onKeydown);
        });

        let previousOverflow = document.body.style.overflow;
        const close = () => {
            document.removeEventListener('keydown', onKeydown);
            document.body.style.overflow = previousOverflow;
            modal.remove();
            trigger?.focus();
        };
        const onKeydown = event => {
            if (event.key === 'Escape') close();
        };

        closeButton.addEventListener('click', close);
        modal.addEventListener('click', event => {
            if (event.target === modal) close();
        });
        document.addEventListener('keydown', onKeydown);

        titlebar.append(title, closeButton);
        panel.append(titlebar, frame);
        modal.appendChild(panel);
        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';
        closeButton.focus();
    }

    function openSalesReceiptModal(receiptUrl, trigger) {
        if (document.getElementById('gws-receipt-modal')) return;

        if (!document.getElementById('gws-receipt-modal-styles')) {
            const styles = document.createElement('style');
            styles.id = 'gws-receipt-modal-styles';
            styles.textContent = `
                .gws-receipt-header{padding:1.25rem 1.2rem 1.15rem;background:linear-gradient(145deg,#1598d0,#1485be);color:#fff;text-align:center}
                .gws-receipt-header h2{display:flex;align-items:center;justify-content:center;margin:0;color:#fff;font-size:.95rem;font-weight:700;letter-spacing:.7px;line-height:1.2;text-transform:uppercase}
                .gws-receipt-header img{width:30px;height:30px;padding:3px;margin-right:.55rem;border-radius:8px;background:rgba(255,255,255,.2);object-fit:contain}
                .gws-receipt-address{max-width:240px;margin:.25rem auto 0;color:rgba(255,255,255,.9);font-size:.62rem;line-height:1.3}
                .gws-receipt-date{margin:.35rem 0 0;color:rgba(255,255,255,.85);font-size:.65rem}
                .gws-receipt-time{margin:.15rem 0 0;color:rgba(255,255,255,.85);font-size:.65rem}
                .gws-receipt-summary{display:flex;align-items:center;justify-content:space-between;gap:.75rem;padding:.8rem 1.15rem;background:#f8fbff;border-bottom:1px solid #e2e8f0}
                .gws-receipt-summary strong{display:block;margin-top:.2rem;color:#075985;font-size:.95rem}
                .gws-receipt-label,.gws-receipt-section-title{display:block;color:#64748b;font-size:.62rem;font-weight:800;letter-spacing:.8px}
                .gws-receipt-section-title{padding:.85rem 1.15rem .3rem}
                .gws-receipt-status{padding:.38rem .65rem;border-radius:999px;background:#dcfce7;color:#15803d;font-size:.65rem;font-weight:800;white-space:nowrap}
                .gws-receipt-items{padding:.2rem 1.15rem .55rem}
                .gws-receipt-item{display:flex;justify-content:space-between;gap:.55rem;padding:.55rem 0;border-bottom:1px solid #edf2f7;color:#334155;font-size:.72rem;line-height:1.3}
                .gws-receipt-item-left{display:flex;align-items:flex-start;gap:.55rem}
                .gws-receipt-qty{min-width:1.25rem;padding:2px 6px;border-radius:5px;background:#e0f2fe;color:#0369a1;text-align:center;font-size:.68rem;font-weight:700}
                .gws-receipt-fee,.gws-receipt-discount{display:flex;justify-content:space-between;padding:.62rem 1.15rem;color:#475569;font-size:.72rem}
                .gws-receipt-discount{color:#15803d}
                .gws-receipt-total{display:flex;justify-content:space-between;align-items:center;padding:.85rem 1.15rem;border-top:1px solid #dbeafe;background:#f0f9ff;color:#075985;font-size:1.05rem;font-weight:700}
                .gws-receipt-total span:first-child{color:#64748b;font-size:.7rem;font-weight:600}
                .gws-receipt-info{display:flex;justify-content:space-between;gap:.75rem;padding:.62rem 1.15rem;border-bottom:1px solid #edf2f7;color:#64748b;font-size:.72rem}
                .gws-receipt-info strong{color:#1e293b;text-align:right}
                .gws-receipt-actions{display:flex;gap:.5rem;justify-content:center;padding:.8rem 1.15rem .95rem;border-top:1px solid #e2e8f0}
                .gws-receipt-actions button{flex:1;padding:.62rem .75rem;border-radius:8px;font-size:.72rem;font-weight:700;cursor:pointer}
                .gws-receipt-download{border:0;background:#1598d0;color:#fff}
                .gws-receipt-close{border:1px solid #dbe3ed;background:#fff;color:#334155}
                @media print{
                    body.gws-printing-receipt>*:not(#gws-receipt-modal){display:none!important}
                    body.gws-printing-receipt #gws-receipt-modal{position:absolute!important;inset:0!important;display:block!important;padding:0!important;background:#fff!important}
                    body.gws-printing-receipt #gws-receipt-modal .gws-receipt-content{width:80mm!important;height:auto!important;max-height:none!important;margin:0 auto!important;overflow:visible!important;box-shadow:none!important}
                    body.gws-printing-receipt #gws-receipt-modal .gws-receipt-actions{display:none!important}
                }
            `;
            document.head.appendChild(styles);
        }

        const modal = document.createElement('div');
        modal.id = 'gws-receipt-modal';
        modal.setAttribute('role', 'presentation');
        modal.style.cssText = [
            'position:fixed',
            'inset:0',
            'z-index:10000',
            'display:flex',
            'align-items:center',
            'justify-content:center',
            'padding:16px',
            'background:rgba(15,23,42,.5)',
            'backdrop-filter:blur(4px)',
            '-webkit-backdrop-filter:blur(4px)'
        ].join(';');

        const content = document.createElement('div');
        content.className = 'gws-receipt-content';
        content.setAttribute('role', 'dialog');
        content.setAttribute('aria-modal', 'true');
        content.setAttribute('aria-label', 'Sales receipt');
        content.style.cssText = [
            'width:min(330px,calc(100vw - 32px))',
            'height:auto',
            'max-height:calc(100vh - 32px)',
            'max-height:calc(100dvh - 32px)',
            'box-sizing:border-box',
            'flex:0 0 auto',
            'overflow:auto',
            'border-radius:16px',
            'background:#fff',
            'box-shadow:0 24px 70px rgba(15,23,42,.28)',
            'font:14px Arial,sans-serif',
            'color:#334155'
        ].join(';');
        content.innerHTML = '<div style="padding:32px;text-align:center;color:#64748b">Loading receipt…</div>';

        const previousOverflow = document.body.style.overflow;
        const previousPaddingRight = document.body.style.paddingRight;
        const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
        const close = () => {
            document.removeEventListener('keydown', onKeydown);
            document.body.classList.remove('gws-printing-receipt');
            document.body.style.overflow = previousOverflow;
            document.body.style.paddingRight = previousPaddingRight;
            modal.remove();
            trigger?.focus();
        };
        const onKeydown = event => {
            if (event.key === 'Escape') close();
        };
        modal.addEventListener('click', event => {
            if (event.target === modal) close();
        });
        document.addEventListener('keydown', onKeydown);
        document.body.appendChild(modal);
        modal.appendChild(content);
        if (scrollbarWidth > 0) {
            document.body.style.paddingRight = `${scrollbarWidth}px`;
        }
        document.body.style.overflow = 'hidden';

        const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[character]);
        const money = value => Number(value || 0).toLocaleString('en-PH', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        const logoUrl = '/static/accounts/images/for%20login%20image.png';
        const stationAddress = 'BLK 19 LOT 1 PHASE 1 ST.LOUIE VILLAGE ADMIRAL TALON 3, Las Piñas City, 1747';

        fetch(receiptUrl, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
            .then(response => {
                if (!response.ok) throw new Error(`Receipt request failed (${response.status})`);
                return response.json();
            })
            .then(data => {
                if (data.error) throw new Error(data.error);
                const items = Array.isArray(data.items) ? data.items : [];
                const receiptDate = data.created_at
                    ? new Date(data.created_at).toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    })
                    : '—';
                const receiptTime = data.created_at
                    ? new Date(data.created_at).toLocaleTimeString('en-US')
                    : '—';
                const transactionDate = data.delivered_at || data.created_at
                    ? new Date(data.delivered_at || data.created_at).toLocaleString()
                    : '—';
                const transactionDateLabel = data.delivered_at ? 'Delivered At' : 'Date & Time';
                content.innerHTML = `
                    <div class="gws-receipt-header">
                        <h2><img src="${logoUrl}" alt="">Grateful Water Station</h2>
                        <div class="gws-receipt-address">${stationAddress}</div>
                        <div class="gws-receipt-date">${escapeHtml(receiptDate)}</div>
                        <div class="gws-receipt-time">${escapeHtml(receiptTime)}</div>
                    </div>
                    <div class="gws-receipt-summary">
                        <div><span class="gws-receipt-label">RECEIPT NUMBER</span><strong>${escapeHtml(data.receipt_number)}</strong></div>
                        <span class="gws-receipt-status">${escapeHtml(data.status_display)}</span>
                    </div>
                    <div class="gws-receipt-section-title">ORDER ITEMS</div>
                    <div class="gws-receipt-items">
                        ${items.length ? items.map(item => `
                            <div class="gws-receipt-item">
                                <div class="gws-receipt-item-left"><span class="gws-receipt-qty">${escapeHtml(item.quantity)}</span><span>${escapeHtml(item.product_name)}</span></div>
                                <span>₱${money(item.subtotal)}</span>
                            </div>
                        `).join('') : '<div class="gws-receipt-item">No items</div>'}
                    </div>
                    ${Number(data.discount || 0) > 0 ? `<div class="gws-receipt-discount"><span>Discount</span><span>-₱${money(data.discount)}</span></div>` : ''}
                    ${Number(data.delivery_fee || 0) > 0 ? `<div class="gws-receipt-fee"><span>Delivery Fee</span><span>₱${money(data.delivery_fee)}</span></div>` : ''}
                    <div class="gws-receipt-total"><span>TOTAL</span><span>₱${money(data.total_amount)}</span></div>
                    <div class="gws-receipt-section-title">TRANSACTION DETAILS</div>
                    <div class="gws-receipt-info"><span>Customer</span><strong>${escapeHtml(data.customer_name)}</strong></div>
                    <div class="gws-receipt-info"><span>Payment Method</span><strong>${escapeHtml(data.payment_method_display)}</strong></div>
                    <div class="gws-receipt-info"><span>${escapeHtml(transactionDateLabel)}</span><strong>${escapeHtml(transactionDate)}</strong></div>
                    <div class="gws-receipt-actions">
                        <button type="button" class="gws-receipt-download">Download PDF</button>
                        <button type="button" class="gws-receipt-close">Close</button>
                    </div>`;

                content.querySelector('.gws-receipt-close').addEventListener('click', close);
                content.querySelector('.gws-receipt-download').addEventListener('click', () => {
                    if (typeof window.html2pdf === 'function') {
                        const copy = content.cloneNode(true);
                        copy.querySelector('.gws-receipt-actions')?.remove();
                        window.html2pdf().set({
                            margin: 2,
                            filename: `receipt_${data.receipt_number || 'sale'}.pdf`,
                            image: {type: 'jpeg', quality: .98},
                            html2canvas: {scale: 2, useCORS: true},
                            jsPDF: {unit: 'mm', format: [80, 180], orientation: 'portrait'}
                        }).from(copy).save();
                        return;
                    }
                    document.body.classList.add('gws-printing-receipt');
                    window.print();
                    window.addEventListener('afterprint', () => {
                        document.body.classList.remove('gws-printing-receipt');
                    }, {once: true});
                });
            })
            .catch(error => {
                console.error('Unable to load sales receipt:', error);
                content.innerHTML = `<div style="padding:24px;color:#b91c1c;text-align:center">${escapeHtml(error.message || 'Unable to load receipt.')}</div><div style="padding:0 24px 24px"><button type="button" class="gws-receipt-close" style="width:100%;padding:10px;border:1px solid #dbe3ed;border-radius:8px;background:white;cursor:pointer">Close</button></div>`;
                content.querySelector('.gws-receipt-close').addEventListener('click', close);
            });
    }

    document.addEventListener('click', event => {
        const salesReceiptButton = event.target.closest('[data-sales-receipt-url]');
        if (salesReceiptButton) {
            event.preventDefault();
            openSalesReceiptModal(salesReceiptButton.dataset.salesReceiptUrl, salesReceiptButton);
            return;
        }

        const profileLink = event.target.closest('a[href]');
        if (!profileLink) return;

        const profileUrl = new URL(profileLink.href, window.location.origin);
        const isProfileLink = /\/account\/profile\/?$/.test(profileUrl.pathname);
        const isReceiptLink = /\/pos\/sales\/\d+\/receipt\/?$/.test(profileUrl.pathname);
        if (!isProfileLink && !isReceiptLink) return;
        if (isProfileLink && profileLink.hasAttribute('data-standalone-profile')) return;
        if (new URLSearchParams(window.location.search).get('floating') === '1') return;

        event.preventDefault();
        if (isProfileLink) {
            openAccountProfileModal(profileUrl.href, profileLink);
        } else {
            openSalesReceiptModal(profileUrl.href, profileLink);
        }
    });

    function keepCurrentNavigationActive() {
        const sidebarLinks = document.querySelector('.sidebar .nav-links');
        const staffDashboardLink = sidebarLinks?.querySelector(
            'a[href*="/accounts/staff/dashboard"]'
        );
        const profileLink = sidebarLinks?.querySelector(
            'a[href*="/accounts/account/profile"]'
        );
        const logoutItem = sidebarLinks?.querySelector(
            'a[href*="/accounts/logout"]'
        )?.closest('li');
        if (staffDashboardLink && profileLink && logoutItem) {
            logoutItem.parentElement.insertBefore(profileLink.closest('li'), logoutItem);
        }

        const currentPath = window.location.pathname.replace(/\/+$/, '') || '/';
        document.querySelectorAll('.nav-links a[href]').forEach(link => {
            const linkUrl = new URL(link.href, window.location.origin);
            const linkPath = linkUrl.pathname.replace(/\/+$/, '') || '/';
            if (linkPath === currentPath && !link.classList.contains('nav-dropdown-toggle')) {
                link.classList.add('active');
                const dropdown = link.closest('.nav-dropdown');
                if (dropdown) dropdown.classList.add('active');
            }
        });
        const currentLink = document.querySelector(`.nav-links a[href="${window.location.pathname}"]`);
        if (currentLink) {
            const dropdown = currentLink.closest('.nav-dropdown');
            if (dropdown) {
                dropdown.classList.add('active');
                dropdown.querySelector('.nav-dropdown-toggle').classList.add('active');
            }
        }
    }

    document.addEventListener('DOMContentLoaded', keepCurrentNavigationActive);

    let previousScrollY = window.scrollY;
    let accumulatedScrollDelta = 0;
    let scrollUpdateQueued = false;

    function updateMenuToggleVisibility() {
        const menuToggle = document.querySelector('.menu-toggle');
        const sidebar = document.querySelector('.sidebar');
        const currentScrollY = window.scrollY;

        if (!menuToggle) {
            previousScrollY = currentScrollY;
            accumulatedScrollDelta = 0;
            scrollUpdateQueued = false;
            return;
        }

        if (window.innerWidth > 768 || currentScrollY <= 24 || sidebar?.classList.contains('active')) {
            menuToggle.classList.remove('scroll-hidden');
            accumulatedScrollDelta = 0;
        } else {
            const scrollDelta = currentScrollY - previousScrollY;
            accumulatedScrollDelta = scrollDelta > 0
                ? Math.max(0, accumulatedScrollDelta) + scrollDelta
                : Math.min(0, accumulatedScrollDelta) + scrollDelta;

            if (accumulatedScrollDelta > 8) {
                menuToggle.classList.add('scroll-hidden');
                accumulatedScrollDelta = 0;
            } else if (accumulatedScrollDelta < -8) {
                menuToggle.classList.remove('scroll-hidden');
                accumulatedScrollDelta = 0;
            }
        }

        previousScrollY = currentScrollY;
        scrollUpdateQueued = false;
    }

    window.addEventListener('scroll', () => {
        if (scrollUpdateQueued) return;
        scrollUpdateQueued = true;
        window.requestAnimationFrame(updateMenuToggleVisibility);
    }, { passive: true });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            document.querySelector('.menu-toggle')?.classList.remove('scroll-hidden');
        }
        previousScrollY = window.scrollY;
        accumulatedScrollDelta = 0;
    });

    const endpoint = document.body.dataset.liveUpdatesUrl;
    if (!endpoint) return;

    let previousToken = null;
    let previousOrderToken = null;
    let previousProductToken = null;
    let previousReturnRequestToken = null;
    let previousReturnPickupToken = null;
    let previousCustomerReturnToken = null;
    let previousMaintenanceToken = null;
    let previousDeliveryFeeToken = null;
    let refreshingProductFragments = false;

    async function refreshLiveProductFragments() {
        const currentFragments = Array.from(
            document.querySelectorAll('[data-live-products]')
        );
        if (!currentFragments.length || refreshingProductFragments) return;

        refreshingProductFragments = true;
        try {
            const pageUrl = new URL(window.location.href);
            pageUrl.searchParams.set('_live_products_refresh', String(Date.now()));
            const response = await fetch(pageUrl.toString(), {
                cache: 'no-store',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            if (!response.ok) throw new Error('Product refresh request failed');
            if (
                response.redirected &&
                new URL(response.url).pathname !== window.location.pathname
            ) {
                throw new Error('Product refresh was redirected');
            }

            const freshDocument = new DOMParser().parseFromString(
                await response.text(),
                'text/html',
            );
            const freshFragments = Array.from(
                freshDocument.querySelectorAll('[data-live-products]')
            );
            const usedFragments = new Set();
            let updated = false;

            currentFragments.forEach((currentFragment) => {
                const freshFragment = freshFragments.find((candidate) => (
                    !usedFragments.has(candidate) &&
                    candidate.dataset.liveProducts === currentFragment.dataset.liveProducts
                ));
                if (!freshFragment) return;

                usedFragments.add(freshFragment);
                currentFragment.innerHTML = freshFragment.innerHTML;
                updated = true;
            });

            if (updated) {
                document.dispatchEvent(new CustomEvent('gws:product-fragments-updated'));
            }
        } catch (error) {
            console.error('Unable to refresh live product sections:', error);
        } finally {
            refreshingProductFragments = false;
        }
    }

    document.addEventListener('gws:products-updated', refreshLiveProductFragments);
    let customerOrderBaseline = null;
    let adminStaffOrderBaseline = null;

    function enableBrowserNotifications() {
        if (
            !window.isSecureContext ||
            !('Notification' in window) ||
            Notification.permission !== 'default'
        ) {
            return;
        }
        Notification.requestPermission().catch(() => {});
    }

    function sendBrowserNotification(title, body, targetUrl) {
        if (
            !window.isSecureContext ||
            !('Notification' in window) ||
            Notification.permission !== 'granted'
        ) {
            return;
        }
        const notification = new Notification(title, {
            body: body,
            icon: '/static/accounts/images/for login image.png',
            tag: 'grateful-waterstation-order',
        });
        notification.onclick = () => {
            window.focus();
            window.location.href = targetUrl;
            notification.close();
        };
    }

    function sendToDashboardNotificationBell(notification) {
        if (!document.querySelector('[data-dashboard-notification-bell]')) return false;
        document.dispatchEvent(new CustomEvent('gws:dashboard-notification', {
            detail: {
                ...notification,
                category_label: notification.category === 'announcement'
                    ? 'Announcement'
                    : notification.category === 'orders'
                        ? 'Orders'
                        : notification.category || '',
                source: 'live',
                is_read: false,
                created_at: new Date().toISOString(),
            },
        }));
        return true;
    }

    function showOrderStatusNotification(order) {
        const title = 'Order status updated';
        const description = `Order ${order.order_number} · ${order.status_display}`;
        const targetUrl = '/accounts/customer/orders/';
        if (sendToDashboardNotificationBell({
            id: `order-status-${order.id}-${order.updated_at}`,
            title,
            description,
            category: 'orders',
            severity: 'info',
            target_url: targetUrl,
        })) {
            sendBrowserNotification(title, description, targetUrl);
            return;
        }
        let toast = document.getElementById('gws-order-status-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'gws-order-status-toast';
            toast.style.cssText = [
                'position:fixed',
                'right:20px',
                'bottom:20px',
                'z-index:2000',
                'width:min(360px,calc(100vw - 40px))',
                'padding:16px 42px 16px 18px',
                'border:1px solid #dbeafe',
                'border-left:4px solid #1a8ad4',
                'border-radius:14px',
                'background:rgba(255,255,255,.96)',
                'color:#17324d',
                'box-shadow:0 14px 34px rgba(15,83,130,.18)',
                'backdrop-filter:blur(12px)',
                'font:600 14px/1.45 Segoe UI,sans-serif',
                'cursor:pointer',
                'opacity:0',
                'transform:translateY(12px)',
                'transition:opacity .2s ease,transform .2s ease'
            ].join(';');
            document.body.appendChild(toast);
        }
        toast.innerHTML = `<span style="display:flex;align-items:center;gap:10px"><span style="display:grid;place-items:center;width:32px;height:32px;border-radius:10px;background:#eaf3fb;color:#1a8ad4;font-size:15px"><i class="fas fa-box"></i></span><span><strong style="display:block;font-size:13px;color:#17324d">Order status updated</strong><span style="display:block;margin-top:2px;font-size:12px;font-weight:400;color:#60758a">Order ${order.order_number} · ${order.status_display}</span></span></span><button type="button" aria-label="Close notification" style="position:absolute;top:10px;right:11px;border:0;background:transparent;color:#8aa0b5;font-size:18px;line-height:1;cursor:pointer">&times;</button>`;
        toast.onclick = () => {
            window.location.href = '/accounts/customer/orders/';
        };
        toast.querySelector('button').onclick = (event) => {
            event.stopPropagation();
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(12px)';
        };
        sendBrowserNotification(
            'Order status updated',
            `Order ${order.order_number} · ${order.status_display}`,
            '/accounts/customer/orders/'
        );
        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        });
        clearTimeout(toast._hideTimer);
        toast._hideTimer = setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(12px)';
        }, 6000);
    }

    function notifyCustomerOrderChanges(data) {
        if (!Array.isArray(data.customer_order_updates)) return;
        const current = {};
        data.customer_order_updates.forEach((order) => {
            current[order.id] = `${order.status}:${order.updated_at}`;
        });
        if (customerOrderBaseline !== null) {
            data.customer_order_updates.forEach((order) => {
                if (
                    customerOrderBaseline[order.id] &&
                    customerOrderBaseline[order.id] !== current[order.id]
                ) {
                    showOrderStatusNotification(order);
                }
            });
        }
        customerOrderBaseline = current;
    }

    function showNewOrderNotification(order) {
        const title = 'New customer order';
        const description = `Order ${order.order_number} is ready to review`;
        const targetUrl = '/accounts/manage-orders/';
        if (sendToDashboardNotificationBell({
            id: `new-customer-order-${order.id}-${order.created_at}`,
            title,
            description,
            category: 'orders',
            severity: 'info',
            target_url: targetUrl,
        })) {
            sendBrowserNotification(title, description, targetUrl);
            return;
        }
        let toast = document.getElementById('gws-new-order-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'gws-new-order-toast';
            toast.style.cssText = [
                'position:fixed',
                'right:20px',
                'bottom:20px',
                'z-index:2000',
                'width:min(360px,calc(100vw - 40px))',
                'padding:16px 42px 16px 18px',
                'border:1px solid #dbeafe',
                'border-left:4px solid #1a8ad4',
                'border-radius:14px',
                'background:rgba(255,255,255,.96)',
                'color:#17324d',
                'box-shadow:0 14px 34px rgba(15,83,130,.18)',
                'backdrop-filter:blur(12px)',
                'font:600 14px/1.45 Segoe UI,sans-serif',
                'cursor:pointer',
                'opacity:0',
                'transform:translateY(12px)',
                'transition:opacity .2s ease,transform .2s ease'
            ].join(';');
            document.body.appendChild(toast);
        }
        toast.innerHTML = `<span style="display:flex;align-items:center;gap:10px"><span style="display:grid;place-items:center;width:32px;height:32px;border-radius:10px;background:#eaf3fb;color:#1a8ad4;font-size:15px"><i class="fas fa-shopping-bag"></i></span><span><strong style="display:block;font-size:13px;color:#17324d">New customer order</strong><span style="display:block;margin-top:2px;font-size:12px;font-weight:400;color:#60758a">Order ${order.order_number} is ready to review</span></span></span><button type="button" aria-label="Close notification" style="position:absolute;top:10px;right:11px;border:0;background:transparent;color:#8aa0b5;font-size:18px;line-height:1;cursor:pointer">&times;</button>`;
        toast.onclick = () => {
            window.location.href = '/accounts/manage-orders/';
        };
        toast.querySelector('button').onclick = (event) => {
            event.stopPropagation();
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(12px)';
        };
        sendBrowserNotification(
            'New customer order',
            `Order ${order.order_number} is ready to review`,
            '/accounts/manage-orders/'
        );
        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        });
        clearTimeout(toast._hideTimer);
        toast._hideTimer = setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(12px)';
        }, 6000);
    }

    function restoreNewOrderNotification() {
        try {
            const pending = JSON.parse(sessionStorage.getItem('gws-pending-new-order'));
            if (
                pending &&
                pending.order &&
                Date.now() - pending.createdAt < 15000
            ) {
                showNewOrderNotification(pending.order);
            }
            sessionStorage.removeItem('gws-pending-new-order');
        } catch (error) {
            sessionStorage.removeItem('gws-pending-new-order');
        }
    }

    function notifyAdminStaffNewOrder(data) {
        const order = data.latest_customer_order;
        if (!order) return;
        const current = `${order.id}:${order.created_at}`;
        if (adminStaffOrderBaseline !== null && current !== adminStaffOrderBaseline) {
            try {
                sessionStorage.setItem('gws-pending-new-order', JSON.stringify({
                    order: order,
                    createdAt: Date.now(),
                }));
            } catch (error) {
                // The live popup still works when session storage is unavailable.
            }
            showNewOrderNotification(order);
        }
        adminStaffOrderBaseline = current;
    }

    function styleBadge(badge) {
        badge.classList.add('live-notification-badge');
        badge.style.setProperty('width', '26px', 'important');
        badge.style.setProperty('height', '26px', 'important');
        badge.style.setProperty('min-width', '26px', 'important');
        badge.style.setProperty('padding', '0', 'important');
        badge.style.setProperty('margin', '0', 'important');
        badge.style.setProperty('border-radius', '50%', 'important');
        badge.style.setProperty('background', '#ef4444', 'important');
        badge.style.setProperty('color', '#fff', 'important');
        badge.style.setProperty('font-size', '.75rem', 'important');
        badge.style.setProperty('font-weight', '700', 'important');
        badge.style.setProperty('line-height', '26px', 'important');
        badge.style.setProperty('text-align', 'center', 'important');
        badge.style.setProperty('align-items', 'center', 'important');
        badge.style.setProperty('justify-content', 'center', 'important');
        badge.style.setProperty('position', 'absolute', 'important');
        badge.style.setProperty('top', '50%', 'important');
        badge.style.setProperty('right', '.85rem', 'important');
        badge.style.setProperty('transform', 'translateY(-50%)', 'important');
        badge.style.setProperty('box-sizing', 'border-box', 'important');
    }

    function updateBadges(data) {
        function ensureBadge(link, className, marker) {
            let badge = link.querySelector(`.${className}`);
            if (!badge) {
                badge = document.createElement('span');
                badge.className = `${className} live-notification-badge`;
                badge.dataset.liveBadge = marker;
                badge.style.cssText = [
                    'width:26px',
                    'height:26px',
                    'min-width:26px',
                    'padding:0',
                    'margin:0',
                    'border-radius:50%',
                    'background:#ef4444',
                    'color:#fff',
                    'font-size:.75rem',
                    'font-weight:700',
                    'line-height:26px',
                    'text-align:center',
                    'display:inline-flex',
                    'align-items:center',
                    'justify-content:center',
                    'flex-shrink:0',
                    'position:absolute',
                    'top:50%',
                    'right:.85rem',
                    'transform:translateY(-50%)',
                    'box-sizing:border-box'
                ].join(';');
                link.appendChild(badge);
            }

            styleBadge(badge);
            return badge;
        }

        const messageLinks = document.querySelectorAll(
            '.nav-links a[href*="messages"], .sidebar-utility a[href*="messages"]'
        );
        messageLinks.forEach((link) => {
            const badge = ensureBadge(link, 'unread-badge', 'messages');
            const count = Number(data.unread_count || 0);
            badge.textContent = count;
            badge.style.setProperty('display', count > 0 ? 'inline-flex' : 'none', 'important');
        });

        const orderLinks = document.querySelectorAll(
            '.nav-links a[href*="manage-orders"], .nav-links a[href*="customer/orders"], ' +
            '.sidebar-utility a[href*="manage-orders"], .sidebar-utility a[href*="customer/orders"]'
        );
        orderLinks.forEach((link) => {
            const badge = ensureBadge(link, 'order-badge', 'orders');
            const count = Number(data.order_notification_count || 0);
            badge.textContent = count;
            badge.style.setProperty('display', count > 0 ? 'inline-flex' : 'none', 'important');
        });

        document.querySelectorAll('.unread-badge').forEach((badge) => {
            styleBadge(badge);
            const count = Number(data.unread_count || 0);
            badge.textContent = count;
            badge.style.setProperty('display', count > 0 ? 'inline-flex' : 'none', 'important');
        });

        document.querySelectorAll('.order-badge').forEach((badge) => {
            styleBadge(badge);
            const count = Number(
                data.order_notification_count ?? data.pending_orders ?? 0
            );
            badge.textContent = count;
            badge.style.setProperty('display', count > 0 ? 'inline-flex' : 'none', 'important');
        });
    }

    let stationAvailability;
    const stationReminderKey = 'gws-station-closed-reminder-shown';

    function ensureCustomerStationReminder() {
        if (document.getElementById('gwsStationReminderOverlay')) return;
        const overlay = document.createElement('div');
        overlay.id = 'gwsStationReminderOverlay';
        overlay.className = 'gws-station-reminder-overlay';
        overlay.hidden = true;
        overlay.innerHTML = '<div class="gws-station-reminder" role="dialog" aria-modal="true" aria-labelledby="gwsStationReminderTitle"><h3 id="gwsStationReminderTitle">Reminder</h3><p>The Grateful Water Station is closed, but you can buy our products for reservation.</p><button type="button">OK</button></div>';
        document.body.appendChild(overlay);
        overlay.querySelector('button').addEventListener('click', () => { overlay.hidden = true; });
        overlay.addEventListener('click', (event) => {
            if (event.target === overlay) overlay.hidden = true;
        });
    }

    function updateCustomerStationAvailability(data) {
        if (data.user_role !== 'customer' || typeof data.station_is_open !== 'boolean') return;
        const isOpen = data.station_is_open;
        document.querySelectorAll('#stationAvailabilityBadge').forEach((badge) => {
            badge.classList.toggle('is-open', isOpen);
            badge.classList.toggle('is-closed', !isOpen);
            badge.textContent = isOpen ? "We're open now" : "We're closed now";
            badge.setAttribute('aria-label', isOpen ? "We're open now" : "We're closed now");
        });
        ensureCustomerStationReminder();
        const overlay = document.getElementById('gwsStationReminderOverlay');
        if (isOpen) {
            stationAvailability = true;
            overlay.hidden = true;
            window.localStorage.removeItem(stationReminderKey);
            return;
        }
        const alreadyShown = window.localStorage.getItem(stationReminderKey) === 'true';
        if (stationAvailability !== false && !alreadyShown) {
            overlay.hidden = false;
            window.localStorage.setItem(stationReminderKey, 'true');
        }
        stationAvailability = false;
    }

    function pollLiveUpdates() {
        fetch(endpoint, {
            cache: 'no-store',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
            .then((response) => {
                if (!response.ok) throw new Error('Live update request failed');
                return response.json();
            })
            .then((data) => {
                updateBadges(data);
                updateCustomerStationAvailability(data);
                notifyCustomerOrderChanges(data);
                notifyAdminStaffNewOrder(data);
                const orderToken = JSON.stringify(data.orders);
                const orderStatusChanged =
                    previousOrderToken !== null && orderToken !== previousOrderToken;
                previousOrderToken = orderToken;
                const productToken = JSON.stringify(data.products);
                const productsChanged =
                    previousProductToken !== null &&
                    productToken !== previousProductToken;
                previousProductToken = productToken;
                if (productsChanged) {
                    document.dispatchEvent(new CustomEvent('gws:products-updated'));
                }
                const returnRequestToken = JSON.stringify(data.return_requests);
                const returnRequestChanged =
                    previousReturnRequestToken !== null &&
                    returnRequestToken !== previousReturnRequestToken;
                previousReturnRequestToken = returnRequestToken;
                const returnPickupToken = JSON.stringify(data.return_pickups);
                const returnPickupChanged =
                    previousReturnPickupToken !== null &&
                    returnPickupToken !== previousReturnPickupToken;
                previousReturnPickupToken = returnPickupToken;
                const customerReturnToken = JSON.stringify(data.customer_returns);
                const customerReturnChanged =
                    previousCustomerReturnToken !== null &&
                    customerReturnToken !== previousCustomerReturnToken;
                previousCustomerReturnToken = customerReturnToken;
                const maintenanceToken = JSON.stringify(data.maintenance);
                const maintenanceChanged =
                    previousMaintenanceToken !== null &&
                    maintenanceToken !== previousMaintenanceToken;
                previousMaintenanceToken = maintenanceToken;
                const deliveryFeeToken = JSON.stringify(data.delivery_fee_rates);
                if (
                    data.delivery_fee_rates &&
                    (previousDeliveryFeeToken === null ||
                        deliveryFeeToken !== previousDeliveryFeeToken)
                ) {
                    document.dispatchEvent(new CustomEvent('gws:delivery-fee-update', {
                        detail: { delivery_fee_rates: data.delivery_fee_rates },
                    }));
                }
                previousDeliveryFeeToken = deliveryFeeToken;
                const token = JSON.stringify({
                    orders: data.orders,
                    return_requests: data.return_requests,
                    return_pickups: data.return_pickups,
                    customer_returns: data.customer_returns,
                    products: data.products,
                    sales: data.sales,
                    users: data.users,
                    maintenance: data.maintenance,
                    pending_orders: data.pending_orders,
                    assigned_orders: data.assigned_orders,
                    customer_orders: data.customer_orders,
                    customer_order_updates: data.customer_order_updates,
                    latest_customer_order: data.latest_customer_order,
                    delivery_fee_rates: data.delivery_fee_rates,
                });
                const changed = previousToken !== null && token !== previousToken;
                previousToken = token;
                if (changed) {
                    document.dispatchEvent(new CustomEvent('gws:live-update', {
                        detail: {
                            ...data,
                            orderStatusChanged,
                            productsChanged,
                            returnRequestChanged,
                            returnPickupChanged,
                            customerReturnChanged,
                            maintenanceChanged,
                        },
                    }));
                }
                if (
                    orderStatusChanged &&
                    document.body.dataset.liveOrderRefresh === 'true'
                ) {
                    window.location.reload();
                }
                if (
                    returnRequestChanged &&
                    document.body.dataset.liveReturnRefresh === 'true'
                ) {
                    window.location.reload();
                }
            })
            .catch((error) => console.error('Unable to poll live updates:', error));
    }

    document.querySelectorAll('.unread-badge, .order-badge').forEach((badge) => {
        styleBadge(badge);
        if (Number(badge.textContent.trim()) === 0) {
            badge.style.setProperty('display', 'none', 'important');
        } else {
            badge.style.setProperty('display', 'inline-flex', 'important');
        }
    });

    restoreNewOrderNotification();
    if (!window.isSecureContext || !('Notification' in window)) {
        // The in-page notification remains available on HTTP LAN addresses.
    } else if (Notification.permission !== 'granted') {
        const requestNotificationPermission = () => {
            enableBrowserNotifications();
        };
        document.addEventListener('click', requestNotificationPermission, { once: true });
        document.addEventListener('touchstart', requestNotificationPermission, { once: true });
    }
    pollLiveUpdates();
    window.setInterval(pollLiveUpdates, 5000);
}());
