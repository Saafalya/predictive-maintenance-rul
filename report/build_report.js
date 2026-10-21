// Original-draft builder. The submitted report is built by build_report_edited.js from edited_content.json.
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
    run('Unplanned equipment failure is one of the largest sources of downtime and safety risk in aviation, manufacturing and energy systems. Predictive maintenance (PdM) replaces fixed service intervals with decisions based on the measured health of a machine, and its central quantity is the Remaining Useful Life (RUL): the number of operating cycles left before failure. This report presents a deep learning pipeline that estimates RUL directly from multivariate time-series sensor data, evaluated on the NASA C-MAPSS turbofan engine benchmark. Raw sensor streams are filtered to 14 informative channels, min-max normalised, labelled with a piece-wise linear RUL target capped at 125 cycles and converted into 30-cycle sliding windows. Under one shared pipeline we compare two classical baselines (Linear Regression and Random Forest) with three deep models: a 1D Convolutional Neural Network (1D-CNN), a stacked Long Short-Term Memory (LSTM) network, and a hybrid CNN-LSTM with additive temporal attention. Models are scored with Root Mean Squared Error (RMSE) and the asymmetric PHM08 score, which penalises late predictions more than early ones, averaged over five seeds. The CNN-LSTM with attention achieves the lowest RMSE on both subsets studied: 13.37 cycles on FD001 and 11.88 on FD003, against 14.99 and 16.26 for the best classical baseline. The plain LSTM, however, obtains the best PHM08 score on both subsets, and on FD001 the gap between the two recurrent models is within seed-to-seed variation. An ablation shows that the RUL cap affects error as much as the choice of architecture, and attention analysis shows that the model places 76% of its weight on the most recent cycle of each window.', { size: 18 }),
  ] }),
  new Paragraph({ spacing: { after: 120, line: 240 }, alignment: AlignmentType.JUSTIFIED, children: [
    run('Index Terms: ', { bold: true, size: 18 }),
    run('predictive maintenance, remaining useful life, multivariate time series, prognostics and health management, LSTM, convolutional neural networks, attention, C-MAPSS, deep learning.', { size: 18 }),
  ] }),
];

// ---------- I. Introduction ----------
const intro = [
  sectionHead('I. Introduction'),
  ...body(
    'Industrial maintenance usually follows one of three strategies. Reactive maintenance repairs a machine only after it breaks, which leads to long and expensive downtime. Preventive maintenance services machines at fixed intervals, which is safer but throws away the remaining life of healthy parts. Predictive maintenance monitors the actual condition of the asset through sensors and intervenes only when degradation is detected. Low-cost sensing and Industry 4.0 data platforms now produce continuous streams of temperature, pressure, vibration and speed readings, which makes data-driven predictive maintenance practical at scale.',
    'The key quantity in predictive maintenance is the Remaining Useful Life (RUL) of a component. Estimating RUL from multivariate sensor data is hard for four reasons. Sensors are noisy and strongly correlated with each other. Readings shift with operating conditions such as altitude and throttle setting, independently of wear. Degradation is gradual and non-linear, and it is barely visible in the early life of a machine. Finally, an error in one direction matters more than the other: predicting failure too late can be catastrophic, while predicting it too early only costs a slightly premature repair.',
    'Deep learning models learn temporal features directly from raw sequences, removing much of the manual feature engineering that classical prognostics depends on. Convolutional networks capture short local patterns across sensors, while recurrent networks such as the LSTM model the longer trend of degradation over many cycles. This project studies how far these models improve on classical baselines when every model is trained under the same pre-processing and evaluation protocol.',
  ),
  subHead('A. Problem Statement'),
  ...body('Given the multivariate sensor history of an engine up to its current cycle, predict the number of cycles remaining before failure, as accurately as possible and with a preference for early rather than late errors.'),
  subHead('B. Objectives'),
  bullet('Build a reproducible pre-processing pipeline for C-MAPSS: sensor selection, condition-wise normalisation, RUL capping and sliding-window generation.'),
  bullet('Implement and train three deep learning models (1D-CNN, LSTM, and CNN-LSTM with attention) for RUL regression.'),
  bullet('Compare them against Linear Regression and Random Forest baselines using RMSE and the PHM08 score.'),
  bullet('Study the effect of key design choices (window length and RUL cap) and interpret model behaviour with prediction trajectories and attention weights.'),
  subHead('C. Scope and Organisation'),
  ...body('The study uses the simulated NASA C-MAPSS dataset and focuses on point estimates of RUL. Section II reviews related work. Section III describes the dataset, pre-processing, model architectures and training setup. Section IV presents quantitative and qualitative results with a comparative study. Section V concludes and outlines future work.'),
];

