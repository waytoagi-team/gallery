// Inlined by build_html.py so the exported HTML remains usable offline.
const AtlasRanking = (() => {
  const valid = n => Number.isFinite(n) && n >= 0;
  function signal(c) {
    if (c.source === 'github') {
      if (c.githubKind === 'repository') return ['github:stars', c.stars];
      if (['pull_request', 'issue'].includes(c.githubKind)) return ['github:' + c.githubKind + ':reactions', c.reactions];
      return [null, null];
    }
    // Keep plays and likes in separate cohorts, including when a video lacks plays.
    const field = c.source === 'video' && c.views != null ? 'views' : 'likes';
    return [c.source + ':' + field, c[field]];
  }
  function assign(cases) {
    const groups = new Map();
    for (const c of cases) {
      c._hot = -1;
      const [group, value] = signal(c);
      if (group && valid(value)) {
        if (!groups.has(group)) groups.set(group, []);
        groups.get(group).push({c, value});
      }
    }
    for (const list of groups.values()) {
      list.sort((a, b) => a.value - b.value);
      for (let i = 0; i < list.length;) {
        let end = i + 1;
        while (end < list.length && list[end].value === list[i].value) end++;
        // Midrank percentile: ties are equal and do not depend on input order.
        // No activity is always 0; missing data remains -1. A singleton is neutral.
        const score = list[i].value === 0 ? 0 : list.length === 1 ? 0.5 : (i + end - 1) / 2 / (list.length - 1);
        for (let j = i; j < end; j++) list[j].c._hot = score;
        i = end;
      }
    }
    return cases;
  }
  return {signal, assign};
})();
if (typeof module !== 'undefined') module.exports = AtlasRanking;
