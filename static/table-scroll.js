/* Las tablas anchas permanecen navegables con teclado en pantallas estrechas. */
document.addEventListener('keydown', (event) => {
  const region = event.target;
  if (!(region instanceof HTMLElement) || !region.matches('.admin-table-wrap') ||
      region.scrollWidth <= region.clientWidth || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
  if (event.key === 'ArrowRight') region.scrollLeft += 80;
  else if (event.key === 'ArrowLeft') region.scrollLeft -= 80;
  else if (event.key === 'Home') region.scrollLeft = 0;
  else if (event.key === 'End') region.scrollLeft = region.scrollWidth;
  else return;
  event.preventDefault();
});