// ---------- II. Literature Review ----------
const lit = [
  sectionHead('II. Literature Review'),
  subHead('A. Prognostics and Predictive Maintenance'),
  ...body(
    'Early prognostics relied on physics-based degradation models and statistical approaches such as similarity-based matching and regression on hand-crafted health indicators. Lei et al. [1] review the complete prognostics pipeline, from data acquisition and health-indicator construction to RUL prediction, and observe that data-driven methods are preferred whenever an accurate physical model of the asset is unavailable. Carvalho et al. [2] survey machine learning for predictive maintenance and report that Random Forests, Support Vector Machines and artificial neural networks are the most frequently used techniques.',
  ),
  subHead('B. The C-MAPSS Benchmark'),
  ...body(
    'Saxena et al. [3] created the C-MAPSS dataset by simulating damage propagation in turbofan engines under varying operating conditions and fault modes, and it has since become the standard benchmark for RUL estimation. Ramasso and Saxena [4] analysed the methods applied to it and stressed that results are only comparable when pre-processing and metrics are consistent, introducing the PHM08 score as a common measure alongside RMSE.',
  ),
  subHead('C. Convolutional Approaches'),
  ...body(
    'Heimes [5] applied recurrent neural networks to the 2008 PHM challenge, an early demonstration of neural models for this task. Babu et al. [6] were among the first to use a deep CNN for RUL regression, treating windows of sensor readings as two-dimensional inputs and outperforming shallow regressors. Li et al. [7] extended this with a deeper one-dimensional CNN over time windows, achieving strong results on all four C-MAPSS subsets without hand-crafted features.',
  ),
  subHead('D. Recurrent and Attention-Based Approaches'),
  ...body(
    'Because degradation is a temporal process, recurrent models are a natural fit. The LSTM [8] uses gated memory cells to avoid the vanishing gradients of plain recurrent networks and can capture long-range dependencies. Zheng et al. [9] showed that stacked LSTM layers estimate RUL more accurately than CNN and classical baselines on C-MAPSS. Malhotra et al. [10] used an LSTM encoder-decoder for unsupervised anomaly detection on multi-sensor data, showing that reconstruction error can serve as a health indicator. The attention mechanism [11] lets a model weight the most informative time steps, and hybrid CNN-LSTM models with attention have been reported to improve both accuracy and interpretability.',
  ),
  subHead('E. Research Gap'),
  ...body(
    'Most studies report a single model, often on a single subset and with different pre-processing choices, which makes it hard to tell whether gains come from the architecture or from the pipeline. This project trains classical and deep models under one shared pipeline (the same sensors, normalisation, windows, RUL cap and metrics), adds an ablation of window length and RUL cap, and pairs the numbers with qualitative error analysis. Table I summarises the most relevant prior work.',
  ),
  ...tableCaption('Summary of Related Work'),
  ...table(['Ref.', 'Method', 'Dataset', 'Key Contribution'], [
    ['[5]', 'Recurrent neural network', 'PHM08', 'Early neural RUL estimation'],
    ['[6]', 'Deep 2D CNN', 'C-MAPSS', 'First CNN-based RUL regression'],
    ['[7]', '1D-CNN with time windows', 'C-MAPSS', 'Deeper CNN, strong results on all subsets'],
    ['[9]', 'Stacked LSTM', 'C-MAPSS', 'Temporal modelling beats CNN and ML baselines'],
    ['[10]', 'LSTM encoder-decoder', 'Multi-sensor', 'Unsupervised health indicator'],
    ['This work', 'CNN-LSTM + attention', 'C-MAPSS', 'Unified comparison of ML and DL models'],
  ], [1300, 2800, 1700, 4280]),
];

