document.addEventListener('DOMContentLoaded', function () {
  var post = document.querySelector('.post');
  var tocContainer = document.getElementById('toc');
  if (!post || !tocContainer) return;

  var headings = post.querySelectorAll('h2, h3');
  if (headings.length < 3) {
    tocContainer.parentElement.style.display = 'none';
    return;
  }

  var list = document.createElement('ul');

  headings.forEach(function (h) {
    if (!h.id) {
      h.id = h.textContent
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/\s+/g, '-');
    }

    var li = document.createElement('li');
    li.className = h.tagName === 'H3' ? 'toc-h3' : '';

    var a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = h.textContent;
    li.appendChild(a);
    list.appendChild(li);
  });

  tocContainer.appendChild(list);

  // Highlight active heading on scroll
  var tocLinks = tocContainer.querySelectorAll('a');
  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          tocLinks.forEach(function (link) { link.classList.remove('active'); });
          var active = tocContainer.querySelector('a[href="#' + entry.target.id + '"]');
          if (active) active.classList.add('active');
        }
      });
    },
    { rootMargin: '0px 0px -80% 0px', threshold: 0 }
  );

  headings.forEach(function (h) { observer.observe(h); });
});
