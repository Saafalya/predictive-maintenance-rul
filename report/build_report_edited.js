// Builds the DL ESE report in the same layout as the reference (MARS) report.
// Usage: node build_report.js   (run from this folder)
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Header, Footer, AlignmentType,
  PageNumber, PageBreak, Table, TableRow, TableCell, WidthType, ShadingType,
  BorderStyle, LevelFormat,
} = require('docx');

const img = (f) => fs.readFileSync(f);

// Real experiment output from code/run_experiments.py.
// Text from the edited report, laid out with the original formatting.
const E = JSON.parse(fs.readFileSync('edited_content.json', 'utf8'));
const R = JSON.parse(fs.readFileSync('../results/results.json', 'utf8'));
const MODEL_ORDER = ['Linear Regression', 'Random Forest', '1D-CNN', 'LSTM', 'CNN-LSTM + Attention'];
const fmt = (x, d) => x.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
const pm = (m, sd, d) => sd > 0 ? `${fmt(m, d)} \u00B1 ${fmt(sd, d)}` : fmt(m, d);
const ms = (sub, m, k, d) => pm(R.main[sub][m][`${k}_mean`], R.main[sub][m][`${k}_std`], d);
const kparams = (m) => { const p = R.main.FD001[m].params; return p == null ? '-' : `${(p / 1000).toFixed(1)} K`; };
const FONT = 'Times New Roman';
const TITLE = 'AI-Based Predictive Maintenance Using Multivariate Sensor Data';
const SUBTITLE = 'Deep Learning-Based Remaining Useful Life Estimation of Turbofan Engines on NASA C-MAPSS';
const TEXT_W = 10080; // Letter width minus 0.75" margins, in DXA

// Placeholder values are highlighted yellow so they are easy to find and replace.
const run = (t, o = {}) => new TextRun({ text: t, size: o.size ?? 21, bold: o.bold, italics: o.italic, smallCaps: o.sc, color: o.color, highlight: o.ph ? 'yellow' : undefined });
// Paragraph from segments: strings are plain, {ph: '...'} is a highlighted placeholder, {b: '...'} is bold.
const seg = (s) => typeof s === 'string' ? run(s) : s.ph ? run(s.ph, { ph: true }) : run(s.b, { bold: true });
const para = (parts, o = {}) => new Paragraph({
  alignment: o.align ?? AlignmentType.JUSTIFIED,
  indent: o.first ? { firstLine: 202 } : undefined,
  spacing: { after: o.after ?? 0, line: 252 },
  children: (Array.isArray(parts) ? parts : [parts]).map(seg),
});
// Body text: first paragraph after a heading is flush, the rest get a first-line indent (as in the template).
const body = (...ps) => ps.map((t, i) => para(t, { first: i > 0 }));

const centered = (children, after = 0, before = 0, keepNext = false) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before, after }, keepNext, children });
const sectionHead = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 120 }, children: [run(t, { sc: true })] });
const subHead = (t) => new Paragraph({ spacing: { before: 160, after: 60 }, children: [run(t, { italic: true })] });
const bullet = (parts) => new Paragraph({ numbering: { reference: 'num', level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { line: 252 }, children: (Array.isArray(parts) ? parts : [parts]).map(seg) });
const dash = (parts) => new Paragraph({ numbering: { reference: 'dash', level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { line: 252 }, children: (Array.isArray(parts) ? parts : [parts]).map(seg) });

let tableNo = 0, figNo = 0;
const ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
const tableCaption = (t) => [
  centered([run(`TABLE ${ROMAN[tableNo++]}`, { size: 16, sc: true })], 0, 200, true),
  centered([run(t, { size: 16, sc: true })], 80, 0, true),
];
function figure(file, w, h, captionText) {
  figNo++;
  return [
    centered([new ImageRun({ type: 'png', data: img(file), transformation: { width: w, height: h } })], 60, 160),
    new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 160 }, children: [run(`Fig. ${figNo}. `, { size: 16 }), run(captionText, { size: 16 })] }),
  ];
}

