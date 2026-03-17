document.addEventListener('DOMContentLoaded', function () {
  var blocks = document.querySelectorAll('.highlight');

  blocks.forEach(function (block) {
    var btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.setAttribute('aria-label', 'Copy code');
    btn.textContent = 'Copy';

    btn.addEventListener('click', function () {
      var code = block.querySelector('code');
      var text = code ? code.innerText : block.innerText;

      navigator.clipboard.writeText(text).then(function () {
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(function () {
          btn.textContent = 'Copy';
          btn.classList.remove('copied');
        }, 2000);
      });
    });

    block.style.position = 'relative';
    block.appendChild(btn);
  });
});
