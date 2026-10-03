(() => {
  const content = document.getElementById('screen-content');
  const emergency = document.getElementById('emergency-panel');
  let frame;
  function fit() {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => {
      const width = document.documentElement.clientWidth;
      const height = window.visualViewport?.height || innerHeight;
      const available = Math.max(1, height - emergency.getBoundingClientRect().height - 4);
      const scale = Math.min(width / 1512, available / content.scrollHeight, 1);
      content.style.transform = `scale(${scale})`;
      content.style.marginLeft = `${Math.max(0,(width - 1512 * scale)/2)}px`;
    });
  }
  new ResizeObserver(fit).observe(content);
  new ResizeObserver(fit).observe(emergency);
  addEventListener('resize', fit);
  new MutationObserver(fit).observe(content, {childList:true, subtree:true, characterData:true});
  fit();
})();
