

document.addEventListener("DOMContentLoaded", () => {
    let isSubscribed = false;
    const btn = document.getElementById("push-subscribe-btn");
    const row = document.getElementById("push-subscribe-row");
    
    if (!btn) return;
    
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
    
    if (!isStandalone) {
        if (row) row.classList.add("d-none");
        return;
    }
    
    const urlUnsubscribe = btn.dataset.urlUnsubscribe;
    const urlSubscribe = btn.dataset.urlSubscribe;
    const urlVapid = btn.dataset.urlVapid;
    const textSubscribe = btn.dataset.textSubscribe;
    const textSubscribed = btn.dataset.textSubscribed;
    const textError = btn.dataset.textError;

    async function togglePushSubscription() {
        btn.disabled = true;
        
        try {
            const registration = await navigator.serviceWorker.ready;
            const csrfMeta = document.querySelector('meta[name="csrf-token"]');
            const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
            
            if (isSubscribed) {
                // Unsubscribe
                const subscription = await registration.pushManager.getSubscription();
                if (subscription) {
                    await subscription.unsubscribe();
                    await fetch(urlUnsubscribe, {
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        body: JSON.stringify({endpoint: subscription.endpoint})
                    });
                }
                
                isSubscribed = false;
                btn.textContent = textSubscribe;
                btn.classList.remove("btn-success");
                btn.classList.add("btn-outline-primary");
                
            } else {
                // Subscribe
                const res = await fetch(urlVapid);
                const vapidData = await res.json();
                
                const subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(vapidData.public_key)
                });

                const subRes = await fetch(urlSubscribe, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(subscription)
                });
                
                if (subRes.ok) {
                    isSubscribed = true;
                    btn.textContent = textSubscribed;
                    btn.classList.remove("btn-outline-primary");
                    btn.classList.add("btn-success");
                } else {
                    throw new Error("Server error");
                }
            }
        } catch (e) {
            console.error(e);
            btn.textContent = textError;
            btn.classList.remove("btn-outline-primary", "btn-success");
            btn.classList.add("btn-danger");
        }
        btn.disabled = false;
    }

    navigator.serviceWorker.ready.then(registration => {
        registration.pushManager.getSubscription().then(subscription => {
            if (subscription) {
                isSubscribed = true;
                btn.textContent = textSubscribed;
                btn.classList.remove("btn-outline-primary");
                btn.classList.add("btn-success");
                
                // Sync with server just in case the server missed it
                const csrfMeta = document.querySelector('meta[name="csrf-token"]');
                const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
                fetch(urlSubscribe, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(subscription)
                });
            }
            // update onclick
            btn.onclick = togglePushSubscription;
        });
    });
});