// ---------- III. Methodology ----------
const method = [
  sectionHead('III. Methodology'),
  subHead('A. System Overview'),
  ...body('Fig. 1 shows the complete pipeline. Raw sensor readings are cleaned and normalised, cut into fixed-length windows, passed to a learned model that outputs an RUL estimate, and finally compared with a maintenance threshold to decide whether service should be scheduled.'),
  ...figure('block_diagram.png', 640, 163, 'Block diagram of the proposed predictive maintenance pipeline. The same pre-processing and windowing feed every model, so differences in results come from the model alone.'),
  subHead('B. Dataset Description'),
  ...body(
    'We use the NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) dataset [3]. Each engine starts in a healthy state with unknown manufacturing variation and initial wear, and degrades until failure. Each row is one operating cycle and contains the engine identifier, the cycle number, three operational settings and 21 sensor readings covering temperatures, pressures, fan and core speeds, and fuel-flow ratios. In the training set every engine runs to failure; in the test set the series stops some time before failure, and the true RUL at the last cycle is provided separately. Table II lists the four subsets. FD001 is used as the primary benchmark and FD003 for a second comparison.',
  ),
  ...tableCaption('C-MAPSS Dataset Subsets'),
  ...table(['Subset', 'Train Engines', 'Test Engines', 'Operating Conditions', 'Fault Modes'], [
    ['FD001', '100', '100', '1', '1 (HPC)'],
    ['FD002', '260', '259', '6', '1 (HPC)'],
    ['FD003', '100', '100', '1', '2 (HPC, Fan)'],
    ['FD004', '248', '248', '6', '2 (HPC, Fan)'],
  ], [1800, 1900, 1900, 2380, 2100]),
  subHead('C. Data Pre-processing'),
  dash([{ b: 'Sensor selection. ' }, 'Seven sensors that are constant or nearly constant in FD001 (s1, s5, s6, s10, s16, s18, s19) are dropped, leaving 14 informative channels.']),
  dash([{ b: 'Normalisation. ' }, 'Min-max scaling to [0, 1] is fitted on the training engines only, and applied per operating condition for the multi-condition subsets.']),
  dash([{ b: 'RUL labelling. ' }, 'RUL = last cycle - current cycle, clipped at 125 cycles. This piece-wise linear target reflects that degradation is not observable early in an engine\'s life.']),
  dash([{ b: 'Windowing. ' }, 'Sliding windows of 30 cycles with stride 1 give inputs of shape 30 x 14. For the test set the last window of each engine is used.']),
  dash([{ b: 'Validation split. ' }, '20% of training engines, split by engine ID so that no engine appears in both sets, are held out for early stopping and tuning.']),
  subHead('D. Model Architectures'),
  ...body(
    [{ b: 'Baselines. ' }, 'Linear Regression and a Random Forest Regressor (200 trees, minimum 5 samples per leaf) are trained on flattened windows, giving a reference point without temporal modelling.'],
    [{ b: '1D-CNN. ' }, 'Two Conv1D layers (64 filters, kernel sizes 5 and 3, ReLU) extract local patterns across time and sensors, whose output is flattened (keeping the position of each time step) and passed to a 64-unit dense layer, dropout of 0.3 and a single linear output.'],
    [{ b: 'LSTM. ' }, 'Two stacked LSTM layers with 64 and 32 units model the degradation trend over the window, followed by dropout of 0.2, a 32-unit dense layer and a linear output.'],
    [{ b: 'Proposed CNN-LSTM with attention. ' }, 'A Conv1D block (64 filters, kernel 3) first extracts local features at each time step. An LSTM layer (64 units, returning the full sequence) encodes temporal dependencies. A Bahdanau-style additive attention layer then computes a weight for each of the 30 time steps and forms a context vector as their weighted sum, which a dense regression head maps to the RUL estimate. The attention weights also make the model\'s focus inspectable.'],
  ),
  subHead('E. Training Setup'),
  ...body('All deep models are trained with the settings in Table III. Each configuration is trained with five random seeds (model initialisation and batch order) on a fixed engine-level train/validation split, and we report the mean and standard deviation. Linear Regression is deterministic, so it is run once.'),
  ...tableCaption('Training Hyperparameters'),
  ...table(['Parameter', 'Value'], [
    ['Framework', 'Python 3, PyTorch, scikit-learn'],
    ['Hardware', '4-core CPU, no GPU'],
    ['Loss function', 'Mean Squared Error on RUL / 125 (target scaled to [0, 1])'],
    ['Optimiser', 'Adam [12], learning rate 1e-3'],
    ['Batch size / max epochs', '256 / 150'],
    ['Early stopping', 'Patience 20 on validation MSE, best weights restored'],
    ['Window length / RUL cap', '30 cycles / 125 cycles'],
    ['Seeds per configuration', '5'],
  ], [4000, 6080]),
  subHead('F. Evaluation Metrics'),
  ...body(
    'Let d = RUL_pred - RUL_true for each test engine. Root Mean Squared Error, RMSE = sqrt( (1/N) Σ d² ), penalises early and late errors equally.',
    'The PHM08 score [3], s = Σ (e^(-d/13) - 1) for d < 0 and Σ (e^(d/10) - 1) for d ≥ 0, grows faster for late predictions (d > 0) because they are more dangerous in practice. Lower values are better for both metrics.',
  ),
];

