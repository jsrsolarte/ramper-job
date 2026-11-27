(() => {
  const panel = document.querySelector('[data-operational-alerts]');
  if (!panel) return;
  const enable = panel.querySelector('[data-operational-push-enable]');
  const disable = panel.querySelector('[data-operational-push-disable]');
  const status = panel.querySelector('[data-operational-push-status]');
  const csrf = document.cookie.split('; ').find((part) => part.startsWith('csrftoken='))?.split('=').slice(1).join('=') || '';
  const decodeKey = (value) => {
    const padded = value.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - value.length % 4) % 4);
    return Uint8Array.from(atob(padded), (char) => char.charCodeAt(0));
  };
  const post = async (payload) => {
    const response = await fetch(panel.dataset.subscriptionUrl, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error('No fue posible actualizar las alertas.');
    return response.json();
  };
  enable?.addEventListener('click', async () => {
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window) || !panel.dataset.publicKey) {
        throw new Error('Este navegador no admite las notificaciones push.');
      }
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') throw new Error('El permiso de notificaciones no fue concedido.');
      const registration = await navigator.serviceWorker.register(panel.dataset.workerUrl, {
        scope: '/', updateViaCache: 'none',
      });
      await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true, applicationServerKey: decodeKey(panel.dataset.publicKey),
      });
      await post({ enabled: true, subscription: subscription.toJSON() });
      status.textContent = 'Alertas operativas activas en este dispositivo.';
    } catch (error) {
      status.textContent = error.message || 'No fue posible activar las alertas.';
    }
  });
  disable?.addEventListener('click', async () => {
    try {
      const registration = await navigator.serviceWorker.getRegistration('/')
        || await navigator.serviceWorker.register(panel.dataset.workerUrl, { scope: '/' });
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) await post({ enabled: false, subscription: subscription.toJSON() });
      status.textContent = 'Alertas operativas desactivadas en este dispositivo.';
    } catch (error) {
      status.textContent = error.message || 'No fue posible desactivar las alertas.';
    }
  });
})();
