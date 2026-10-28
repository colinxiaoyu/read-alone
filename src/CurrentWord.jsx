import { useLayoutEffect, useRef } from 'react';

export default function CurrentWord({ word, highlighted }) {
  const ref = useRef(null);
  useLayoutEffect(() => {
    const node = ref.current;
    const parent = node.parentElement;
    const fit = () => {
      const preferred = Math.min(window.innerWidth * .105, 410);
      node.style.fontSize = `${preferred}px`;
      if (node.scrollWidth > parent.clientWidth) {
        node.style.fontSize = `${preferred * Math.max(20, parent.clientWidth - 8) / node.scrollWidth}px`;
      }
    };
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(parent);
    return () => observer.disconnect();
  }, [word]);
  return <h2 id="current-word" ref={ref} className={highlighted ? 'is-current' : undefined} lang="en">{word}</h2>;
}
