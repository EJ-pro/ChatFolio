import React, { useEffect, useRef } from "react";
import mermaid from "mermaid";

// Initialize Mermaid
mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  securityLevel: 'loose',
  themeVariables: {
    primaryColor: '#10b981',
    primaryTextColor: '#fff',
    primaryBorderColor: '#10b981',
    lineColor: '#64748b',
    secondaryColor: '#3b82f6',
    tertiaryColor: '#1f2937',
    mainBkg: '#0f172a',
    nodeBorder: '#1e293b',
    clusterBkg: '#1e293b',
    clusterBorder: '#334155',
    defaultLinkColor: '#64748b',
    titleColor: '#e2e8f0',
    edgeLabelBackground: '#0f172a',
    actorBkg: '#1e293b',
    actorBorder: '#3b82f6',
    actorTextColor: '#e2e8f0',
    actorLineColor: '#3b82f6',
    signalColor: '#10b981',
    signalTextColor: '#e2e8f0',
    labelBoxBkgColor: '#1e293b',
    labelBoxBorderColor: '#10b981',
    loopTextColor: '#e2e8f0',
    noteBkgColor: '#1e293b',
    noteBorderColor: '#eab308',
    noteTextColor: '#e2e8f0'
  }
});

const MermaidDiagram = ({ chart }) => {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.removeAttribute("data-processed");
      mermaid.render("mermaid-svg-" + Math.random().toString(36).slice(2, 11), chart).then((result) => {
        ref.current.innerHTML = result.svg;
      });
    }
  }, [chart]);

  return <div ref={ref} className="flex justify-center w-full" />;
};

export default MermaidDiagram;
