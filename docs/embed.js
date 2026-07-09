(function () {
  const script = document.currentScript;
  const src = script.dataset.src || new URL('index.html', script.src).toString();
  const height = script.dataset.height || '720';
  const iframe = document.createElement('iframe');
  iframe.src = src;
  iframe.title = 'Tax Policy Monitor';
  iframe.loading = 'lazy';
  iframe.style.width = '100%';
  iframe.style.maxWidth = script.dataset.width || '420px';
  iframe.style.height = height + 'px';
  iframe.style.border = '0';
  iframe.style.borderRadius = '16px';
  iframe.style.overflow = 'hidden';
  script.parentNode.insertBefore(iframe, script);
})();
