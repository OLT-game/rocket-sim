---
title: Rocket Sim (MathJax-enabled)
---

<!--
This page includes the repository's README.md so that LaTeX expressions
can be rendered via MathJax on GitHub Pages.

How it works:
- Jekyll's include_relative brings README.md content into this page.
- MathJax (loaded below) renders LaTeX written in $...$ or $$...$$.
-->

<!-- Load MathJax v3 -->
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

{% include_relative ../README.md %}