// ---------- IV. Results and Discussion ----------
const results = [
  sectionHead('IV. Results and Discussion'),
  subHead('A. Quantitative Results'),
  ...body('Table IV reports test-set performance on FD001 and FD003. Deep models and the Random Forest are averaged over five seeds; Linear Regression is deterministic and run once. Params is the number of trainable parameters.'),
  ...tableCaption('Comparative Results on the Test Set (mean ± std over 5 seeds)'),
  ...table(['Model', 'RMSE FD001', 'Score FD001', 'RMSE FD003', 'Score FD003', 'Params'],
    MODEL_ORDER.map(m => [m, ms('FD001', m, 'rmse', 2), ms('FD001', m, 'score', 0), ms('FD003', m, 'rmse', 2), ms('FD003', m, 'score', 0), kparams(m)]),
    [2580, 1500, 1500, 1500, 1500, 1500]),
  ...body(
    'All three deep models outperform both classical baselines on RMSE. The proposed CNN-LSTM with attention has the lowest RMSE on both subsets: 13.37 ± 0.35 on FD001 and 11.88 ± 0.70 on FD003. This is 10.8% and 26.9% lower than Linear Regression, the stronger of the two baselines, and 2.0% and 3.9% lower than the plain LSTM.',
    'Two results differ from what we expected. First, Linear Regression beats the Random Forest on both subsets (14.99 against 15.91 on FD001). A likely reason is that the flattened input has 420 strongly correlated features, which suits a linear model, while tree ensembles predict averages of training targets and tend to pull extreme RUL values towards the middle. Second, the plain LSTM, not the proposed model, has the best PHM08 score on both subsets (305 on FD001 and 261 on FD003). Since PHM08 punishes late predictions exponentially, this means the LSTM makes fewer large late errors even though its average error is slightly higher. On FD001 the RMSE gap between the two recurrent models (0.27 cycles) is smaller than the LSTM\'s own seed-to-seed standard deviation (0.52), so the two should be regarded as comparable there; on FD003 the gap is larger.',
    'The advantage of the deep models is larger on FD003, which contains two fault modes. Linear Regression and the Random Forest lose 1.3 to 1.5 cycles of RMSE from FD001 to FD003, while the recurrent models improve, suggesting that sequence models cope better with more varied degradation patterns. FD003 also has more training windows (17,273 against 13,980), which benefits the larger models.',
  ),
  subHead('B. Ablation Study'),
  ...body('Table V varies the window length and RUL cap for the proposed model on FD001 while keeping all other settings fixed (mean ± std over three seeds). To keep rows comparable, every setting is scored against the same target, the true RUL capped at 125 cycles.'),
  ...tableCaption('Effect of Window Length and RUL Cap (CNN-LSTM + Attention, FD001)'),
  ...table(['Window Length', 'RUL Cap', 'RMSE', 'Score'],
    R.ablation.map(r => [String(r.window), r.cap === null ? 'none' : String(r.cap), pm(r.rmse_mean, r.rmse_std, 2), pm(r.score_mean, r.score_std, 0)]),
    [2520, 2520, 2520, 2520]),
  ...body(
    'A 20-cycle window is clearly too short (RMSE 15.96), while 30 and 40 cycles perform almost identically (13.31 and 13.49), so 30 cycles is a sufficient history. The RUL cap matters more. Training without a cap is by far the worst setting (RMSE 28.30): the model learns to predict values well above 125 for healthy engines, which it cannot justify from sensor data. A cap of 115 gives a lower error than 125 (12.66 against 13.31), and 130 a higher one (14.58). Part of this effect comes from scoring every row against the cap-125 target, which favours models whose predictions stay below 125. We keep 125 as the main setting because it was fixed in advance following the literature, and choosing it from test results would bias the comparison in Table IV.',
  ),
  subHead('C. Qualitative Results'),
  ...body('Fig. 2 compares predicted and actual RUL for all 100 FD001 test engines (seed 0, test RMSE 13.51). Predictions are tight for engines close to failure: the RMSE is 5.40 cycles for engines with fewer than 50 cycles left, against 13.09 for engines with 100 or more. This is the useful direction for maintenance, since accuracy matters most just before failure. Twelve of the 100 engines have an absolute error above 20 cycles, almost all in the mid and high RUL range, and 61% of predictions are later than the true value, which explains the PHM08 penalty discussed above.'),
  ...figure('fig_pred_vs_actual.png', 560, 266, 'Predicted versus actual RUL for the FD001 test engines (CNN-LSTM with attention, seed 0), sorted by actual RUL.'),
  ...body('Fig. 3 follows held-out validation engine 2 over its full life of 287 cycles (validation engines, unlike test engines, run to failure). The prediction stays at the cap during the healthy phase, begins to fall around cycle 100, before the start of the labelled decline at cycle 162, and then tracks the decline to failure with an RMSE of 7.44 cycles. Declining early means the model warns before the label does, which is the safe direction.'),
  ...figure('fig_engine_trajectory.png', 560, 266, 'RUL prediction over the life of FD001 validation engine 2. The prediction falls slightly before the labelled knee point and then follows the linear decline.'),
  ...body('Fig. 4 shows training and validation loss of the proposed model. Both fall quickly in the first ten epochs and then level off together with no widening gap, so the model does not over-fit; early stopping restored the weights from the best validation epoch.'),
  ...figure('fig_loss_curves.png', 560, 266, 'Training and validation MSE loss (log scale) of the CNN-LSTM with attention on FD001, seed 0.'),
  ...body('Fig. 5 shows the mean attention weight per time step over all validation windows. The model places 76% of its attention on the current cycle and 89% on the last five, with almost no weight on cycles older than about fifteen steps. The LSTM state at the final step already summarises the history, so attention mostly acts as a learned read-out of that state with a small correction from the preceding cycles. This also explains why the gain over the plain LSTM is small.'),
  ...figure('fig_attention.png', 560, 224, 'Mean attention weight per time step within the 30-cycle window (FD001 validation windows, seed 0).'),
  subHead('D. Discussion'),
  ...body(
    'The results support three conclusions. First, temporal modelling matters: every deep model beats both classical baselines on RMSE under the same pipeline, and the margin grows on the more complex FD003 subset. Second, the proposed CNN-LSTM with attention gives the lowest average error, but its gain over a well-trained LSTM is modest, and the LSTM is better on the safety-weighted PHM08 score. Where late warnings are costly, the plain LSTM is therefore a strong and simpler choice. Third, pre-processing choices such as the RUL cap change the error as much as the architecture does, so a shared pipeline is essential for a fair comparison.',
    'Training details also mattered as much as architecture. In a first run with unscaled RUL targets and a short early-stopping patience, two of three LSTM seeds collapsed to predicting the mean RUL (test RMSE above 40), and a 1D-CNN with global average pooling, which discards the position of each time step, performed worse than the Random Forest. Scaling the target to [0, 1], increasing the patience and flattening the convolutional output fixed both problems. These changes were checked on validation error only.',
    'The study has limitations. C-MAPSS is simulated, and real fleets show sensor drift, missing data and maintenance events that the benchmark does not contain. Only the single-condition subsets FD001 and FD003 were evaluated. The models give point estimates without a measure of confidence, which a maintenance planner would need, and the late-prediction rate (61% on FD001) shows that an explicit safety margin or an asymmetric loss would be needed in practice.',
  ),
];

