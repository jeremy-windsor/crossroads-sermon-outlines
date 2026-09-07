(() => {
  'use strict';

  const form = document.querySelector('.site-search');
  const input = document.querySelector('#site-search-query');
  const status = document.querySelector('#search-status');
  const results = document.querySelector('#search-results');
  if (!form || !input || !status || !results) return;

  const normalize = value => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
  const query = new URLSearchParams(window.location.search).get('q') || '';
  input.value = query;
  const terms = normalize(query).split(' ').filter(Boolean);

  const appendText = (parent, tag, text, className) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.textContent = text;
    parent.appendChild(element);
    return element;
  };

  const show = documents => {
    results.replaceChildren();
    if (!terms.length) {
      status.textContent = 'Enter a search above.';
      return;
    }
    const matches = documents.map((item, order) => {
      const haystack = normalize(item.terms);
      if (!terms.every(term => haystack.includes(term))) return null;
      const title = normalize(item.title);
      const phrase = normalize(query);
      const excerpts = item.excerpts || [item.excerpt];
      let score = terms.reduce((total, term) => total + (title.includes(term) ? 8 : 1), 0);
      if (title === phrase) score += 30;
      else if (title.startsWith(phrase)) score += 15;
      if (excerpts.some(excerpt => normalize(excerpt).includes(phrase))) score += 20;
      else if (haystack.includes(phrase)) score += 5;
      if (item.kind === 'scripture' && terms.some(term => normalize(item.reference || '').includes(term))) score += 6;
      return {item, order, score};
    }).filter(Boolean).sort((left, right) => right.score - left.score || left.order - right.order);

    const shown = matches.slice(0, 100);
    status.textContent = matches.length === 1 ? '1 result' : `${matches.length} results`;
    for (const {item} of shown) {
      const excerpts = item.excerpts || [item.excerpt];
      const excerpt = excerpts.reduce((best, candidate) => {
        const score = terms.filter(term => normalize(candidate).includes(term)).length;
        return score > best.score ? {text: candidate, score} : best;
      }, {text: item.excerpt, score: -1}).text;
      const entry = document.createElement('li');
      const article = document.createElement('article');
      const heading = document.createElement('h2');
      const anchor = document.createElement('a');
      anchor.href = item.url;
      anchor.textContent = item.title;
      heading.appendChild(anchor);
      article.appendChild(heading);
      appendText(article, 'p', item.context, 'result-meta');
      appendText(article, 'p', excerpt, 'result-excerpt');
      entry.appendChild(article);
      results.appendChild(entry);
    }
    if (matches.length > shown.length) {
      appendText(status, 'span', ` Showing the first ${shown.length}.`, 'result-limit');
    }
  };

  fetch('search-index.json', {credentials: 'same-origin'})
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(index => show(index.documents))
    .catch(() => {
      status.textContent = 'Search is temporarily unavailable. Browse by series or use the Timeline.';
    });
})();