const line = { style: BorderStyle.SINGLE, size: 4, color: '000000' };
const none = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
// Booktabs-style table: rule above and below the header, rule at the bottom.
function table(headers, rows, widths, phCols = []) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, i, r, last) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    borders: { top: r === 0 ? line : none, bottom: r === 0 || last ? line : none, left: none, right: none },
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
      children: [run(t, { size: 17, bold: r === 0, ph: r > 0 && phCols.includes(i) })] })],
  });
  return [new Table({
    alignment: AlignmentType.CENTER, width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [headers, ...rows].map((r, ri) => new TableRow({ tableHeader: ri === 0, children: r.map((c, i) => cell(c, i, ri, ri === rows.length)) })),
  }), new Paragraph({ spacing: { after: 160 }, children: [] })];
}

// ---------- Cover page (matches template page 1) ----------
const coverRule = () => new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: '000000', space: 1 } }, spacing: { after: 240 }, children: [] });
const twoCol = (left, right, w = 4000) => new Table({
  alignment: AlignmentType.CENTER, width: { size: 2 * w, type: WidthType.DXA }, columnWidths: [w, w],
  borders: { top: none, bottom: none, left: none, right: none, insideHorizontal: none, insideVertical: none },
  rows: [new TableRow({ children: [left, right].map(lines => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders: { top: none, bottom: none, left: none, right: none },
    children: lines.map(l => new Paragraph({ alignment: AlignmentType.CENTER, children: [run(l.t, { size: l.size ?? 21, bold: l.bold, italic: l.italic })] })),
  })) })],
});

const cover = [
  new Paragraph({ spacing: { before: 400, after: 600 }, children: [new ImageRun({ type: 'png', data: img('sit_logo.png'), transformation: { width: 480, height: 76 } })] }),
  centered([run('DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING', { bold: true, size: 22 })], 600),
  coverRule(),
  centered([run('DEEP LEARNING PROJECT REPORT', { size: 22 })], 240),
  centered([run('AI-Based Predictive Maintenance', { size: 40 })], 120),
  centered([run('Using Multivariate Sensor Data for Remaining Useful Life Estimation', { size: 20 })], 120),
  new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: '000000', space: 1 } }, spacing: { after: 800 }, children: [] }),
  centered([run('Submitted by', { italic: true })], 400),
  twoCol([{ t: 'Saafalya Sengupta', bold: true, size: 26 }, { t: 'PRN 24070126158' }],
         [{ t: 'Ribhav Dhankani', bold: true, size: 26 }, { t: 'PRN 24070126150' }]),
  centered([run('AIML, Division C1')], 400, 160),
  centered([run('Faculty Coordinator', { italic: true })], 40),
  centered([run('Dr. Shrikrishna Kolhar', { bold: true })]),
  centered([run('Associate Professor', { italic: true })], 1000),
  centered([run('Academic Year 2026–27')]),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- Paper title + author block (template page 2) ----------
const author = (name, email) => [
  { t: name, size: 22 },
  { t: 'Department of Artificial Intelligence and Machine Learning', italic: true, size: 18 },
  { t: 'Symbiosis Institute of Technology, Symbiosis International', italic: true, size: 18 },
  { t: '(Deemed University)', italic: true, size: 18 },
  { t: 'Pune, Maharashtra, India', italic: true, size: 18 },
  { t: email, italic: true, size: 18 },
];
const titleBlock = [
  centered([run(TITLE, { size: 40 })], 200),
  twoCol(author('Saafalya Sengupta', 'saafalya.sengupta.btech2024@sitpune.edu.in'),
         author('Ribhav Dhankani', 'ribhav.dhankani.btech2024@sitpune.edu.in'), 5040),
  new Paragraph({ spacing: { before: 300, after: 120, line: 240 }, alignment: AlignmentType.JUSTIFIED, children: [
    run('Abstract: ', { bold: true, size: 18 }),
    run(E.abstract, { size: 18 }),
  ] }),
  new Paragraph({ spacing: { after: 120, line: 240 }, alignment: AlignmentType.JUSTIFIED, children: [
    run('Index Terms: ', { bold: true, size: 18 }),
    run(E.index, { size: 18 }),
  ] }),
];