// ---------- V. Conclusion ----------
const conclusion = [
  sectionHead('V. Conclusion'),
  ...body(
    'This report presented a deep learning approach to predictive maintenance that estimates the Remaining Useful Life of turbofan engines from multivariate sensor data. Using one shared pipeline of sensor selection, normalisation, RUL capping and sliding windows, we compared two classical baselines with a 1D-CNN, a stacked LSTM and a hybrid CNN-LSTM with attention over five seeds. All deep models outperformed the baselines. The CNN-LSTM with attention achieved the lowest RMSE on both subsets (13.37 on FD001 and 11.88 on FD003), while the plain LSTM achieved the best PHM08 score (305 and 261), so the two recurrent models are the strongest candidates and the better choice depends on whether average error or late-prediction risk matters more. The ablation showed that 30 cycles of history are sufficient and that the RUL cap is as influential as the architecture.',
    'Future work will extend the evaluation to the multi-condition subsets FD002 and FD004, train with an asymmetric loss that directly penalises late predictions, test Transformer-based sequence models, add uncertainty estimation through Monte Carlo dropout or deep ensembles so that each prediction carries a confidence interval, validate on real industrial data, and deploy the model as a real-time monitoring dashboard.',
  ),
];

// ---------- References ----------
const refs = [
  'Y. Lei, N. Li, L. Guo, N. Li, T. Yan, and J. Lin, "Machinery health prognostics: A systematic review from data acquisition to RUL prediction," Mech. Syst. Signal Process., vol. 104, pp. 799-834, 2018.',
  'T. P. Carvalho, F. A. Soares, R. Vita, R. P. Francisco, J. P. Basto, and S. G. Alcalá, "A systematic literature review of machine learning methods applied to predictive maintenance," Comput. Ind. Eng., vol. 137, 106024, 2019.',
  'A. Saxena, K. Goebel, D. Simon, and N. Eklund, "Damage propagation modeling for aircraft engine run-to-failure simulation," in Proc. Int. Conf. Prognostics and Health Management (PHM), 2008, pp. 1-9.',
  'E. Ramasso and A. Saxena, "Performance benchmarking and analysis of prognostic methods for CMAPSS datasets," Int. J. Prognostics Health Manag., vol. 5, no. 2, 2014.',
  'F. O. Heimes, "Recurrent neural networks for remaining useful life estimation," in Proc. Int. Conf. Prognostics and Health Management (PHM), 2008, pp. 1-6.',
  'G. S. Babu, P. Zhao, and X.-L. Li, "Deep convolutional neural network based regression approach for estimation of remaining useful life," in Proc. Int. Conf. Database Systems for Advanced Applications (DASFAA), 2016, pp. 214-228.',
  'X. Li, Q. Ding, and J.-Q. Sun, "Remaining useful life estimation in prognostics using deep convolution neural networks," Reliab. Eng. Syst. Saf., vol. 172, pp. 1-11, 2018.',
  'S. Hochreiter and J. Schmidhuber, "Long short-term memory," Neural Comput., vol. 9, no. 8, pp. 1735-1780, 1997.',
  'S. Zheng, K. Ristovski, A. Farahat, and C. Gupta, "Long short-term memory network for remaining useful life estimation," in Proc. IEEE Int. Conf. Prognostics and Health Management (ICPHM), 2017, pp. 88-95.',
  'P. Malhotra, A. Ramakrishnan, G. Anand, L. Vig, P. Agarwal, and G. Shroff, "LSTM-based encoder-decoder for multi-sensor anomaly detection," arXiv:1607.00148, 2016.',
  'A. Vaswani et al., "Attention is all you need," in Proc. Advances in Neural Information Processing Systems (NeurIPS), 2017, pp. 5998-6008.',
  'D. P. Kingma and J. Ba, "Adam: A method for stochastic optimization," in Proc. Int. Conf. Learning Representations (ICLR), 2015.',
];
const references = [
  sectionHead('References'),
  ...refs.map((r, i) => new Paragraph({ spacing: { after: 40 }, indent: { left: 400, hanging: 400 }, alignment: AlignmentType.JUSTIFIED,
    children: [run(`[${i + 1}]\t${r}`, { size: 16 })] })),
];

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
    children: [...cover, ...titleBlock, ...intro, ...lit, ...method, ...results, ...conclusion, ...references],
  }],
});

Packer.toBuffer(doc).then(b => { fs.writeFileSync('DL_ESE_Project_Report_Predictive_Maintenance.docx', b); console.log('written'); });
