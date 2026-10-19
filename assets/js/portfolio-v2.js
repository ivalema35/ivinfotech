/* =============================================================================
   IV Infotech — Portfolio v2 behaviour (vanilla JS, no dependencies)
   - Listing page : category filter + search + "show more" + balanced last row + URL state
   - Case study   : progress bar, section nav, gallery (tabs / carousel / lightbox),
                    testimonials carousel, broken-image cleanup,
                    Visual Builder live-preview protocol (embed mode only)
   Every feature is progressive enhancement: with JS off all content is still visible.
   ============================================================================= */
(function () {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var smooth = reduceMotion ? 'auto' : 'smooth';

  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function debounce(fn, ms) {
    var t;
    return function () { clearTimeout(t); var a = arguments, c = this; t = setTimeout(function () { fn.apply(c, a); }, ms); };
  }
  function plural(n, w) { return n + ' ' + w + (n === 1 ? '' : 's'); }

  /* ==========================================================================
     LISTING
     ========================================================================== */
  function initList() {
    var grid = $('#pfGrid');
    if (!grid) return;

    var PAGE = 9, STEP = 6;
    var cards = $$('.pf-card', grid);
    var chips = $$('.pf-chip');
    var search = $('#pfSearch'), count = $('#pfCount'), more = $('#pfMore'), empty = $('#pfEmpty'), reset = $('#pfReset');
    var state = { cat: 'all', q: '', shown: PAGE };

    // restore state from the URL (?cat=web&q=erp) so filtered views can be shared / bookmarked
    try {
      var params = new URLSearchParams(location.search);
      var c = params.get('cat');
      if (c && chips.some(function (b) { return b.getAttribute('data-filter') === c; })) state.cat = c;
      if (params.get('q')) { state.q = params.get('q').slice(0, 80); if (search) search.value = state.q; }
    } catch (e) { /* old browser — ignore */ }

    function matches(card) {
      var okCat = state.cat === 'all' || (' ' + card.getAttribute('data-cats') + ' ').indexOf(' ' + state.cat + ' ') !== -1;
      if (!okCat) return false;
      if (!state.q) return true;
      var hay = card.getAttribute('data-search') || '';
      return state.q.toLowerCase().split(/\s+/).filter(Boolean).every(function (w) { return hay.indexOf(w) !== -1; });
    }

    // Keep every row visually "full": first visible card becomes a wide feature card (when 3+ results),
    // and the last row stretches so there are never ugly empty slots — for any number of results.
    function balance(vis) {
      var w = window.innerWidth;
      var cols = w >= 1100 ? 3 : (w >= 680 ? 2 : 1);
      cards.forEach(function (card) { card.classList.remove('is-feature', 'is-span-12', 'is-span-6'); });
      if (!vis.length || cols === 1) return;
      var feature = vis.length >= 3;
      if (feature) vis[0].classList.add('is-feature');
      if (cols === 3) {
        var rest = vis.length - (feature ? 2 : 0);
        var r = rest % 3;
        if (r === 1) vis[vis.length - 1].classList.add('is-span-12');
        else if (r === 2) { vis[vis.length - 1].classList.add('is-span-6'); vis[vis.length - 2].classList.add('is-span-6'); }
      } else {
        var rest2 = vis.length - (feature ? 1 : 0);
        if (rest2 % 2 === 1) vis[vis.length - 1].classList.add('is-span-12');
      }
    }

    function render(updateUrl) {
      var list = cards.filter(matches);
      var vis = list.slice(0, state.shown);
      cards.forEach(function (card) { card.hidden = vis.indexOf(card) === -1; });
      balance(vis);
      if (empty) empty.hidden = list.length !== 0;
      if (count) count.textContent = list.length ? ('Showing ' + vis.length + ' of ' + plural(list.length, 'project')) : 'No matching projects';
      chips.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-filter') === state.cat ? 'true' : 'false'); });
      if (more) {
        var rem = list.length - vis.length;
        more.hidden = rem <= 0;
        var label = more.querySelector('.pf-more__label');
        if (label) label.textContent = 'Show ' + plural(Math.min(STEP, rem), 'more project');
      }
      if (updateUrl && window.history && history.replaceState) {
        var p = new URLSearchParams();
        if (state.cat !== 'all') p.set('cat', state.cat);
        if (state.q) p.set('q', state.q);
        var qs = p.toString();
        history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') + location.hash);
      }
    }

    chips.forEach(function (b) {
      b.addEventListener('click', function () { state.cat = b.getAttribute('data-filter'); state.shown = PAGE; render(true); });
    });
    if (search) {
      search.addEventListener('input', debounce(function () { state.q = search.value.trim().slice(0, 80); state.shown = PAGE; render(true); }, 160));
    }
    if (more) more.addEventListener('click', function () { state.shown += STEP; render(false); });
    if (reset) reset.addEventListener('click', function () { state.cat = 'all'; state.q = ''; state.shown = PAGE; if (search) search.value = ''; render(true); });
    window.addEventListener('resize', debounce(function () { render(false); }, 150));
    render(false);
  }

  /* ==========================================================================
     CASE STUDY
     ========================================================================== */
  function initProgress() {
    var bar = $('.pf-progress span');
    if (!bar) return;
    var ticking = false;
    function update() {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      bar.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, Math.max(0, (window.scrollY || h.scrollTop) / max)) : 0) + ')';
      ticking = false;
    }
    window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    update();
  }

  function initSectionNav() {
    var links = $$('.pf-snav a[href^="#"]');
    if (!links.length) return;
    var map = {};
    links.forEach(function (a) {
      var id = a.getAttribute('href').slice(1);
      var el = document.getElementById(id);
      if (!el) { a.remove(); return; }
      map[id] = a;
      a.addEventListener('click', function (e) {
        e.preventDefault();
        el.scrollIntoView({ behavior: smooth, block: 'start' });
        if (history.replaceState) history.replaceState(null, '', '#' + id);
      });
    });
    if (!('IntersectionObserver' in window)) return;
    var current = null;
    function activate(id) {
      if (current === id || !map[id]) return;
      current = id;
      Object.keys(map).forEach(function (k) { map[k].classList.toggle('is-active', k === id); });
      var a = map[id], nav = a.parentElement;
      if (nav && nav.scrollWidth > nav.clientWidth) nav.scrollTo({ left: a.offsetLeft - nav.clientWidth / 2 + a.clientWidth / 2, behavior: smooth });
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) activate(en.target.id); });
    }, { rootMargin: '-35% 0px -55% 0px', threshold: 0 });
    Object.keys(map).forEach(function (id) { io.observe(document.getElementById(id)); });
  }

  /* generic scroll-snap carousel: prev/next buttons + disabled state + optional counter / dots */
  function bindCarousel(track, prev, next, opts) {
    if (!track) return null;
    opts = opts || {};
    function items() { return $$(opts.itemSelector || ':scope > *', track).filter(function (n) { return n.offsetParent !== null; }); }
    function step() {
      var it = items()[0];
      if (!it) return track.clientWidth;
      var gap = parseFloat(getComputedStyle(track).columnGap || getComputedStyle(track).gap) || 0;
      return it.getBoundingClientRect().width + gap;
    }
    function pageCount() { return Math.max(1, Math.round(track.scrollWidth / Math.max(1, track.clientWidth))); }
    function update() {
      var max = track.scrollWidth - track.clientWidth;
      var atStart = track.scrollLeft <= 2, atEnd = track.scrollLeft >= max - 2;
      if (prev) prev.disabled = atStart;
      if (next) next.disabled = atEnd;
      var fits = max <= 2;
      if (opts.ctrl) opts.ctrl.hidden = fits;
      if (opts.counter) {
        var its = items(), idx = 0, best = 1e9;
        var c = track.scrollLeft + track.clientWidth / 2;
        its.forEach(function (n, i) { var d = Math.abs(n.offsetLeft + n.offsetWidth / 2 - c); if (d < best) { best = d; idx = i; } });
        opts.counter.textContent = (idx + 1) + ' / ' + its.length;
      }
      if (opts.dots) {
        var pages = pageCount(), cur = max > 0 ? Math.round(track.scrollLeft / max * (pages - 1)) : 0;
        if (opts.dots.children.length !== pages) {
          opts.dots.innerHTML = '';
          for (var i = 0; i < pages; i++) {
            (function (n) {
              var b = document.createElement('button');
              b.type = 'button'; b.setAttribute('aria-label', 'Go to slide ' + (n + 1));
              b.addEventListener('click', function () { track.scrollTo({ left: pages > 1 ? n * (track.scrollWidth - track.clientWidth) / (pages - 1) : 0, behavior: smooth }); });
              opts.dots.appendChild(b);
            })(i);
          }
        }
        Array.prototype.forEach.call(opts.dots.children, function (b, i) { if (i === cur) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current'); });
      }
    }
    if (prev) prev.addEventListener('click', function () { track.scrollBy({ left: -step(), behavior: smooth }); });
    if (next) next.addEventListener('click', function () { track.scrollBy({ left: step(), behavior: smooth }); });
    track.addEventListener('scroll', debounce(update, 40), { passive: true });
    window.addEventListener('resize', debounce(update, 120));
    track.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); track.scrollBy({ left: step(), behavior: smooth }); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); track.scrollBy({ left: -step(), behavior: smooth }); }
    });
    update();
    return { update: update };
  }

  function initGallery() {
    var section = $('#gallery');
    if (!section) return;
    var panels = $$('.pf-gset', section);
    var tabs = $$('.pf-seg [role="tab"]', section);
    var strip = $('.pf-seg', section);
    var ctrls = [];
    function refresh() { ctrls.forEach(function (c) { if (c) c.update(); }); }

    function selectTab(tab) {
      tabs.forEach(function (t) { var on = t === tab; t.setAttribute('aria-selected', on ? 'true' : 'false'); t.tabIndex = on ? 0 : -1; });
      panels.forEach(function (p) { p.hidden = p.id !== tab.getAttribute('aria-controls'); });
      refresh();
    }

    // a screenshot failed to load (404 …): remove its slide, tidy tabs / counters, never leave empty frames
    function dropSlide(img) {
      var li = img.closest('.pf-slide');
      if (!li || !li.parentNode) return;
      li.remove();
      var alive = panels.filter(function (p) { return p.querySelector('.pf-slide'); });
      panels.forEach(function (p) {
        if (alive.indexOf(p) !== -1) return;
        p.hidden = true;
        tabs.forEach(function (t) { if (t.getAttribute('aria-controls') === p.id) t.hidden = true; });
      });
      if (!alive.length) {
        section.hidden = true;
        var link = $('.pf-snav a[href="#gallery"]'); if (link) link.hidden = true;
        return;
      }
      if (strip && alive.length < 2) strip.hidden = true;
      if (alive.every(function (p) { return p.hidden; })) {
        var t0 = tabs.filter(function (t) { return t.getAttribute('aria-controls') === alive[0].id; })[0];
        if (t0) selectTab(t0); else alive[0].hidden = false;
      }
      $$('.pf-gset', section).forEach(function (p) {
        var c = $('[data-g-count]', p), n = $$('.pf-slide', p).length;
        if (c && n) c.textContent = '1 / ' + n;
      });
      refresh();
    }

    $$('.pf-gallery', section).forEach(function (g) {
      ctrls.push(bindCarousel($('.pf-gallery__track', g), $('.pf-gnav--prev', g), $('.pf-gnav--next', g), { counter: $('[data-g-count]', g.parentElement), itemSelector: '.pf-slide' }));
    });
    $$('.pf-slide img', section).forEach(function (img) {
      if (img.complete && img.naturalWidth === 0 && img.getAttribute('src')) dropSlide(img);
      else img.addEventListener('error', function () { dropSlide(img); }, { once: true });
    });
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { selectTab(t); });
      t.addEventListener('keydown', function (e) {
        var n = null;
        if (e.key === 'ArrowRight') n = tabs[(i + 1) % tabs.length];
        if (e.key === 'ArrowLeft') n = tabs[(i - 1 + tabs.length) % tabs.length];
        if (n) { e.preventDefault(); n.focus(); selectTab(n); }
      });
    });

    /* lightbox */
    var dlg = $('#pfLightbox');
    if (!dlg || typeof dlg.showModal !== 'function') return;
    var img = $('img', dlg), cap = $('#pfLbCap'), cnt = $('#pfLbCount');
    var list = [], idx = 0;
    function show(i) {
      if (!list.length) return;
      idx = (i + list.length) % list.length;
      var it = list[idx];
      img.src = it.src; img.alt = it.alt;
      cap.textContent = it.cap;
      cnt.textContent = (idx + 1) + ' / ' + list.length;
    }
    section.addEventListener('click', function (e) {
      var btn = e.target.closest('.pf-slide__btn');
      if (!btn) return;
      var panel = btn.closest('.pf-gset') || section;
      var btns = $$('.pf-slide__btn', panel);
      list = btns.map(function (b) {
        var im = $('img', b), fc = b.parentElement.querySelector('figcaption');
        return { src: im.currentSrc || im.src, alt: im.alt, cap: fc ? fc.textContent.trim() : '' };
      });
      show(btns.indexOf(btn));
      dlg.showModal();
    });
    $('.is-close', dlg).addEventListener('click', function () { dlg.close(); });
    $('.is-prev', dlg).addEventListener('click', function () { show(idx - 1); });
    $('.is-next', dlg).addEventListener('click', function () { show(idx + 1); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg || e.target.classList.contains('pf-lightbox__stage') || e.target.classList.contains('pf-lightbox__img')) dlg.close(); });
    dlg.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') show(idx - 1);
      if (e.key === 'ArrowRight') show(idx + 1);
    });
    var sx = null;
    dlg.addEventListener('pointerdown', function (e) { sx = e.clientX; });
    dlg.addEventListener('pointerup', function (e) {
      if (sx === null) return;
      var dx = e.clientX - sx; sx = null;
      if (Math.abs(dx) > 60) show(idx + (dx < 0 ? 1 : -1));
    });
    dlg.addEventListener('close', function () { img.removeAttribute('src'); });
  }

  /* testimonials — also used by the Visual Builder live preview */
  var testiCtl = null;
  function initTestimonials() {
    var track = $('#pfTestiTrack');
    if (!track) return;
    testiCtl = bindCarousel(track, $('#pfTestiPrev'), $('#pfTestiNext'), { dots: $('#pfTestiDots'), ctrl: $('.pf-tcar__ctrl'), itemSelector: '.pf-tcard' });
  }
  window.bzReinitTestimonials = function (data) {
    var track = $('#pfTestiTrack'), section = $('#testimonials');
    if (!track) return;
    data = Array.isArray(data) ? data : [];
    track.innerHTML = data.map(function (t) {
      var name = t.client_name || t.name || '';
      var initials = name.split(' ').filter(Boolean).map(function (w) { return w.charAt(0); }).join('').slice(0, 2).toUpperCase() || '··';
      var role = [t.client_role || t.role || '', t.company_name || t.company || ''].filter(Boolean).join(' · ');
      var stars = Math.max(0, Math.min(5, parseInt(t.rating, 10) || 5));
      return '<li class="pf-tcard pf-glass"><blockquote><p>' + esc(t.quote) + '</p></blockquote><footer>' +
        '<span class="pf-clay pf-avatar" aria-hidden="true">' + esc(initials) + '</span>' +
        '<div class="pf-who"><b>' + esc(name) + '</b><span>' + esc(role) + '</span></div>' +
        '<span class="pf-stars" role="img" aria-label="' + stars + ' out of 5 stars">' + new Array(stars + 1).join('<i class="fa-solid fa-star"></i>') + '</span></footer></li>';
    }).join('');
    track.className = 'pf-tcar__track pf-n-' + Math.min(data.length, 3);
    if (section) section.hidden = data.length === 0;
    var link = $('.pf-snav a[href="#testimonials"]');
    if (link) link.hidden = data.length === 0;
    track.scrollLeft = 0;
    if (testiCtl) testiCtl.update();
  };

  /* hero visual: keep layout in sync with which device frames are actually visible
     (no frames → visual column collapses and the copy goes full width) */
  function syncHeroVisual() {
    var vis = $('.pf-visual'), grid = $('.pf-dhero__grid');
    if (!vis) return;
    var w = $('[data-ivb-container="hero_image_web"]'), a = $('[data-ivb-container="hero_image_app"]');
    var hasW = !!(w && !w.hidden), hasA = !!(a && !a.hidden);
    vis.hidden = !(hasW || hasA);
    vis.classList.toggle('pf-visual--app-only', hasA && !hasW);
    if (grid) grid.classList.toggle('is-single', vis.hidden);
  }

  function initImageFallbacks() {
    // hero mockups: if the image is missing/broken hide that device frame so no empty frame is shown
    $$('img[data-ivb="hero_image_web"], img[data-ivb="hero_image_app"]').forEach(function (im) {
      var hide = function () {
        var key = im.getAttribute('data-ivb');
        var box = $('[data-ivb-container="' + key + '"]');
        if (box && !document.documentElement.hasAttribute('data-ivb-embed')) { box.hidden = true; syncHeroVisual(); }
      };
      if (im.complete && im.naturalWidth === 0 && im.getAttribute('src')) hide();
      else im.addEventListener('error', hide, { once: true });
    });
  }

  /* ==========================================================================
     VISUAL BUILDER — live preview protocol (only inside the admin iframe: ?embed=1)
     Messages (from builder):  {source:'ivb', type:'css'|'text'|'img'|'testimonials'|'array_update'|'ping'}
     Replies   (to builder):   {source:'ivb-preview', type:'ready'|'pong'|'edit'}
     ========================================================================== */
  function initEmbed() {
    var qs = ''; try { qs = new URLSearchParams(location.search).get('embed'); } catch (e) { /* ignore */ }
    if (!qs || window.parent === window) return;
    document.documentElement.setAttribute('data-ivb-embed', '1');

    function luminance(hex) {
      var h = String(hex || '').replace('#', '');
      if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
      if (!/^[0-9a-fA-F]{6}$/.test(h)) return 0;
      return parseInt(h.slice(0, 2), 16) * 0.299 + parseInt(h.slice(2, 4), 16) * 0.587 + parseInt(h.slice(4, 6), 16) * 0.114;
    }
    function toggleEmpties(key, value) {
      // KPI tile hides when its value is empty; outcome sticker hides when empty
      var m = /^kpi_(\d)_value$/.exec(key);
      if (m) { var tile = $('.pf-kpi[data-kpi="' + m[1] + '"]'); if (tile) tile.hidden = !String(value || '').trim(); }
      if (key === 'hero_outcome') { var st = $('.pf-sticker[data-ivb-wrap="hero_outcome"]'); if (st) st.hidden = !String(value || '').trim(); }
      var kp = $$('.pf-kpi:not([hidden])'); var strip = $('.pf-kpis'); if (strip) strip.hidden = kp.length === 0;
    }
    var DEFAULT_BADGES = 'Core Web Vitals|GA4 Tracking|Secure Payments|SEO-ready';
    function renderBadges(items) {
      var wrap = document.getElementById('preview-trust-badges');
      if (!wrap) return;
      items = Array.isArray(items) ? items : [];
      // same rule as the template: the untouched builder default set is not shown on the public page
      if (items.map(function (b) { return b.text; }).join('|') === DEFAULT_BADGES) items = [];
      wrap.innerHTML = items.map(function (b) {
        return '<span class="pf-badge pf-glass"><i class="' + esc(b.icon || 'fa-solid fa-shield-halved') + '" aria-hidden="true"></i>' + esc(b.text || 'Badge') + '</span>';
      }).join('');
      wrap.hidden = !wrap.children.length;
    }

    window.addEventListener('message', function (evt) {
      if (evt.source !== window.parent) return;
      var d = evt.data;
      if (!d || d.source !== 'ivb') return;
      if (d.type === 'css') {
        var themeEl = document.getElementById('ivb-theme-vars');
        if (themeEl) themeEl.textContent = String(d.css || '');
        var m = /--pf-primary:\s*(#[0-9a-fA-F]{3,6})/.exec(String(d.css || ''));
        if (m) document.documentElement.style.setProperty('--pf-on-primary', luminance(m[1]) > 165 ? '#0b1c3c' : '#ffffff');
      } else if (d.type === 'testimonials') {
        window.BZ_TESTIMONIALS = d.testimonials;
        window.bzReinitTestimonials(d.testimonials);
      } else if (d.type === 'array_update') {
        if (d.key === 'trust_badges') renderBadges(d.data);
      } else if (d.type === 'text') {
        $$('[data-ivb="' + d.key + '"]').forEach(function (n) { n.textContent = d.value; });
        toggleEmpties(d.key, d.value);
      } else if (d.type === 'img') {
        $$('img[data-ivb="' + d.key + '"]').forEach(function (i) {
          if (!d.value) return;
          i.src = d.value;
          var box = $('[data-ivb-container="' + d.key + '"]'); if (box) box.hidden = false;
        });
        syncHeroVisual();   // single-device <-> two-device <-> no visual
      } else if (d.type === 'ping') {
        evt.source.postMessage({ source: 'ivb-preview', type: 'pong' }, '*');
      }
    });
    document.addEventListener('input', function (e) {
      var el = e.target, key = el.getAttribute && el.getAttribute('data-ivb');
      if (key && el.isContentEditable) window.parent.postMessage({ source: 'ivb-preview', type: 'edit', key: key, value: el.textContent }, '*');
    });
    window.parent.postMessage({ source: 'ivb-preview', type: 'ready' }, '*');
  }

  function boot() {
    initList();
    if ($('.pf-detail')) {
      initProgress();
      initSectionNav();
      initGallery();
      initTestimonials();
      initImageFallbacks();
      initEmbed();
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