// ---------- Body: text from the edited report (edited_content.json), original formatting ----------
const bodyBlocks = [];
let afterHeading = true;
for (const b of E.blocks) {
  if (b.k === 'sec') { bodyBlocks.push(sectionHead(b.t)); afterHeading = true; continue; }
  if (b.k === 'sub') { bodyBlocks.push(subHead(b.t)); afterHeading = true; continue; }
  if (b.k === 'body') { bodyBlocks.push(para(b.t, { first: !afterHeading })); afterHeading = false; continue; }
  if (b.k === 'num') bodyBlocks.push(bullet(b.t));
  else if (b.k === 'dash') bodyBlocks.push(dash([{ b: b.parts[0] }, b.parts[1]]));
  else if (b.k === 'lab') bodyBlocks.push(para([{ b: b.parts[0] }, b.parts[1]], { first: !afterHeading }));
  else if (b.k === 'tcap') { tableNo++; bodyBlocks.push(centered([run(b.t1, { size: 16, sc: true })], 0, 200, true), centered([run(b.t2, { size: 16, sc: true })], 80, 0, true)); }
  else if (b.k === 'table') {
    const n = b.rows[0].length, first = n === 2 ? 4000 : n === 4 && b.rows[0][0] === 'Ref.' ? 1300 : 2580;
    const widths = n === 2 ? [4000, 6080] : b.rows[0][0] === 'Ref.' ? [1300, 2800, 1700, 4280]
      : n === 4 ? [2520, 2520, 2520, 2520] : n === 5 ? [1800, 1900, 1900, 2380, 2100] : [2580, 1500, 1500, 1500, 1500, 1500];
    bodyBlocks.push(...table(b.rows[0], b.rows.slice(1), widths));
  }
  else if (b.k === 'fig') bodyBlocks.push(...figure(b.f, b.w, b.h, b.cap));
  else if (b.k === 'ref') { const n = bodyBlocks.filter(x => x._ref).length + 1;
    const p = new Paragraph({ spacing: { after: 40 }, indent: { left: 400, hanging: 400 }, alignment: AlignmentType.JUSTIFIED, children: [run(`[${n}]\t${b.t}`, { size: 16 })] });
    p._ref = true; bodyBlocks.push(p); }
  afterHeading = false;
}

// ---------- Header / footer ----------
// Cover page has its own (empty) header like the template; later pages carry the SIT logo.
const header = new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
  border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: 'A6192E', space: 4 } },
  children: [new ImageRun({ type: 'png', data: img('sit_logo.png'), transformation: { width: 190, height: 30 } })] })] });
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] });
const firstFooter = footer;

const doc = new Document({
  creator: 'Saafalya Sengupta, Ribhav Dhankani',
  title: TITLE,
  description: SUBTITLE,
  styles: { default: { document: { run: { font: FONT, size: 21 } } } },
  numbering: { config: [
    { reference: 'num', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 640, hanging: 320 } } } }] },
    { reference: 'dash', levels: [{ level: 0, format: LevelFormat.BULLET, text: '–', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 640, hanging: 320 } } } }] },
  ] },
  sections: [{
    properties: { titlePage: true, page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, bottom: 1080, left: 1080, right: 1080, header: 500, footer: 500 } } },
    headers: { default: header, first: new Header({ children: [new Paragraph({ children: [] })] }) },
    footers: { default: footer, first: firstFooter },
    children: [...cover, ...titleBlock, ...bodyBlocks],
  }],
});

Packer.toBuffer(doc).then(b => { fs.writeFileSync(process.argv[2] || 'DL_ESE_Project_Report_Predictive_Maintenance.docx', b); console.log('written'); });
