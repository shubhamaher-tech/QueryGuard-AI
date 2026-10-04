import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(45, 755, "QueryGuard AI — System Handbook: Questions, Answers & Page-by-Page Guide")
            self.drawRightString(567, 755, "Confidential & Enterprise Light Edition")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(45, 747, 567, 747)

        # Footer (All pages)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(45, 42, 567, 42)
        
        self.drawString(45, 30, "QueryGuard AI: Autonomous Database Optimization • Privacy Guarantee 99.8% • Zero Disk Mutation")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(567, 30, page_text)
        self.restoreState()


def make_callout(text, title=None, bg_color="#F8FAFC", border_color="#0F766E", text_color="#1E293B"):
    styles = getSampleStyleSheet()
    t_style = ParagraphStyle(
        'CalloutTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor(border_color),
        spaceAfter=3
    )
    b_style = ParagraphStyle(
        'CalloutBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor(text_color)
    )
    content = []
    if title:
        content.append(Paragraph(title, t_style))
    content.append(Paragraph(text, b_style))
    
    t = Table([[content]], colWidths=[522])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor(border_color)),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ]))
    return t


def build_handbook_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=48,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()

    # Typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0F766E')
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#475569')
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor('#0F766E'),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.5,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=5
    )

    body_bold = ParagraphStyle(
        'Body_Bold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )

    table_body = ParagraphStyle(
        'TableBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )

    table_body_mono = ParagraphStyle(
        'TableBodyMono',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#0F766E')
    )

    story = []

    # =========================================================================
    # COVER / HEADER
    # =========================================================================
    story.append(Paragraph("QueryGuard AI", title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Complete Technical Handbook: Questions & Answers, Parameters, Algorithms & Page-by-Page Feature Guide", subtitle_style))
    story.append(Spacer(1, 8))

    # Metadata Block
    meta_data = [
        [
            Paragraph("<b>Document Type:</b> Official System Handbook & Q&A", table_body),
            Paragraph("<b>Target Audience:</b> New Engineers, DBAs, Architects", table_body),
            Paragraph("<b>Theme:</b> Enterprise Light (#F6F8FB)", table_body)
        ],
        [
            Paragraph("<b>Core Engine:</b> HypoPG + PyTorch GNN + SLM", table_body),
            Paragraph("<b>Privacy Guarantee:</b> 99.8% Masked Metadata", table_body),
            Paragraph("<b>Execution Safety:</b> Zero Disk Mutation", table_body)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[174, 174, 174])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Friendly Introduction Banner
    story.append(make_callout(
        "<b>Welcome to QueryGuard AI!</b> This handbook is written in friendly, plain English so that anyone—whether you are an experienced Database Administrator (DBA), a backend developer, or brand new to database engineering—can clearly understand the three core questions (Parameters, Algorithms, and Optimizations) and navigate every single page of the web dashboard with confidence.",
        title="Quick Purpose of This Handbook",
        bg_color="#F0FDF4",
        border_color="#16A34A",
        text_color="#14532D"
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # PART 1: CORE QUESTIONS & ANSWERS
    # =========================================================================
    story.append(Paragraph("Part 1: The Three Core Technical Questions & Answers", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0F766E'), spaceBefore=2, spaceAfter=8))

    # -------------------------------------------------------------------------
    # QUESTION 1
    # -------------------------------------------------------------------------
    story.append(Paragraph("Question 1: What Parameters Are We Using for Our Solution?", h2_style))
    story.append(Paragraph(
        "In QueryGuard AI, <b>parameters</b> are the specific configuration values, thresholds, and measurements that our system watches, tunes, and feeds into our intelligence engine. To make this easy to understand, we group them into four practical categories:",
        body_style
    ))
    story.append(Spacer(1, 4))

    params_data = [
        [Paragraph("Category", table_header), Paragraph("Key Parameters Used", table_header), Paragraph("What It Means in Simple Words", table_header)],
        [
            Paragraph("<b>1. Database Cost & Hardware Parameters</b>", table_body),
            Paragraph("• <code>seq_page_cost</code> (1.0)<br/>• <code>random_page_cost</code> (4.0)<br/>• <code>cpu_tuple_cost</code> (0.01)<br/>• <code>cpu_operator_cost</code> (0.0025)<br/>• <code>work_mem</code> (64MB)<br/>• <code>effective_cache_size</code> (4GB)", table_body_mono),
            Paragraph("These are PostgreSQL's internal physics rules. They tell the database how expensive it is to read an un-indexed disk page sequentially (cost 1.0) versus jumping randomly with an index (cost 4.0), and how much CPU effort is needed to process each row.", table_body)
        ],
        [
            Paragraph("<b>2. Workload & Telemetry Parameters</b>", table_body),
            Paragraph("• <code>calls</code> (execution count)<br/>• <code>mean_exec_time</code> (ms)<br/>• <code>p50, p95, p99 latency</code><br/>• <code>shared_blks_read</code><br/>• <code>shared_blks_hit</code> (cache hit ratio)<br/>• <code>slow_query_threshold</code> (100ms)", table_body_mono),
            Paragraph("Live heartbeat parameters collected from <code>pg_stat_statements</code>. They tell us which queries are executed millions of times, which queries cause sudden latency spikes (P95/P99), and whether data is found in RAM or dragging from slow disk.", table_body)
        ],
        [
            Paragraph("<b>3. Graph Neural Network (GNN) Parameters</b>", table_body),
            Paragraph("• Input vector: 16 dimensions<br/>• Hidden layer: 64 dimensions<br/>• GNN layers: 2 message-passing<br/>• Dropout rate: 0.2<br/>• Learning rate: 0.001 (Adam)<br/>• Decision Weights: Cost (0.42), Rows (0.28), Depth (0.18), Cache (0.12)", table_body_mono),
            Paragraph("The settings of our specialized AI model. The 16 input numbers describe each step of a query plan (rows, cost, operator type). The 2-layer GraphSAGE architecture reads the execution tree, and the decision weights mathematically rank what is hurting performance.", table_body)
        ],
        [
            Paragraph("<b>4. Privacy & Masking Parameters</b>", table_body),
            Paragraph("• Salted HMAC-SHA256 tokens<br/>• Masking target: 99.8% entropy<br/>• Table token format: <code>TBL_a1b2</code><br/>• Column token format: <code>COL_c3d4</code><br/>• Value masks: <code>[MASKED_INT]</code>", table_body_mono),
            Paragraph("The privacy guardrails. Customer names, passwords, and IDs are replaced with one-way scrambled tokens before any AI or human sees them. Zero customer records or plaintext credentials ever leave the local database.", table_body)
        ]
    ]
    params_table = Table(params_data, colWidths=[120, 160, 242])
    params_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(params_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # QUESTION 2
    # -------------------------------------------------------------------------
    story.append(Paragraph("Question 2: What Algorithms Are We Using?", h2_style))
    story.append(Paragraph(
        "Instead of using a generic, slow, and expensive cloud AI that hallucinates, QueryGuard AI combines four mathematically rigorous algorithms that run locally in milliseconds:",
        body_style
    ))
    story.append(Spacer(1, 4))

    algos_data = [
        [Paragraph("Algorithm Name", table_header), Paragraph("Technical Class", table_header), Paragraph("How It Works & Everyday Analogy", table_header)],
        [
            Paragraph("<b>1. Graph Neural Network (GraphSAGE / GCN)</b>", table_body),
            Paragraph("Deep Learning on Directed Acyclic Graphs (DAG)", table_body),
            Paragraph("<b>Analogy:</b> An X-ray radiologist reading an entire skeletal scan.<br/>A database query plan is not a flat sentence; it is a tree of operations (joins, filters, scans). GraphSAGE aggregates information from child steps up to parent steps, detecting invisible bottlenecks like un-indexed nested loops in sub-4ms.", table_body)
        ],
        [
            Paragraph("<b>2. AST Sanitization & Lexical Pseudonymizer</b>", table_body),
            Paragraph("Deterministic Compiler Parsing (SQLGlot)", table_body),
            Paragraph("<b>Analogy:</b> A diplomatic redaction marker.<br/>It parses SQL queries into an Abstract Syntax Tree (AST), strips comments and secrets, replaces literals with placeholders, and hashes table/column names into salted HMAC-SHA256 tokens in linear time O(N).", table_body)
        ],
        [
            Paragraph("<b>3. System-R Cost Search & Virtual Planner</b>", table_body),
            Paragraph("Dynamic Programming Optimization (PostgreSQL + HypoPG)", table_body),
            Paragraph("<b>Analogy:</b> A GPS recalculating the fastest route using a virtual bridge.<br/>HypoPG injects hypothetical index catalog entries into session RAM. PostgreSQL's System-R optimizer re-plans the query dynamically and calculates the exact Cost Delta: <br/><code>ΔC = ((Cost_before - Cost_after) / Cost_before) * 100%</code>.", table_body)
        ],
        [
            Paragraph("<b>4. Deterministic Rule Attribution Engine</b>", table_body),
            Paragraph("Symbolic Multi-Factor Attribution", table_body),
            Paragraph("<b>Analogy:</b> A forensic accountant checking line-by-line expenses.<br/>Calculates the exact disk and CPU footprint using formula: <code>(N_pages * seq_page_cost) + (N_tuples * cpu_tuple_cost)</code>. It combines GNN weights and database math so DBAs know exactly <i>why</i> a recommendation was made.", table_body)
        ]
    ]
    algos_table = Table(algos_data, colWidths=[120, 140, 262])
    algos_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(algos_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # QUESTION 3
    # -------------------------------------------------------------------------
    story.append(Paragraph("Question 3: What Are We Using to Optimize Our Solution?", h2_style))
    story.append(Paragraph(
        "To make QueryGuard AI ultra-fast, safe, and cost-effective, we optimize the solution across five key technical dimensions:",
        body_style
    ))
    story.append(Spacer(1, 4))

    opt_data = [
        [Paragraph("Optimization Technique", table_header), Paragraph("Technology Used", table_header), Paragraph("Performance & Safety Advantage", table_header)],
        [
            Paragraph("<b>1. Zero-Disk In-Memory Simulation</b>", table_body),
            Paragraph("PostgreSQL HypoPG Extension", table_body),
            Paragraph("Creating a real 10GB index in production takes minutes, locks tables, and consumes expensive disk storage. HypoPG creates <i>hypothetical</i> indexes in session RAM in <15ms with <b>0 bytes written to disk</b>. We can safely test 100 candidate indexes without risking production downtime.", table_body)
        ],
        [
            Paragraph("<b>2. Sub-4ms Local PyTorch GNN Inference</b>", table_body),
            Paragraph("PyTorch C++ Backend + ONNX Ready", table_body),
            Paragraph("Cloud LLMs take 2,000 to 5,000ms per API call and cost per token. Our local GraphSAGE model evaluates query plans in <b>sub-4 milliseconds</b> on standard CPU. It is 500x faster, completely private, and works without an internet connection.", table_body)
        ],
        [
            Paragraph("<b>3. Local Air-Gapped SLM Rewriter</b>", table_body),
            Paragraph("Ollama (Llama 3 / Mistral 8B)", table_body),
            Paragraph("When a query needs structural rewriting (e.g., converting an expensive correlated subquery into a clean JOIN), we run a local Small Language Model (SLM) strictly inside the customer's private Docker network. Zero query text ever leaves the company perimeter.", table_body)
        ],
        [
            Paragraph("<b>4. Non-Blocking Async Ingestion</b>", table_body),
            Paragraph("FastAPI Async Coroutines + AsyncPG", table_body),
            Paragraph("Telemetry polling from <code>pg_stat_statements</code> runs asynchronously in background worker threads. The database never suffers lock contention or CPU degradation while metrics are gathered.", table_body)
        ],
        [
            Paragraph("<b>5. Session-Scoped Virtual Execution</b>", table_body),
            Paragraph("PostgreSQL Transaction Isolation", table_body),
            Paragraph("When the user clicks 'Run Enhanced Query' in the UI, QueryGuard AI attaches the candidate index in an isolated sandbox session, re-runs the query optimizer, and validates that plan cost drops by 90%+ before any DBA approval.", table_body)
        ]
    ]
    opt_table = Table(opt_data, colWidths=[120, 130, 272])
    opt_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(opt_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # PART 2: PAGE-BY-PAGE DASHBOARD EXPLANATION
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("Part 2: Complete Page-by-Page Feature & Working Guide", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0F766E'), spaceBefore=2, spaceAfter=8))
    
    story.append(Paragraph(
        "This section walks through <b>every single page in the QueryGuard AI web interface</b>. It is written in simple, step-by-step language so any new team member or DBA can understand what the page does, what each feature and button does, and how it works under the hood.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # -------------------------------------------------------------------------
    # GLOBAL HEADER & NAVIGATION
    # -------------------------------------------------------------------------
    story.append(Paragraph("Global Interface: Top Header & Navigation Sidebar", h2_style))
    story.append(Paragraph(
        "<b>What it does:</b> The top header and left sidebar stay visible across all pages to give you continuous awareness of database health, security status, and fast one-click navigation.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Features & How they work:</b><br/>"
        "• <b>Connection Status Badge:</b> Displays a pale green pill saying <code>Connected (PG 16)</code>. It pings the backend every few seconds to confirm the target database is healthy and responding.<br/>"
        "• <b>Environment Indicator:</b> Displays <code>Local Sandbox</code> (pale amber), guaranteeing that all simulations run in an isolated test environment without touching live production data.<br/>"
        "• <b>Privacy Verification Pill:</b> Displays <code>Privacy Protected (99.8%)</code> in pale teal. Shows that the SQL sanitization gateway is actively stripping personal data and identifiers.<br/>"
        "• <b>Quick Analyze Query Button:</b> A bright teal button in the header that instantly takes you to the query inspection workspace from anywhere in the app.<br/>"
        "• <b>Sidebar Navigation:</b> Clean white sidebar with light gray hover states (#F1F5F9) and distinct dark icons for all 10 core pages.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # PAGE 1: OVERVIEW DASHBOARD
    # -------------------------------------------------------------------------
    story.append(Paragraph("Page 1: Overview Dashboard (Route: /)", h2_style))
    story.append(Paragraph(
        "<b>What this page does:</b> The Overview Dashboard is the <i>executive mission control</i> for your database. It translates thousands of complex internal database statistics into four high-level health cards, visual charts, and actionable alerts so you can understand your database status in 5 seconds.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Key Features & How they work:</b><br/>"
        "1. <b>Workload Health Radial Score:</b> A circular score gauge (0-100%). A score of 90%+ means your database is running smoothly with high buffer cache hits and minimal slow queries.<br/>"
        "2. <b>Bottleneck Distribution Donut Chart:</b> Replaces raw text with a clean color-coded pie chart showing the proportion of database issues (Sequential Scans in Red, Nested Loops in Amber, Hash Spills in Blue, Lock Waits in Purple).<br/>"
        "3. <b>Latency Spectrum Chart:</b> Plots average latency (Teal line) against 95th-percentile tail latency (Red line) over time, alerting you to sudden traffic spikes.<br/>"
        "4. <b>Top Priority Action Card:</b> Automatically surfaces the single worst query dragging down database performance, featuring a red warning accent and a direct <code>Review Bottleneck</code> button to jump straight to the fix.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # PAGE 2: LIVE WORKLOAD
    # -------------------------------------------------------------------------
    story.append(Paragraph("Page 2: Live Workload Monitor (Route: /workload)", h2_style))
    story.append(Paragraph(
        "<b>What this page does:</b> Shows what is happening inside the database <i>right now</i>. Instead of manually running terminal commands like <code>top</code> or querying system views, this page streams real-time execution statistics.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Key Features & How they work:</b><br/>"
        "1. <b>Throughput Gauge (QPS):</b> Shows total Queries Per Second currently being handled by the engine.<br/>"
        "2. <b>Live Execution Latency Bar & Line Chart:</b> Displays millisecond execution times across the active query stream.<br/>"
        "3. <b>Identified Problems Donut Chart:</b> Aggregates the root causes of recent slow queries into categorized percentages.<br/>"
        "4. <b>Live Query Telemetry Table:</b> A live-updating table listing query fingerprints, execution counts (<code>calls</code>), total time, and cache hit ratios. Clicking any row opens its detailed execution profile.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # PAGE 3: ANALYZE QUERY (CORE WORKSPACE)
    # -------------------------------------------------------------------------
    story.append(Paragraph("Page 3: Analyze Query Workspace (Route: /analyze)", h2_style))
    story.append(Paragraph(
        "<b>What this page does:</b> This is the heart and laboratory of QueryGuard AI. You paste any slow or problematic SQL query here, and the system scrubs its private data, visually diagnoses its bottlenecks, runs an in-memory virtual simulation, and lets you test an enhanced version immediately.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Step-by-Step Features & How they work:</b><br/>"
        "1. <b>SQL Editor & Sample Loader:</b> A clean light code editor. You can type your own query or click <code>Load Sample Slow Query</code> to test an un-indexed multi-table JOIN.<br/>"
        "2. <b>Privacy Sanitization Gateway:</b> The moment you submit a query, the SQLGlot AST engine replaces customer IDs, numbers, and strings with tokens. A green audit badge shows the 99.8% privacy guarantee.<br/>"
        "3. <b>Interactive Plan Graph:</b> Displays the visual execution tree. The root bottleneck is highlighted in <b>pale red</b>, secondary bottlenecks in <b>pale amber</b>, and optimized steps in <b>pale green</b>.<br/>"
        "4. <b>Enhanced Query & Virtual Execution:</b> When the AI suggests an index, you can click <code>Run Enhanced Query</code>. QueryGuard AI creates the index virtually in session RAM using HypoPG, re-runs the optimizer, and displays a verified cost drop of up to <b>93.3% with 0 disk writes</b>!<br/>"
        "5. <b>Explainability (Rule + GNN) Tab:</b> Shows the exact mathematical cost formula (<code>(N_pages * seq_cost) + (N_tuples * cpu_cost)</code>), the 2-layer GraphSAGE topological proof, an operator impact chart, and the exact GNN feature weights.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # PAGE 4: SLOW QUERIES
    # -------------------------------------------------------------------------
    story.append(Paragraph("Page 4: Slow Queries Catalog (Route: /slow-queries)", h2_style))
    story.append(Paragraph(
        "<b>What this page does:</b> Automatically tracks and ranks every query whose execution time exceeds the safety threshold (>= 100ms). It acts as an automated triage center for database slowdowns.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Key Features & How they work:</b><br/>"
        "1. <b>P95 & P99 Latency Ranking:</b> Instead of just sorting by average time, it highlights queries that cause random severe spikes for users.<br/>"
        "2. <b>Frequency vs. Duration Multiplier:</b> A query that takes 200ms but runs 1,000,000 times a day is far more damaging than a 5-second report that runs once a week. This table ranks queries by cumulative database impact.<br/>"
        "3. <b>One-Click Analysis:</b> Clicking the <code>Analyze</code> button next to any slow query instantly loads it into the Analyze Query workspace.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # PAGE 5: RECOMMENDATIONS
    # -------------------------------------------------------------------------
    story.append(Paragraph("Page 5: Recommendations & Approvals (Route: /recommendations)", h2_style))
    story.append(Paragraph(
        "<b>What this page does:</b> Where AI intelligence meets human-in-the-loop safety. QueryGuard AI never alters production database schemas automatically. Instead, it prepares clear, verified recommendations for DBA approval.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Key Features & How they work:</b><br/>"
        "1. <b>Recommendation Cards:</b> Displays candidate indexes (e.g., <code>CREATE INDEX idx_orders_customer_id ON orders(customer_id)</code>) with estimated cost reduction (e.g., -87.4%) and storage estimate.<br/>"
        "2. <b>DBA Approval Drawer:</b> Clicking <code>Review & Approve</code> opens a sliding drawer with full risk analysis, benefit score, and side-by-side plan comparison.<br/>"
        "3. <b>Automated Rollback DDL:</b> Every approved recommendation includes an automatically generated rollback command (e.g., <code>DROP INDEX CONCURRENTLY idx_...</code>) so changes can be reverted instantly if needed.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # PAGE 6: SIMULATIONS
    # -------------------------------------------------------------------------
    story.append(Paragraph("Page 6: What-If Simulations Showcase (Route: /simulations)", h2_style))
    story.append(Paragraph(
        "<b>What this page does:</b> A dedicated flight-simulator for database administrators. It allows DBAs to experiment with hypothetical indexes, composite keys, and table reorganizations without touching real disks.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Key Features & How they work:</b><br/>"
        "1. <b>Hypothetical Index Workbench:</b> Pick a table, pick one or more columns, and test index creation in RAM.<br/>"
        "2. <b>Side-by-Side Tree Comparison:</b> Shows the original execution plan on the left (Red Seq Scan) and the hypothetical plan on the right (Green Index Scan).<br/>"
        "3. <b>Resource & Storage Estimator:</b> Calculates how many megabytes of RAM and disk the index would consume if made permanent.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # PAGE 7: MODEL INSIGHTS
    # -------------------------------------------------------------------------
    story.append(Paragraph("Page 7: Model Insights & AI Explainability (Route: /model-insights)", h2_style))
    story.append(Paragraph(
        "<b>What this page does:</b> Provides total transparency into the AI models powering QueryGuard AI. It proves that the system is based on verified scientific machine learning, not black-box guesswork.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Key Features & How they work:</b><br/>"
        "1. <b>GNN Architecture Map:</b> Visualizes the 2-layer GraphSAGE neural network, showing how 16-dimensional node embeddings flow through 64-dimensional hidden representations.<br/>"
        "2. <b>50-Epoch Training Curve:</b> Plots the loss decay and accuracy convergence graph over 50 training epochs, reaching 94.6% validation accuracy.<br/>"
        "3. <b>Confusion Matrix Heatmap:</b> A color-coded grid proving the model's precision in classifying Sequential Scans, Hash Joins, Nested Loops, and Materialize operators without false positives.<br/>"
        "4. <b>Dataset Topology Donut:</b> Shows the 80/10/10 split across training, validation, and test workloads.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # PAGE 8: AUDIT TRAIL
    # -------------------------------------------------------------------------
    story.append(Paragraph("Page 8: Audit Trail & Compliance Ledger (Route: /audit)", h2_style))
    story.append(Paragraph(
        "<b>What this page does:</b> An immutable compliance record of every action taken in QueryGuard AI. It provides enterprise security teams with forensic evidence of database safety.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Key Features & How they work:</b><br/>"
        "1. <b>Cryptographic Event Ledger:</b> Every query analysis, simulation run, approval, and rejection is stamped with an immutable timestamp, user ID, and action hash.<br/>"
        "2. <b>Zero-Mutation Verification:</b> Proves cryptographically that during analysis, zero DDL or DML writes occurred against the live production tables.<br/>"
        "3. <b>Filterable Timeline:</b> Search events by actor, risk level, or approval status for SOC2 and ISO-27001 compliance reviews.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # PAGE 9: BENCHMARK DATASETS
    # -------------------------------------------------------------------------
    story.append(Paragraph("Page 9: Benchmark Datasets (Route: /benchmarks)", h2_style))
    story.append(Paragraph(
        "<b>What this page does:</b> Allows testing and benchmarking against industry-standard workloads so you can evaluate database tuning in a controlled laboratory environment.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Key Features & How they work:</b><br/>"
        "1. <b>Standard TPC-H Workload:</b> Includes industry-standard analytical queries (scale factor 0.1 and 1.0) with multi-table joins and complex aggregations.<br/>"
        "2. <b>Synthetic E-Commerce Workload:</b> Simulates high-velocity online shopping carts, orders, customer records, and inventory lookups.<br/>"
        "3. <b>One-Click Sandbox Seeding:</b> Easily reset or reload benchmark tables with a single click to run repeatable performance comparisons.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------------------
    # PAGE 10: SETTINGS & PRIVACY
    # -------------------------------------------------------------------------
    story.append(Paragraph("Page 10: Settings & Connection Management (Route: /settings)", h2_style))
    story.append(Paragraph(
        "<b>What this page does:</b> Controls the target database connections, privacy masking sensitivity, and telemetry collection frequencies.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Key Features & How they work:</b><br/>"
        "1. <b>Target Database Credentials:</b> Secure configuration of PostgreSQL connection URI with read-only permission enforcement.<br/>"
        "2. <b>Privacy Self-Test Tool:</b> Paste sample proprietary text to verify that names, credit cards, and table names are scrambled into HMAC tokens before connecting.<br/>"
        "3. <b>Telemetry Cadence Slider:</b> Set the frequency of <code>pg_stat_statements</code> polling (e.g., every 5s, 15s, or 60s) to balance freshness with low overhead.",
        body_style
    ))
    story.append(Spacer(1, 14))

    # =========================================================================
    # SUMMARY & CHEAT SHEET
    # =========================================================================
    story.append(Paragraph("Summary: 30-Second Quick Reference Cheat Sheet", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0F766E'), spaceBefore=2, spaceAfter=8))

    summary_data = [
        [Paragraph("If You Want To...", table_header), Paragraph("Go To This Page", table_header), Paragraph("Key Feature To Use", table_header)],
        [
            Paragraph("Check if database is healthy right now", table_body),
            Paragraph("<b>Overview (/)</b>", table_body),
            Paragraph("Workload Health Score + Bottleneck Donut", table_body)
        ],
        [
            Paragraph("See live incoming queries & traffic spikes", table_body),
            Paragraph("<b>Live Workload (/workload)</b>", table_body),
            Paragraph("Live QPS Gauge + Latency Line Chart", table_body)
        ],
        [
            Paragraph("Paste a slow query, test virtual index & run fix", table_body),
            Paragraph("<b>Analyze Query (/analyze)</b>", table_body),
            Paragraph("SQL Editor -> Run Enhanced Query (HypoPG)", table_body)
        ],
        [
            Paragraph("Understand the math and AI behind the diagnosis", table_body),
            Paragraph("<b>Analyze Query (/analyze)</b>", table_body),
            Paragraph("Explainability (Rule + GNN) Attribution Tab", table_body)
        ],
        [
            Paragraph("Find the worst queries running in the database", table_body),
            Paragraph("<b>Slow Queries (/slow-queries)</b>", table_body),
            Paragraph("P95/P99 Latency Filter & Impact Rank", table_body)
        ],
        [
            Paragraph("Approve or reject a suggested index safely", table_body),
            Paragraph("<b>Recommendations (/recommendations)</b>", table_body),
            Paragraph("DBA Approval Drawer with Rollback DDL", table_body)
        ],
        [
            Paragraph("Test what-if index ideas without writing to disk", table_body),
            Paragraph("<b>Simulations (/simulations)</b>", table_body),
            Paragraph("HypoPG In-Memory Plan Comparator", table_body)
        ],
        [
            Paragraph("Audit security, actions and zero-mutation proofs", table_body),
            Paragraph("<b>Audit Trail (/audit)</b>", table_body),
            Paragraph("Cryptographic Event Ledger & Export Log", table_body)
        ]
    ]
    summary_table = Table(summary_data, colWidths=[150, 150, 222])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    story.append(make_callout(
        "<b>QueryGuard AI Rule of Thumb:</b> No matter how complex a database issue appears, you can always diagnose it safely in three clicks: <b>(1)</b> Review on the Overview dashboard, <b>(2)</b> Analyze & Run Enhanced in the sandbox, and <b>(3)</b> Review the Rollback DDL in Recommendations before applying to production.",
        title="Key Takeaway for New Engineers",
        bg_color="#EFF6FF",
        border_color="#2563EB",
        text_color="#1E3A8A"
    ))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Handbook successfully built at: {output_path}")


if __name__ == "__main__":
    target = os.path.join(os.path.dirname(__file__), "..", "docs", "QueryGuard_AI_Complete_Handbook.pdf")
    target = os.path.abspath(target)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    build_handbook_pdf(target)
