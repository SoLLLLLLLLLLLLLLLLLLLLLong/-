function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("\n", "&#10;");
}

function formatInline(text) {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/~~([^~]+)~~/g, "<del>$1</del>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noreferrer">$1</a>'
    );
}

function renderTable(lines) {
  if (lines.length < 2 || !/^\s*\|?[\s:-]+\|[\s|:-]*$/.test(lines[1])) {
    return "";
  }

  const rows = lines.map((line) =>
    line
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim())
  );

  const headers = rows[0]
    .map((cell) => `<th>${formatInline(cell)}</th>`)
    .join("");
  const body = rows
    .slice(2)
    .map(
      (row) =>
        `<tr>${row.map((cell) => `<td>${formatInline(cell)}</td>`).join("")}</tr>`
    )
    .join("");

  return `<div class="markdown-table-wrap"><table><thead><tr>${headers}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function renderBlock(block) {
  const codeFenceMatch = block.match(/^```([\w-]*)\n?([\s\S]*?)```$/);
  if (codeFenceMatch) {
    const language = codeFenceMatch[1] || "text";
    const rawCode = codeFenceMatch[2].trimEnd();
    const code = escapeHtml(rawCode);
    return `
      <pre class="markdown-pre">
        <div class="markdown-pre-head">
          <span class="markdown-pre-label">${escapeHtml(language)}</span>
          <button type="button" class="code-copy-button" data-copy-code="1" data-code="${escapeAttribute(rawCode)}">复制代码</button>
        </div>
        <code>${code}</code>
      </pre>
    `;
  }

  if (/^---+$/.test(block.trim())) {
    return "<hr />";
  }

  const lines = block.split("\n");
  const table = renderTable(lines);
  if (table) {
    return table;
  }

  if (lines.every((line) => /^>\s?/.test(line))) {
    return `<blockquote>${lines
      .map((line) => formatInline(line.replace(/^>\s?/, "")))
      .join("<br />")}</blockquote>`;
  }

  if (lines.every((line) => /^(\-|\*)\s+/.test(line))) {
    const items = lines
      .map((line) => line.replace(/^(\-|\*)\s+/, ""))
      .map((line) => `<li>${formatInline(line)}</li>`)
      .join("");
    return `<ul>${items}</ul>`;
  }

  if (lines.every((line) => /^\d+\.\s+/.test(line))) {
    const items = lines
      .map((line) => line.replace(/^\d+\.\s+/, ""))
      .map((line) => `<li>${formatInline(line)}</li>`)
      .join("");
    return `<ol>${items}</ol>`;
  }

  const headingMatch = block.match(/^(#{1,4})\s+(.+)$/);
  if (headingMatch) {
    const level = headingMatch[1].length;
    return `<h${level}>${formatInline(headingMatch[2])}</h${level}>`;
  }

  return `<p>${lines.map((line) => formatInline(line)).join("<br />")}</p>`;
}

export function renderMarkdown(content) {
  const normalized = String(content || "").replace(/\r\n/g, "\n").trim();
  if (!normalized) {
    return "";
  }

  return normalized
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean)
    .map((block) => renderBlock(block))
    .join("");
}
