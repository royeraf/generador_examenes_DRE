/**
 * Bloquea el zoom del navegador en móviles y tablets.
 *
 * El meta viewport (`maximum-scale=1, user-scalable=no`) ya lo cubre en la
 * mayoría de navegadores, pero iOS Safari lo ignora desde iOS 10. Este guard
 * cubre los casos restantes:
 *  - pellizco con dos dedos (pinch zoom)
 *  - doble toque (double tap zoom)
 *  - gestos de Safari (`gesturestart` / `gesturechange` / `gestureend`)
 *
 * Para permitir zoom en un elemento puntual (por ejemplo un visor de imágenes)
 * basta con agregarle el atributo `data-allow-zoom`.
 */

const ALLOW_ZOOM_SELECTOR = '[data-allow-zoom], input, textarea, select';

const isZoomAllowed = (target: EventTarget | null): boolean => {
  if (!(target instanceof Element)) return false;
  return target.closest(ALLOW_ZOOM_SELECTOR) !== null;
};

const preventDefault = (event: Event) => {
  event.preventDefault();
};

const onTouchMove = (event: TouchEvent) => {
  if (event.touches.length > 1 && !isZoomAllowed(event.target)) {
    event.preventDefault();
  }
};

let lastTouchEnd = 0;
const onTouchEnd = (event: TouchEvent) => {
  const now = Date.now();
  const isDoubleTap = now - lastTouchEnd <= 300;

  if (isDoubleTap && !isZoomAllowed(event.target)) {
    event.preventDefault();
    // Reinicia el contador para no bloquear un tercer toque normal
    lastTouchEnd = 0;
    return;
  }

  lastTouchEnd = now;
};

let installed = false;

export function usePreventZoom(): void {
  if (installed || typeof document === 'undefined') return;
  installed = true;

  // Safari iOS: gestos de zoom propios del navegador
  document.addEventListener('gesturestart', preventDefault, { passive: false });
  document.addEventListener('gesturechange', preventDefault, { passive: false });
  document.addEventListener('gestureend', preventDefault, { passive: false });

  // Android / Chrome: pellizco con dos dedos
  document.addEventListener('touchmove', onTouchMove, { passive: false });

  // Doble toque en cualquier parte de la interfaz
  document.addEventListener('touchend', onTouchEnd, { passive: false });
}
