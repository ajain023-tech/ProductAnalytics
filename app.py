"""Product Analytics & User Retention Dashboard."""

from pathlib import Path
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
AB_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "experiments" / "ab_test_summary.csv"
AB_RESULTS_PATH = PROJECT_ROOT / "data" / "ab_test_results.csv"
AB_ASSIGNMENTS_PATH = PROJECT_ROOT / "data" / "ab_test_dataset.csv"

# Source: documented project results in README.md.
# These are supplied BigQuery results, not values recalculated by this app.
DOCUMENTED_RESULTS = {
    "funnel": {
        "Signup": 34_000,
        "Onboarding": 18_341,
        "Trial": 5_499,
        "Paid": 3_281,
    },
    "retention_pct": {"D1": 41.01, "D7": 19.07, "D30": 14.73},
    "monetization": {
        "Gross Revenue": 145_262.81,
        "Refunds": 2_919.03,
        "Net Revenue": 142_343.78,
        "Revenue per Payer": 43.38,
        "Cancellation Rate": 6.71,
    },
}

PAGES = [
    "\U0001F4CA Executive Overview",
    "\U0001F50E User Funnel",
    "\U0001F465 User & Segment Analysis",
    "\U0001F4C8 Retention & Cohorts",
    "\U0001F9EA A/B Experiment",
    "\U0001F916 ML Retention Prediction",
    "\U0001F5C3\uFE0F SQL Analysis",
    "\U0001F4B0 Documented Monetization",
    "\U0001F4CB Data & Methodology",
    "\U0001F504 Project Workflow",
]

COLORS = {
    "ink": "#111827",
    "blue": "#2563EB",
    "teal": "#16A34A",
    "gold": "#D97706",
    "coral": "#DC2626",
    "muted": "#6B7280",
    "grid": "#E5E7EB",
    "pale_blue": "#EFF6FF",
    "pale_teal": "#ECFDF5",
}

CORE_OUTCOMES = {
    "onboarding_completed": ("Onboarding Completion", None),
    "trial_started": ("Trial Start", "trial_eligible"),
    "paid_conversion": ("Paid Conversion", "paid_eligible"),
}
RETENTION_OUTCOMES = {
    "d1_retained": ("D1 Retention", "d1_eligible"),
    "d7_retained": ("D7 Retention", "d7_eligible"),
    "d30_retained": ("D30 Retention", "d30_eligible"),
}

st.set_page_config(
    page_title="Product Analytics & User Retention",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

pio.templates.default = "plotly_white"
pio.templates["plotly_white"].layout.font.color = "#374151"
pio.templates["plotly_white"].layout.font.size = 14
pio.templates["plotly_white"].layout.paper_bgcolor = "#FFFFFF"
pio.templates["plotly_white"].layout.plot_bgcolor = "#FFFFFF"

st.markdown(
    """
    <style>
    :root {color-scheme: light;}
    html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
      background:#F5F7FB !important; color:#111827 !important;
    }
    [data-testid="stHeader"] {background:rgba(245,247,251,.96) !important;}
    .block-container {max-width:1440px;padding:1.2rem clamp(1rem,2.2vw,2rem) 2.5rem;}
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
      background:#FFFFFF !important;border-right:1px solid #E5E7EB;
    }
    [data-testid="stSidebar"] * {color:#374151;}
    .sidebar-brand {font-size:1.1rem;line-height:1.3;font-weight:750;color:#111827 !important;}
    .sidebar-caption {font-size:.9rem;color:#4B5563 !important;margin:.35rem 0 .15rem;}
    .sidebar-caption:last-of-type {font-size:.82rem;color:#6B7280 !important;margin-bottom:1.1rem;}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
      color:#374151 !important;font-size:.92rem;line-height:1.35;border-radius:8px;padding:.28rem .35rem;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
      background:#DBEAFE !important;color:#1D4ED8 !important;font-weight:700;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) * {color:#1D4ED8 !important;}
    .eyebrow {font-size:.78rem;letter-spacing:.12em;font-weight:750;color:#166534;}
    .page-title {font-size:30px;line-height:1.18;font-weight:760;color:#111827 !important;
      letter-spacing:-.025em;margin:.2rem 0 .4rem;}
    .page-subtitle {font-size:15px;line-height:1.5;color:#4B5563 !important;margin:0 0 .8rem;}
    .provenance {font-size:13px;color:#4B5563 !important;margin:.15rem 0 .85rem;}
    .kpi-card {background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;padding:14px 16px;
      min-height:104px;box-shadow:0 2px 7px rgba(17,24,39,.06);}
    .kpi-label {font-size:14px;color:#4B5563;font-weight:600;}
    .kpi-value {font-size:30px;line-height:1.3;font-weight:750;color:#111827;
      letter-spacing:-.025em;margin:.23rem 0;}
    .kpi-detail {font-size:13px;color:#4B5563;}
    .insight-card {height:100%;min-height:88px;padding:14px 16px;background:#FFFFFF;
      border:1px solid #E5E7EB;border-left:3px solid #16A34A;border-radius:9px;
      color:#374151;font-size:14px;}
    .insight-title {font-weight:700;color:#111827;margin-bottom:5px;}
    .section-caption {font-size:14px;color:#4B5563;margin-top:-.5rem;}
    h1,h2,h3,h4 {color:#111827 !important;letter-spacing:-.02em;}
    h2 {font-size:24px !important;} h3 {font-size:21px !important;} h4 {font-size:18px !important;}
    p,li,[data-testid="stMarkdownContainer"] {color:#374151;}
    [data-testid="stCaptionContainer"] {color:#4B5563 !important;font-size:13px;}
    [data-testid="stMetric"] {background:#FFFFFF !important;border:1px solid #E5E7EB !important;
      border-radius:10px;padding:13px 15px;min-height:98px;box-shadow:0 2px 7px rgba(17,24,39,.05);}
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {color:#4B5563 !important;font-size:14px !important;}
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {color:#111827 !important;font-size:30px !important;font-weight:750 !important;}
    [data-testid="stMetricDelta"] {font-size:13px !important;}
    [data-testid="stDataFrame"], [data-testid="stTable"] {background:#FFFFFF;border:1px solid #E5E7EB;border-radius:8px;}
    [data-testid="stDataFrame"] [role="columnheader"] {background:#EFF6FF !important;color:#111827 !important;font-weight:700 !important;}
    [data-testid="stDataFrame"] [role="gridcell"] {color:#1F2937 !important;}
    [data-testid="stTable"] th {background:#EFF6FF !important;color:#111827 !important;font-weight:700 !important;}
    [data-testid="stTable"] td {color:#1F2937 !important;}
    [data-testid="stAlert"] {border-radius:9px;}
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {margin-bottom:.55rem;}
    [data-testid="stPlotlyChart"] {background:#FFFFFF;border:1px solid #E5E7EB;border-radius:9px;padding:5px;}
    hr {border-color:#E5E7EB !important;}
    @media (max-width: 1180px) {
      [data-testid="stHorizontalBlock"]:has([data-testid="stPlotlyChart"]) {
        flex-direction:column !important;
      }
      [data-testid="stHorizontalBlock"]:has([data-testid="stPlotlyChart"]) > div {
        width:100% !important;
        min-width:100% !important;
        flex:1 1 100% !important;
      }
      [data-testid="stHorizontalBlock"]:has(.kpi-card):not(:has([data-testid="stPlotlyChart"])) {
        display:grid !important;
        grid-template-columns:repeat(2,minmax(0,1fr)) !important;
        gap:.8rem !important;
      }
      [data-testid="stHorizontalBlock"]:has(.kpi-card):not(:has([data-testid="stPlotlyChart"])) > div {
        width:100% !important;
        min-width:0 !important;
        flex:initial !important;
      }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_local_csv(path_string: str) -> pd.DataFrame | None:
    """Load a project-relative CSV, returning None for missing/empty templates."""
    path = Path(path_string)
    if not path.is_file():
        return None
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
        return None
    return None if frame.empty else frame


def get_ab_data() -> tuple[pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None]:
    summary = load_local_csv(str(AB_SUMMARY_PATH))
    raw_results = load_local_csv(str(AB_RESULTS_PATH))
    assignments = load_local_csv(str(AB_ASSIGNMENTS_PATH))
    return summary, raw_results, assignments


def _binary_column(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce").where(
        pd.to_numeric(frame[column], errors="coerce").isin([0, 1])
    )


def _outcome_counts(
    frame: pd.DataFrame,
    outcome: str,
    eligibility: str | None = None,
) -> tuple[int, int, float | None]:
    values = _binary_column(frame, outcome)
    eligible = (
        _binary_column(frame, eligibility).eq(1)
        if eligibility and eligibility in frame.columns
        else pd.Series(True, index=frame.index)
    )
    valid = values.notna() & eligible
    denominator = int(valid.sum())
    successes = int(values[valid].sum()) if denominator else 0
    rate = 100 * successes / denominator if denominator else None
    return successes, denominator, rate


def _meaningful_categorical_dimensions(frame: pd.DataFrame) -> list[str]:
    dimensions: list[str] = []
    excluded = {"user_id", "assigned_at", "signup_ts", "data_end_date"}
    for column in frame.columns:
        is_temporal_name = any(
            token in column.lower() for token in ["date", "time", "timestamp"]
        )
        if column in excluded or is_temporal_name or not (
            pd.api.types.is_object_dtype(frame[column].dtype)
            or pd.api.types.is_string_dtype(frame[column].dtype)
            or isinstance(frame[column].dtype, pd.CategoricalDtype)
        ):
            continue
        values = frame[column].dropna()
        categories = values.nunique()
        if not 2 <= categories <= 20:
            continue
        dimensions.append(column)
    return dimensions


def analyze_user_dataset(
    dataset: pd.DataFrame | None,
) -> dict[str, object] | None:
    if dataset is None or dataset.empty:
        return None

    data = dataset.copy()
    missing_values = int(data.isna().sum().sum())
    duplicate_rows = int(data.duplicated().sum())
    has_user_id = "user_id" in data.columns
    unique_users = int(data["user_id"].nunique()) if has_user_id else None
    duplicate_users = (
        int(data["user_id"].duplicated(keep="first").sum())
        if has_user_id
        else None
    )

    if "variant" in data.columns:
        normalized_variant = data["variant"].astype("string").str.strip().str.lower()
    else:
        normalized_variant = pd.Series("", index=data.index, dtype="string")
    valid_variants = normalized_variant.isin(["control", "treatment"])
    invalid_variants = int((~valid_variants).sum())

    if has_user_id:
        unique_identity_rows = data["user_id"].notna() & ~data["user_id"].duplicated(
            keep=False
        )
    else:
        unique_identity_rows = pd.Series(False, index=data.index)
    analytical = data.loc[valid_variants & unique_identity_rows].copy()
    analytical["variant"] = normalized_variant.loc[analytical.index].str.title()

    outcomes = {
        **{column: definition for column, definition in CORE_OUTCOMES.items() if column in data.columns},
        **{column: definition for column, definition in RETENTION_OUTCOMES.items() if column in data.columns},
    }
    required_core_outcomes_available = all(
        column in data.columns for column in CORE_OUTCOMES
    )
    valid_outcome_fields = [
        _binary_column(data, column).notna() for column in CORE_OUTCOMES if column in data.columns
    ]
    complete_outcome_records = (
        int(pd.concat(valid_outcome_fields, axis=1).all(axis=1).sum())
        if required_core_outcomes_available
        else 0
    )
    complete_outcome_pct = (
        100 * complete_outcome_records / len(data) if len(data) else 0.0
    )

    group_users = {}
    for group in ["Control", "Treatment"]:
        members = analytical.loc[analytical["variant"] == group]
        group_users[group] = (
            int(members["user_id"].nunique()) if has_user_id else 0
        )
    outcome_rows: list[dict[str, object]] = []
    for column, (label, eligibility) in outcomes.items():
        group_values = {}
        for group in ["Control", "Treatment"]:
            subset = analytical.loc[analytical["variant"] == group]
            successes, denominator, rate = _outcome_counts(
                subset, column, eligibility
            )
            group_values[group] = {
                "successes": successes,
                "denominator": denominator,
                "rate": rate,
            }
        control_rate = group_values["Control"]["rate"]
        treatment_rate = group_values["Treatment"]["rate"]
        outcome_rows.append(
            {
                "column": column,
                "metric": label,
                "eligibility": eligibility,
                "control": group_values["Control"],
                "treatment": group_values["Treatment"],
                "difference_pp": (
                    treatment_rate - control_rate
                    if control_rate is not None and treatment_rate is not None
                    else None
                ),
            }
        )

    overall_outcomes = []
    for column, (label, eligibility) in CORE_OUTCOMES.items():
        if column not in analytical.columns:
            continue
        successes, denominator, rate = _outcome_counts(
            analytical, column, eligibility
        )
        overall_outcomes.append(
            {
                "column": column,
                "metric": label,
                "successes": successes,
                "denominator": denominator,
                "rate": rate,
            }
        )

    dimensions = _meaningful_categorical_dimensions(data)
    status_complete = (
        missing_values == 0
        and duplicate_rows == 0
        and (duplicate_users == 0 if duplicate_users is not None else False)
        and invalid_variants == 0
        and required_core_outcomes_available
        and complete_outcome_pct == 100
    )
    return {
        "data": data,
        "analytical": analytical,
        "records": len(data),
        "unique_users": unique_users,
        "missing_values": missing_values,
        "duplicate_rows": duplicate_rows,
        "duplicate_users": duplicate_users,
        "invalid_variants": invalid_variants,
        "group_users": group_users,
        "outcomes": outcome_rows,
        "core_outcomes": overall_outcomes,
        "dimensions": dimensions,
        "complete_outcome_records": complete_outcome_records,
        "complete_outcome_pct": complete_outcome_pct,
        "required_core_outcomes_available": required_core_outcomes_available,
        "status_complete": status_complete,
    }


def two_proportion_test(
    control_successes: int,
    control_total: int,
    treatment_successes: int,
    treatment_total: int,
) -> tuple[float | None, float | None]:
    if control_total <= 0 or treatment_total <= 0:
        return None, None
    control_rate = control_successes / control_total
    treatment_rate = treatment_successes / treatment_total
    pooled_rate = (control_successes + treatment_successes) / (
        control_total + treatment_total
    )
    standard_error = math.sqrt(
        pooled_rate
        * (1 - pooled_rate)
        * (1 / control_total + 1 / treatment_total)
    )
    if standard_error == 0:
        return 0.0, 1.0 if control_rate == treatment_rate else 0.0
    z_score = (treatment_rate - control_rate) / standard_error
    p_value = math.erfc(abs(z_score) / math.sqrt(2))
    return z_score, p_value


def build_user_segment_metrics(
    frame: pd.DataFrame,
    dimension: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for category in frame[dimension].dropna().drop_duplicates().tolist():
        subset = frame.loc[frame[dimension] == category]
        users = (
            int(subset["user_id"].nunique())
            if "user_id" in subset.columns
            else int(len(subset))
        )
        row: dict[str, object] = {
            "Category": str(category),
            "User Count": users,
        }
        for column, (label, eligibility) in CORE_OUTCOMES.items():
            if column not in subset.columns:
                continue
            _, _, rate = _outcome_counts(subset, column, eligibility)
            row[f"{label} Rate"] = rate
        rows.append(row)
    return pd.DataFrame(rows)


def calculate_funnel_metrics(funnel: dict[str, int]) -> pd.DataFrame:
    """Derive stage conversions and losses from the documented stage counts."""
    rows = []
    previous_count = None
    for stage, users in funnel.items():
        rows.append(
            {
                "stage": stage,
                "users": users,
                "conversion_pct": 100.0 if previous_count is None else 100 * users / previous_count,
                "dropoff_users": 0 if previous_count is None else previous_count - users,
                "dropoff_pct": 0.0 if previous_count is None else 100 * (previous_count - users) / previous_count,
            }
        )
        previous_count = users
    return pd.DataFrame(rows)


def build_overview_insights(
    funnel_metrics: pd.DataFrame,
    retention: dict[str, float],
    primary: pd.Series | None,
    guardrail: pd.Series | None,
) -> list[tuple[str, str]]:
    largest_loss = funnel_metrics.iloc[1:].sort_values("dropoff_users").iloc[-1]
    bottleneck = funnel_metrics.iloc[1:].sort_values("dropoff_pct").iloc[-1]
    days = list(retention)
    retention_losses = [
        (days[index - 1], days[index], retention[days[index - 1]] - retention[days[index]])
        for index in range(1, len(days))
    ]
    retention_drop = max(retention_losses, key=lambda item: item[2])
    insights = [
        (
            "Largest user loss",
            f"{largest_loss['stage']} loses {largest_loss['dropoff_users']:,.0f} users "
            "from the preceding stage.",
        ),
        (
            "Largest stage bottleneck",
            f"{bottleneck['stage']} has the highest stage drop-off "
            f"({bottleneck['dropoff_pct']:.2f}%).",
        ),
        (
            "Retention",
            f"The largest measured decline is {retention_drop[0]} to {retention_drop[1]} "
            f"({retention_drop[2]:.2f} percentage points).",
        ),
    ]
    if primary is not None and guardrail is not None:
        primary_sig = bool(primary["statistically_significant"])
        guardrail_sig = bool(guardrail["statistically_significant"])
        primary_note = "statistically significant" if primary_sig else "not statistically significant"
        guardrail_note = "statistically significant" if guardrail_sig else "not statistically significant"
        guardrail_uplift = float(guardrail["absolute_uplift"])
        direction = "increased" if guardrail_uplift >= 0 else "decreased"
        insights.append(
            (
                "Experiment guardrail",
                f"Onboarding improvement was {primary_note}; paid conversion "
                f"{direction} {abs(guardrail_uplift):.2f} pp and was {guardrail_note}.",
            )
        )
    return insights


def source_label(text: str) -> None:
    st.markdown(f'<div class="provenance">{text}</div>', unsafe_allow_html=True)


def render_kpi(label: str, value: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-detail">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="insight-card">
          <div class="insight-title">{title}</div>
          <div>{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_compact_count(value: int) -> str:
    return f"{value / 1000:.1f}K" if value >= 1000 else f"{value:,}"


def make_funnel_chart(metrics: pd.DataFrame) -> go.Figure:
    chart = go.Figure()
    chart.add_trace(
        go.Funnel(
            y=metrics["stage"],
            x=metrics["users"],
            text=[
                f"{row.users:,.0f} users · {row.conversion_pct:.2f}%"
                for row in metrics.itertuples()
            ],
            textposition="inside",
            textfont={"color": "white", "size": 13},
            customdata=metrics[["conversion_pct", "dropoff_users", "dropoff_pct"]],
            marker={
                "color": [COLORS["blue"], COLORS["teal"], COLORS["gold"], COLORS["ink"]],
                "line": {"width": 0},
            },
            hovertemplate=(
                "<b>%{y}</b><br>Users: %{x:,}"
                "<br>Conversion from previous stage: %{customdata[0]:.2f}%"
                "<br>Users lost from previous stage: %{customdata[1]:,}"
                "<br>Drop-off rate: %{customdata[2]:.2f}%<extra></extra>"
            ),
            connector={"line": {"color": COLORS["grid"], "width": 1}},
        )
    )
    chart.update_layout(
        height=355,
        margin={"l": 8, "r": 8, "t": 8, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        xaxis={"visible": False},
        yaxis={"tickfont": {"size": 12}},
    )
    return chart


def make_retention_chart(retention: dict[str, float]) -> go.Figure:
    frame = pd.DataFrame(
        {"Day": list(retention), "Retention (%)": list(retention.values())}
    )
    chart = px.line(
        frame,
        x="Day",
        y="Retention (%)",
        markers=True,
        text="Retention (%)",
        category_orders={"Day": ["D1", "D7", "D30"]},
        color_discrete_sequence=[COLORS["teal"]],
    )
    chart.update_traces(
        line={"width": 3},
        marker={"size": 10, "line": {"width": 2, "color": "white"}},
        texttemplate="%{y:.2f}%",
        textposition="top center",
        hovertemplate="%{x} retention: %{y:.2f}%<extra></extra>",
    )
    chart.update_layout(
        height=290,
        margin={"l": 10, "r": 10, "t": 20, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        xaxis={"title": "", "showgrid": False},
        yaxis={
            "title": "Retention",
            "ticksuffix": "%",
            "range": [0, max(retention.values()) * 1.35],
            "gridcolor": COLORS["grid"],
            "zeroline": False,
        },
    )
    return chart


def make_revenue_chart(revenue: dict[str, float]) -> go.Figure:
    chart = go.Figure(
        go.Waterfall(
            measure=["absolute", "relative", "total"],
            x=["Gross Revenue", "Refunds", "Net Revenue"],
            y=[revenue["Gross Revenue"], -revenue["Refunds"], 0],
            text=[
                f"${revenue['Gross Revenue']:,.2f}",
                f"−${revenue['Refunds']:,.2f}",
                f"${revenue['Net Revenue']:,.2f}",
            ],
            textposition="outside",
            increasing={"marker": {"color": COLORS["blue"]}},
            decreasing={"marker": {"color": COLORS["coral"]}},
            totals={"marker": {"color": COLORS["teal"]}},
            connector={"line": {"color": "#BCC8D2"}},
            hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>",
        )
    )
    chart.update_layout(
        height=285,
        showlegend=False,
        margin={"l": 5, "r": 5, "t": 25, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        yaxis={"title": "USD", "gridcolor": COLORS["grid"], "zeroline": False},
        xaxis={"title": ""},
    )
    return chart


def make_ab_chart(primary: pd.Series) -> go.Figure:
    frame = pd.DataFrame(
        {
            "Group": ["Control", "Treatment"],
            "Completion rate (%)": [
                float(primary["control_conversion_rate"]),
                float(primary["treatment_conversion_rate"]),
            ],
        }
    )
    chart = px.bar(
        frame,
        x="Group",
        y="Completion rate (%)",
        color="Group",
        text="Completion rate (%)",
        color_discrete_map={"Control": COLORS["blue"], "Treatment": COLORS["teal"]},
    )
    chart.update_traces(
        texttemplate="%{y:.2f}%",
        textposition="outside",
        hovertemplate="%{x}<br>Onboarding completion: %{y:.2f}%<extra></extra>",
    )
    chart.update_layout(
        height=275,
        showlegend=False,
        margin={"l": 5, "r": 5, "t": 12, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        yaxis={
            "title": "Completion rate",
            "ticksuffix": "%",
            "range": [0, 70],
            "gridcolor": COLORS["grid"],
        },
        xaxis={"title": ""},
    )
    return chart


def calculate_variant_funnel(assignments: pd.DataFrame) -> pd.DataFrame | None:
    required = {
        "user_id",
        "variant",
        "onboarding_completed",
        "trial_started",
        "paid_conversion",
    }
    if not required <= set(assignments.columns):
        return None
    rows = assignments[["user_id", "variant", "onboarding_completed", "trial_started", "paid_conversion"]].copy()
    rows = rows.dropna(subset=["user_id", "variant"])
    if rows["user_id"].duplicated().any():
        return None
    rows["variant"] = rows["variant"].astype(str).str.strip().str.title()
    rows = rows[rows["variant"].isin(["Control", "Treatment"])]
    if rows.empty:
        return None
    grouped = rows.groupby("variant", sort=False).agg(
        users=("user_id", "nunique"),
        onboarding_users=("onboarding_completed", "sum"),
        trial_users=("trial_started", "sum"),
        paid_users=("paid_conversion", "sum"),
    )
    metrics = grouped.reset_index()
    for metric_column in ["onboarding_users", "trial_users", "paid_users"]:
        metrics[f"{metric_column}_pct"] = 100 * metrics[metric_column] / metrics["users"]
    return metrics.rename(
        columns={
            "onboarding_users_pct": "onboarding_rate_pct",
            "trial_users_pct": "trial_rate_pct",
            "paid_users_pct": "paid_rate_pct",
        }
    )


def make_stage_conversion_chart(metrics: pd.DataFrame) -> go.Figure:
    stages = metrics.iloc[1:].copy()
    chart = px.bar(
        stages,
        x="stage",
        y="conversion_pct",
        text="conversion_pct",
        color="stage",
        color_discrete_sequence=[COLORS["blue"], COLORS["gold"], COLORS["teal"]],
        custom_data=["dropoff_pct"],
    )
    chart.update_traces(
        texttemplate="%{y:.2f}%",
        textposition="outside",
        hovertemplate=(
            "%{x}<br>Conversion from previous stage: %{y:.2f}%"
            "<br>Drop-off: %{customdata[0]:.2f}%<extra></extra>"
        ),
    )
    chart.update_layout(
        height=330,
        showlegend=False,
        margin={"l": 8, "r": 8, "t": 25, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        xaxis={"title": "", "tickangle": 0},
        yaxis={"title": "Conversion rate", "ticksuffix": "%", "range": [0, 75], "gridcolor": COLORS["grid"]},
    )
    return chart


def make_dropoff_chart(metrics: pd.DataFrame) -> go.Figure:
    stages = metrics.iloc[1:].copy()
    stages["transition"] = [
        f"{metrics.iloc[index - 1]['stage']} → {row.stage}"
        for index, row in enumerate(stages.itertuples(), start=1)
    ]
    chart = px.bar(
        stages,
        x="dropoff_users",
        y="transition",
        orientation="h",
        text="dropoff_users",
        color="dropoff_users",
        color_continuous_scale=[COLORS["pale_blue"], COLORS["blue"]],
        custom_data=["dropoff_pct"],
    )
    chart.update_traces(
        texttemplate="%{x:,.0f}",
        textposition="outside",
        hovertemplate=(
            "%{y}<br>Users lost: %{x:,}"
            "<br>Drop-off rate: %{customdata[0]:.2f}%<extra></extra>"
        ),
    )
    chart.update_layout(
        height=330,
        showlegend=False,
        coloraxis_showscale=False,
        margin={"l": 8, "r": 55, "t": 18, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        xaxis={"title": "Users lost", "gridcolor": COLORS["grid"], "rangemode": "tozero"},
        yaxis={"title": ""},
    )
    return chart


def make_variant_comparison_chart(segments: pd.DataFrame) -> go.Figure:
    chart_data = segments.melt(
        id_vars=["variant"],
        value_vars=["onboarding_rate_pct", "trial_rate_pct", "paid_rate_pct"],
        var_name="Stage",
        value_name="Users (%)",
    )
    stage_labels = {
        "onboarding_rate_pct": "Onboarding",
        "trial_rate_pct": "Trial",
        "paid_rate_pct": "Paid",
    }
    chart_data["Stage"] = chart_data["Stage"].map(stage_labels)
    chart = px.bar(
        chart_data,
        x="Stage",
        y="Users (%)",
        color="variant",
        barmode="group",
        text="Users (%)",
        color_discrete_map={"Control": COLORS["blue"], "Treatment": COLORS["teal"]},
        category_orders={"variant": ["Control", "Treatment"], "Stage": ["Onboarding", "Trial", "Paid"]},
    )
    chart.update_traces(
        texttemplate="%{y:.2f}%",
        textposition="outside",
        hovertemplate="%{x}<br>%{fullData.name}: %{y:.2f}% of assigned users<extra></extra>",
    )
    chart.update_layout(
        height=340,
        margin={"l": 8, "r": 8, "t": 20, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        xaxis={"title": ""},
        yaxis={"title": "Share of assigned users", "ticksuffix": "%", "gridcolor": COLORS["grid"], "rangemode": "tozero"},
        legend={"title": ""},
    )
    return chart


def build_funnel_insights(metrics: pd.DataFrame, segments: pd.DataFrame | None) -> list[tuple[str, str]]:
    transitions = metrics.iloc[1:].copy()
    largest_drop = transitions.loc[transitions["dropoff_users"].idxmax()]
    strongest = transitions.loc[transitions["conversion_pct"].idxmax()]
    weakest = transitions.loc[transitions["conversion_pct"].idxmin()]
    paid = int(metrics.iloc[-1]["users"])
    signups = int(metrics.iloc[0]["users"])
    previous_stage = metrics.iloc[metrics.index.get_loc(largest_drop.name) - 1]["stage"]
    insights = [
        (
            "Largest absolute drop-off",
            f"{previous_stage} → "
            f"{largest_drop['stage']} accounts for {largest_drop['dropoff_users']:,.0f} lost users "
            f"({largest_drop['dropoff_pct']:.2f}%).",
        ),
        (
            "Strongest stage conversion",
            f"{strongest['stage']} has the highest conversion from the previous stage "
            f"at {strongest['conversion_pct']:.2f}%.",
        ),
        (
            "Weakest stage conversion",
            f"{weakest['stage']} has the lowest conversion from the previous stage "
            f"at {weakest['conversion_pct']:.2f}%.",
        ),
        (
            "Funnel efficiency",
            f"{paid:,} of {signups:,} signups reached paid subscription "
            f"({100 * paid / signups:.2f}%).",
        ),
    ]
    if segments is not None and not segments.empty:
        best = segments.loc[segments["paid_rate_pct"].idxmax()]
        worst = segments.loc[segments["paid_rate_pct"].idxmin()]
        insights[-1] = (
            "Funnel efficiency & experiment context",
            f"{100 * paid / signups:.2f}% of signups reached paid overall. In the separate "
            f"experiment sample, paid conversion was {best['paid_rate_pct']:.2f}% for "
            f"{best['variant']} and {worst['paid_rate_pct']:.2f}% for {worst['variant']}.",
        )
    return insights


def show_funnel_page() -> None:
    funnel = DOCUMENTED_RESULTS["funnel"]
    metrics = calculate_funnel_metrics(funnel)
    signup_users = int(metrics.iloc[0]["users"])
    paid_users = int(metrics.iloc[-1]["users"])
    overall_conversion = 100 * paid_users / signup_users
    _, _, assignments = get_ab_data()
    variant_metrics = calculate_variant_funnel(assignments) if assignments is not None else None

    st.markdown('<div class="eyebrow">PRODUCT JOURNEY ANALYSIS</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">User Funnel</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">How do users move from signup to paid subscription, '
        'and where is the greatest opportunity to improve progression?</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Funnel overview")
    st.caption("An ordered funnel counts users at each step of the product journey.")
    overview_col, efficiency_col = st.columns([1.55, 0.65], gap="large")
    with overview_col:
        st.plotly_chart(
            make_funnel_chart(metrics),
            width="stretch",
            config={"displayModeBar": False},
        )
    with efficiency_col:
        render_kpi(
            "Overall Funnel Efficiency",
            f"{overall_conversion:.2f}%",
            "Overall Signup → Paid conversion",
        )
        st.markdown("")
        render_kpi(
            "Paid users per 100 signups",
            f"{overall_conversion:.2f}",
            f"Approximately {overall_conversion:.2f} of every 100 reach paid",
        )
        st.markdown(
            '<div class="insight-card">Funnel efficiency is the share of all signups '
            'that eventually reach the paid stage. It summarizes end-to-end journey '
            'performance in one number.</div>',
            unsafe_allow_html=True,
        )

    stage_cards = st.columns(4, gap="medium")
    for index, row in enumerate(metrics.itertuples()):
        with stage_cards[index]:
            detail = (
                "Starting population"
                if index == 0
                else f"{row.conversion_pct:.2f}% from prior stage · "
                f"{row.dropoff_users:,} lost ({row.dropoff_pct:.2f}%)"
            )
            render_kpi(row.stage, f"{row.users:,}", detail)

    st.markdown("")
    performance_col, dropoff_col = st.columns(2, gap="large")
    with performance_col:
        st.markdown("### Funnel stage performance")
        st.caption("Conversion from the immediately preceding stage")
        st.plotly_chart(
            make_stage_conversion_chart(metrics),
            width="stretch",
            config={"displayModeBar": False},
        )
    with dropoff_col:
        st.markdown("### Users Lost at Each Stage")
        st.caption("Absolute user loss and its share of the preceding stage")
        st.plotly_chart(
            make_dropoff_chart(metrics),
            width="stretch",
            config={"displayModeBar": False},
        )
    largest_drop = metrics.iloc[1:].loc[metrics.iloc[1:]["dropoff_users"].idxmax()]
    previous_stage = metrics.iloc[metrics.index.get_loc(largest_drop.name) - 1]["stage"]
    st.markdown(
        f'<div class="insight-card"><div class="insight-title">Largest absolute drop-off</div>'
        f'{previous_stage} → {largest_drop["stage"]} loses '
        f'{largest_drop["dropoff_users"]:,.0f} users '
        f'({largest_drop["dropoff_pct"]:.2f}% of the preceding stage).</div>',
        unsafe_allow_html=True,
    )

    st.markdown("")
    st.markdown("### How does the funnel differ across user segments?")
    st.caption(
        "Compare stage outcomes across the available user groups. "
        "For experiment variants, rates use the full assigned group as the denominator."
    )
    available_dimensions = [
        "Acquisition Channel",
        "Platform",
        "Device Tier",
        "Region",
        "Experiment Variant (local data)",
    ]
    selected_dimension = st.selectbox(
        "Compare by",
        available_dimensions,
        index=4,
        key="funnel_segment_dimension",
    )
    if selected_dimension == "Experiment Variant (local data)" and variant_metrics is not None:
        st.markdown("#### Experiment assignment groups")
        st.caption(
            "This is a real local comparison for the A/B test population, not a "
            "whole-product acquisition, platform, device, or region breakdown."
        )
        st.plotly_chart(
            make_variant_comparison_chart(variant_metrics),
            width="stretch",
            config={"displayModeBar": False},
        )
        table = variant_metrics.rename(
            columns={
                "variant": "Segment",
                "users": "Users",
                "onboarding_rate_pct": "Onboarding Rate",
                "trial_rate_pct": "Trial Rate",
                "paid_rate_pct": "Paid Rate",
            }
        )[["Segment", "Users", "Onboarding Rate", "Trial Rate", "Paid Rate"]]
        table["Users"] = table["Users"].map(lambda value: f"{value:,}")
        for column in ["Onboarding Rate", "Trial Rate", "Paid Rate"]:
            table[column] = table[column].map(lambda value: f"{value:.2f}%")
        st.dataframe(table, hide_index=True, width="stretch")
    else:
        st.caption(
            "No populated breakdown is available for this selection. "
            "Choose Experiment Variant to view the available comparison."
        )

    st.markdown("")
    st.markdown("### Customer journey insights")
    insights = build_funnel_insights(metrics, variant_metrics)
    for start in range(0, len(insights), 2):
        cards = st.columns(2, gap="medium")
        for column, (title, body) in zip(cards, insights[start : start + 2]):
            with column:
                render_insight(title, body)

    with st.expander("How to explain these metrics"):
        st.markdown(
            """
            - **Funnel:** an ordered view of how users progress through key product steps.
            - **Conversion:** users who reach a step divided by users at the prior step.
            - **Drop-off:** users who were at one step but did not reach the next step.
            - **Funnel efficiency:** paid users divided by signups; it summarizes end-to-end progression.
            - **Segment comparison:** helps identify where outcomes differ across user groups and where the team may investigate product experience or acquisition quality.
            """
        )


def make_experiment_distribution_chart(profile: dict[str, object]) -> go.Figure:
    group_users = profile["group_users"]
    labels = ["Control", "Treatment"]
    values = [int(group_users[label]) for label in labels]
    chart = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            sort=False,
            marker={"colors": [COLORS["blue"], COLORS["teal"]]},
            texttemplate="%{label}<br>%{value:,} users<br>%{percent}",
            textposition="inside",
            customdata=values,
            hovertemplate="%{label}<br>%{value:,} users (%{percent})<extra></extra>",
        )
    )
    chart.update_layout(
        height=330,
        margin={"l": 8, "r": 8, "t": 8, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        showlegend=True,
        legend={"orientation": "h", "y": -0.03},
        annotations=[
            {
                "text": f"{sum(values):,}<br><sup>assigned users</sup>",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 16, "color": COLORS["ink"]},
            }
        ],
    )
    return chart


def make_user_outcome_chart(profile: dict[str, object]) -> go.Figure:
    frame = pd.DataFrame(profile["core_outcomes"])
    frame = frame.loc[frame["rate"].notna()].copy()
    frame["label"] = [
        f"{row.metric}<br>{row.successes:,} / {row.denominator:,}"
        for row in frame.itertuples()
    ]
    chart = px.bar(
        frame,
        x="metric",
        y="rate",
        text="rate",
        color="metric",
        color_discrete_sequence=[COLORS["blue"], COLORS["gold"], COLORS["teal"]],
        custom_data=["successes", "denominator"],
    )
    chart.update_traces(
        texttemplate="%{y:.2f}%",
        textposition="outside",
        hovertemplate=(
            "%{x}<br>Reached outcome: %{customdata[0]:,} / %{customdata[1]:,}"
            "<br>Rate: %{y:.2f}%<extra></extra>"
        ),
    )
    chart.update_layout(
        height=330,
        showlegend=False,
        margin={"l": 8, "r": 8, "t": 22, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        xaxis={"title": ""},
        yaxis={"title": "Share reaching outcome", "ticksuffix": "%", "rangemode": "tozero", "gridcolor": COLORS["grid"]},
    )
    return chart


def make_user_journey_chart(profile: dict[str, object]) -> go.Figure:
    rows: list[dict[str, object]] = []
    all_stages = [
        ("Onboarding Completed", "onboarding_completed"),
        ("Trial Started", "trial_started"),
        ("Paid", "paid_conversion"),
    ]
    stage_columns = [("Assigned Users", None)] + [
        (stage, outcome)
        for stage, outcome in all_stages
        if outcome in profile["data"].columns
    ]
    for group in ["Control", "Treatment"]:
        user_count = int(profile["group_users"].get(group, 0))
        for stage, outcome_column in stage_columns:
            if outcome_column is None:
                users = user_count
            else:
                outcome = next(
                    (
                        item
                        for item in profile["outcomes"]
                        if item["column"] == outcome_column
                    ),
                    None,
                )
                users = int(outcome[group.lower()]["successes"]) if outcome else 0
            rows.append({"Experiment Group": group, "Stage": stage, "Users": users})
    frame = pd.DataFrame(rows)
    chart = px.line(
        frame,
        x="Stage",
        y="Users",
        color="Experiment Group",
        markers=True,
        text="Users",
        color_discrete_map={"Control": COLORS["blue"], "Treatment": COLORS["teal"]},
        category_orders={"Stage": [stage for stage, _ in stage_columns]},
    )
    chart.update_traces(
        line={"width": 3},
        marker={"size": 9},
        texttemplate="%{y:,}",
        textposition="top center",
        hovertemplate="%{fullData.name}<br>%{x}: %{y:,} users<extra></extra>",
    )
    chart.update_layout(
        height=365,
        margin={"l": 8, "r": 8, "t": 20, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        xaxis={"title": ""},
        yaxis={"title": "Users", "gridcolor": COLORS["grid"], "rangemode": "tozero"},
        legend={"title": ""},
    )
    return chart


def make_outcome_comparison_chart(segments: pd.DataFrame) -> go.Figure:
    rate_columns = [
        column
        for column in ["Onboarding Completion Rate", "Trial Start Rate", "Paid Conversion Rate"]
        if column in segments.columns
    ]
    melted = segments.melt(
        id_vars=["Category"],
        value_vars=rate_columns,
        var_name="Outcome",
        value_name="Rate",
    )
    chart = px.bar(
        melted,
        x="Category",
        y="Rate",
        color="Outcome",
        barmode="group",
        text="Rate",
        color_discrete_sequence=[COLORS["blue"], COLORS["gold"], COLORS["teal"]],
        category_orders={"Category": ["Control", "Treatment"]},
    )
    chart.update_traces(
        texttemplate="%{y:.2f}%",
        textposition="outside",
        hovertemplate="%{x}<br>%{fullData.name}: %{y:.2f}%<extra></extra>",
    )
    chart.update_layout(
        height=340,
        margin={"l": 8, "r": 8, "t": 20, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        xaxis={"title": ""},
        yaxis={"title": "Rate", "ticksuffix": "%", "gridcolor": COLORS["grid"], "rangemode": "tozero"},
        legend={"title": ""},
    )
    return chart


def make_p_value_chart(statistics: pd.DataFrame) -> go.Figure:
    chart = px.bar(
        statistics,
        x="metric",
        y="p_value",
        color="p_value",
        color_continuous_scale=[COLORS["teal"], COLORS["gold"], COLORS["coral"]],
        custom_data=["holm_p_value"],
    )
    chart.update_traces(
        hovertemplate=(
            "%{x}<br>Unadjusted p-value: %{y:.6f}"
            "<br>Existing Holm-adjusted p-value: %{customdata[0]:.6f}<extra></extra>"
        )
    )
    chart.update_layout(
        height=330,
        showlegend=False,
        coloraxis_showscale=False,
        margin={"l": 8, "r": 8, "t": 18, "b": 5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif", "color": COLORS["ink"]},
        xaxis={"title": "", "tickangle": -20},
        yaxis={"title": "Unadjusted p-value", "range": [0, 1], "gridcolor": COLORS["grid"]},
        shapes=[
            {
                "type": "line",
                "x0": -0.5,
                "x1": len(statistics) - 0.5,
                "y0": 0.05,
                "y1": 0.05,
                "line": {"color": COLORS["coral"], "dash": "dash", "width": 2},
            }
        ],
        annotations=[
            {
                "x": 1,
                "xref": "paper",
                "y": 0.05,
                "text": "α = 0.05",
                "showarrow": False,
                "yshift": 10,
                "font": {"color": COLORS["coral"]},
            }
        ],
    )
    return chart


def _build_statistics(
    profile: dict[str, object],
    existing_results: pd.DataFrame | None,
) -> pd.DataFrame:
    adjusted_values: dict[str, float] = {}
    if existing_results is not None and {
        "metric",
        "adjusted_p_value",
    } <= set(existing_results.columns):
        adjusted_values = {
            str(row.metric).strip().lower(): float(row.adjusted_p_value)
            for row in existing_results.itertuples()
        }
    source_metric_names = {
        "onboarding_completed": "onboarding_completion",
        "trial_started": "trial_start",
        "paid_conversion": "paid_conversion",
        "d1_retained": "d1_retention",
        "d7_retained": "d7_retention",
        "d30_retained": "d30_retention",
    }
    rows = []
    for outcome in profile["outcomes"]:
        control = outcome["control"]
        treatment = outcome["treatment"]
        if control["rate"] is None or treatment["rate"] is None:
            continue
        z_score, p_value = two_proportion_test(
            int(control["successes"]),
            int(control["denominator"]),
            int(treatment["successes"]),
            int(treatment["denominator"]),
        )
        source_name = source_metric_names[outcome["column"]]
        holm_p = adjusted_values.get(source_name)
        rows.append(
            {
                "metric": outcome["metric"],
                "control_rate": control["rate"],
                "treatment_rate": treatment["rate"],
                "p_value": p_value,
                "significant": p_value < 0.05,
                "holm_p_value": holm_p,
                "control_n": control["denominator"],
                "treatment_n": treatment["denominator"],
                "z_score": z_score,
            }
        )
    return pd.DataFrame(rows)


def _summary_matches_calculations(
    summary: pd.DataFrame | None,
    profile: dict[str, object],
) -> bool | None:
    required_columns = {
        "experiment_name",
        "metric",
        "control_users",
        "treatment_users",
        "control_conversion_rate",
        "treatment_conversion_rate",
        "absolute_uplift",
    }
    if summary is None or not required_columns <= set(summary.columns):
        return None
    metric_columns = {
        "onboarding_completion": "onboarding_completed",
        "paid_conversion": "paid_conversion",
    }
    filtered = summary.loc[summary["experiment_name"] == "onboarding_flow_v2"]
    checks = 0
    for row in filtered.itertuples():
        outcome_column = metric_columns.get(str(row.metric))
        outcome = next(
            (
                item
                for item in profile["outcomes"]
                if item["column"] == outcome_column
            ),
            None,
        )
        if outcome is None:
            continue
        checks += 1
        if (
            outcome["control"]["rate"] is None
            or outcome["treatment"]["rate"] is None
            or outcome["difference_pp"] is None
        ):
            return False
        checks_pass = (
            int(row.control_users) == profile["group_users"]["Control"]
            and int(row.treatment_users) == profile["group_users"]["Treatment"]
            and abs(float(row.control_conversion_rate) - outcome["control"]["rate"]) < 1e-6
            and abs(float(row.treatment_conversion_rate) - outcome["treatment"]["rate"]) < 1e-6
            and abs(float(row.absolute_uplift) - outcome["difference_pp"]) < 1e-6
        )
        if not checks_pass:
            return False
    return True if checks else None


def _user_analysis_insights(
    profile: dict[str, object],
    comparison: pd.DataFrame,
) -> list[tuple[str, str]]:
    total_groups = sum(int(value) for value in profile["group_users"].values())
    treatment_share = (
        100 * profile["group_users"]["Treatment"] / total_groups if total_groups else 0
    )
    control_share = (
        100 * profile["group_users"]["Control"] / total_groups if total_groups else 0
    )
    share_gap = abs(treatment_share - control_share)
    insights = [
        (
            "Experiment allocation",
            f"Control received {control_share:.2f}% and Treatment {treatment_share:.2f}% "
            f"of assignments (a {share_gap:.2f} percentage-point share difference).",
        )
    ]
    if any(item["rate"] is not None for item in profile["core_outcomes"]):
        highest = max(
            (item for item in profile["core_outcomes"] if item["rate"] is not None),
            key=lambda item: item["rate"],
        )
        insights.append(
            (
                "Most common outcome",
                f"{highest['metric']} was reached by {highest['successes']:,} of "
                f"{highest['denominator']:,} users ({highest['rate']:.2f}%).",
            )
        )
    if not comparison.empty:
        largest = comparison.loc[comparison["Difference (pp)"].abs().idxmax()]
        direction = "higher" if largest["Difference (pp)"] >= 0 else "lower"
        insights.append(
            (
                "Largest group difference",
                f"Treatment's {largest['Metric'].lower()} rate was "
                f"{abs(largest['Difference (pp)']):.2f} pp {direction} than Control.",
            )
        )
    if profile["status_complete"]:
        quality_text = (
            f"All {profile['records']:,} records passed the selected completeness, "
            "uniqueness, and variant checks."
        )
    else:
        quality_text = (
            "Review the missing values, duplicate identifiers/rows, incomplete "
            "outcomes, and variant labels shown in the quality checks."
        )
    insights.append(
        (
            "Data quality",
            f"{'Complete' if profile['status_complete'] else 'Review required'} — {quality_text}",
        )
    )
    return insights


def show_user_segment_page() -> None:
    summary, existing_results, assignments = get_ab_data()
    profile = analyze_user_dataset(assignments)
    st.markdown('<div class="eyebrow">USER-LEVEL ANALYSIS</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">User &amp; Segment Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">How are users distributed, how do experiment groups behave, '
        'and what patterns are visible in the available user-level data?</div>',
        unsafe_allow_html=True,
    )
    source_label("Source: local experiment assignment dataset and existing A/B result files")
    if profile is None:
        st.warning("The local experiment assignment dataset could not be loaded.")
        return
    summary_matches = _summary_matches_calculations(summary, profile)

    group_users = profile["group_users"]
    total_group_users = sum(int(count) for count in group_users.values())
    top_cards = [
        ("Total Records", f"{profile['records']:,}", "Rows in the local assignment file"),
        (
            "Unique Users",
            f"{profile['unique_users']:,}" if profile["unique_users"] is not None else "N/A",
            "Distinct non-missing user IDs",
        ),
        ("Control Users", f"{group_users['Control']:,}", "Valid Control assignments"),
        ("Treatment Users", f"{group_users['Treatment']:,}", "Valid Treatment assignments"),
        ("Missing Values", f"{profile['missing_values']:,}", "Missing cells across all columns"),
    ]
    first_row = st.columns(3, gap="medium")
    for column, card in zip(first_row, top_cards[:3]):
        with column:
            render_kpi(*card)
    second_row = st.columns(2, gap="medium")
    for column, card in zip(second_row, top_cards[3:]):
        with column:
            render_kpi(*card)

    st.markdown("")
    distribution_col, outcomes_col = st.columns(2, gap="large")
    with distribution_col:
        st.markdown("### Experiment group distribution")
        st.caption("User counts and share of all valid experiment assignments")
        if total_group_users:
            st.plotly_chart(
                make_experiment_distribution_chart(profile),
                width="stretch",
                config={"displayModeBar": False},
            )
        else:
            st.info("No valid Control/Treatment assignments are available.")
        control_share = 100 * group_users["Control"] / total_group_users if total_group_users else 0
        treatment_share = 100 * group_users["Treatment"] / total_group_users if total_group_users else 0
        group_count_gap = abs(group_users["Treatment"] - group_users["Control"])
        share_gap = abs(treatment_share - control_share)
        balance_cols = st.columns(2, gap="small")
        with balance_cols[0]:
            render_kpi("Control Assignment Share", f"{control_share:.2f}%", f"{group_users['Control']:,} users")
        with balance_cols[1]:
            render_kpi("Treatment Assignment Share", f"{treatment_share:.2f}%", f"{group_users['Treatment']:,} users")
        st.caption(
            f"Absolute group-size difference: {group_count_gap:,} users · "
            f"assignment-share difference: {share_gap:.2f} percentage points."
        )
        st.markdown(
            '<div class="insight-card">Balanced experiment groups give each version '
            'a similar number of users, making conversion-rate comparisons less '
            'sensitive to group size alone. Similar sizes do not prove randomization '
            'was implemented correctly.</div>',
            unsafe_allow_html=True,
        )

    with outcomes_col:
        st.markdown("### User outcome distribution")
        st.caption("Share of assigned users with each recorded product outcome")
        if profile["core_outcomes"]:
            st.plotly_chart(
                make_user_outcome_chart(profile),
                width="stretch",
                config={"displayModeBar": False},
            )
        else:
            st.info("The expected binary outcome columns are not available in this dataset.")
        st.caption(
            "Rates are calculated from valid outcome records; trial rates use "
            "trial-eligible users when an eligibility column is available."
        )

    st.markdown("")
    st.markdown("### Control vs Treatment outcomes")
    st.caption("Rate difference is Treatment minus Control, expressed in percentage points (pp).")
    comparison_rows = []
    for outcome in profile["outcomes"]:
        if outcome["column"] not in CORE_OUTCOMES:
            continue
        control = outcome["control"]
        treatment = outcome["treatment"]
        comparison_rows.append(
            {
                "Metric": outcome["metric"],
                "Control": control["rate"],
                "Treatment": treatment["rate"],
                "Difference (pp)": outcome["difference_pp"],
                "Control n": control["denominator"],
                "Treatment n": treatment["denominator"],
            }
        )
    comparison = pd.DataFrame(comparison_rows)
    if not comparison.empty:
        display_comparison = comparison.copy()
        for column in ["Control", "Treatment"]:
            display_comparison[column] = display_comparison[column].map(
                lambda value: f"{value:.2f}%" if pd.notna(value) else "N/A"
            )
        display_comparison["Difference (pp)"] = display_comparison["Difference (pp)"].map(
            lambda value: f"{value:+.2f} pp" if pd.notna(value) else "N/A"
        )
        for column in ["Control n", "Treatment n"]:
            display_comparison[column] = display_comparison[column].map(
                lambda value: f"{value:,}"
            )
        st.dataframe(display_comparison, hide_index=True, width="stretch")

    journey_col, index_col = st.columns([1.25, 0.75], gap="large")
    with journey_col:
        st.markdown("### User journey by experiment group")
        st.caption("Counts at each outcome stage, starting from assigned users")
        if total_group_users and any(
            item["column"] in CORE_OUTCOMES for item in profile["outcomes"]
        ):
            st.plotly_chart(
                make_user_journey_chart(profile),
                width="stretch",
                config={"displayModeBar": False},
            )
    with index_col:
        st.markdown("### Conversion Index")
        index_values = []
        for group in ["Control", "Treatment"]:
            onboarding = next(
                (
                    item[group.lower()]["successes"]
                    for item in profile["outcomes"]
                    if item["column"] == "onboarding_completed"
                ),
                0,
            )
            paid = next(
                (
                    item[group.lower()]["successes"]
                    for item in profile["outcomes"]
                    if item["column"] == "paid_conversion"
                ),
                0,
            )
            index_rate = 100 * paid / onboarding if onboarding else None
            index_values.append(
                {"Experiment Group": group, "Conversion Index": index_rate}
            )
        for item in index_values:
            value = item["Conversion Index"]
            render_kpi(
                f"{item['Experiment Group']} Conversion Index",
                f"{value:.2f}%" if value is not None else "N/A",
                "Paid conversions ÷ onboarding completions",
            )
            st.markdown("")
        st.markdown(
            '<div class="insight-card">This index asks: among users who completed '
            'onboarding, what percentage ultimately converted to paid? It is a '
            'derived ratio of two user-level outcome counts.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.markdown("### Data Quality Check")
    quality_cols = st.columns(4, gap="medium")
    quality_items = [
        ("Total Records", f"{profile['records']:,}", "Rows loaded"),
        (
            "Unique Users",
            f"{profile['unique_users']:,}" if profile["unique_users"] is not None else "N/A",
            "Distinct user IDs",
        ),
        (
            "Duplicate User IDs",
            f"{profile['duplicate_users']:,}" if profile["duplicate_users"] is not None else "N/A",
            "Repeated IDs after first occurrence",
        ),
        ("Missing Values", f"{profile['missing_values']:,}", "Missing cells"),
        ("Duplicate Rows", f"{profile['duplicate_rows']:,}", "Fully repeated records"),
        ("Invalid / Unknown Variants", f"{profile['invalid_variants']:,}", "Outside Control/Treatment"),
        (
            "Complete Core Outcomes",
            f"{profile['complete_outcome_pct']:.2f}%",
            f"{profile['complete_outcome_records']:,} records with valid outcomes",
        ),
    ]
    for start in range(0, len(quality_items), 4):
        cols = quality_cols if start == 0 else st.columns(4, gap="medium")
        for column, card in zip(cols, quality_items[start : start + 4]):
            with column:
                render_kpi(*card)
    if profile["status_complete"]:
        st.success("✓ Complete — no missing values, duplicate rows/users, or unknown variants; core outcomes are complete.")
    else:
        st.warning("⚠ Review Required — one or more data-quality checks need attention.")

    st.markdown("")
    st.markdown("### Statistical Comparison")
    st.caption("Two-sided pooled two-proportion z-tests, α = 0.05. Rates use outcome-eligible users when an eligibility flag exists.")
    statistics = _build_statistics(profile, existing_results)
    if not statistics.empty:
        display_statistics = statistics[
            [
                "metric",
                "control_rate",
                "treatment_rate",
                "p_value",
                "significant",
                "holm_p_value",
            ]
        ].rename(
            columns={
                "metric": "Metric",
                "control_rate": "Control Rate",
                "treatment_rate": "Treatment Rate",
                "p_value": "Unadjusted p-value",
                "significant": "Significant? (raw α=.05)",
                "holm_p_value": "Holm-adjusted p (existing)",
            }
        )
        for column in ["Control Rate", "Treatment Rate"]:
            display_statistics[column] = display_statistics[column].map(
                lambda value: f"{value:.2f}%"
            )
        display_statistics["Unadjusted p-value"] = display_statistics[
            "Unadjusted p-value"
        ].map(lambda value: f"{value:.6f}")
        display_statistics["Significant? (raw α=.05)"] = display_statistics[
            "Significant? (raw α=.05)"
        ].map(lambda value: "Yes" if value else "No")
        display_statistics["Holm-adjusted p (existing)"] = display_statistics[
            "Holm-adjusted p (existing)"
        ].map(lambda value: f"{value:.6f}" if pd.notna(value) else "—")
        stat_col, p_chart_col = st.columns([1.2, 0.8], gap="large")
        with stat_col:
            st.dataframe(display_statistics, hide_index=True, width="stretch")
        with p_chart_col:
            st.plotly_chart(
                make_p_value_chart(statistics),
                width="stretch",
                config={"displayModeBar": False},
            )
        st.caption(
            "If unadjusted p-value < 0.05, the difference is statistically significant "
            "at the 5% level under this test. The added p-values are unadjusted; "
            "the existing A/B results retain their Holm multiple-comparison correction."
        )

    st.markdown("")
    st.markdown("### Simple User Segmentation")
    dimensions = profile["dimensions"]
    if dimensions:
        dimension = st.selectbox(
            "Available categorical dimension",
            dimensions,
            key="user_analysis_dimension",
        )
        segment_metrics = build_user_segment_metrics(
            profile["analytical"], dimension
        )
        if not segment_metrics.empty:
            segment_chart_col, segment_table_col = st.columns([1, 1], gap="large")
            with segment_chart_col:
                st.plotly_chart(
                    make_outcome_comparison_chart(segment_metrics),
                    width="stretch",
                    config={"displayModeBar": False},
                )
            with segment_table_col:
                shown = segment_metrics.copy()
                shown["User Count"] = shown["User Count"].map(lambda value: f"{value:,}")
                for column in shown.columns:
                    if column.endswith("Rate"):
                        shown[column] = shown[column].map(
                            lambda value: f"{value:.2f}%" if pd.notna(value) else "N/A"
                        )
                st.dataframe(shown, hide_index=True, width="stretch")
        st.caption(
            "Only meaningful categorical fields present in the local dataset are offered. "
            "This file supports experiment variant segmentation; it does not contain "
            "acquisition channel, platform, device tier, or region."
        )
    else:
        st.info("No usable categorical segment dimension is available in the local dataset.")

    st.markdown("")
    st.markdown("### Key User Insights")
    insights = _user_analysis_insights(profile, comparison)
    for start in range(0, len(insights), 2):
        insight_cols = st.columns(2, gap="medium")
        for column, (title, body) in zip(insight_cols, insights[start : start + 2]):
            with column:
                render_insight(title, body)

    with st.expander("Dataset fields and methodology"):
        field_rows = []
        date_fields = {"assigned_at", "signup_ts", "data_end_date"}
        outcome_columns = set(CORE_OUTCOMES) | set(RETENTION_OUTCOMES)
        eligibility_columns = {
            eligibility
            for _, eligibility in [*CORE_OUTCOMES.values(), *RETENTION_OUTCOMES.values()]
            if eligibility
        }
        for column in profile["data"].columns:
            if column == "user_id":
                classification = "User identifier"
            elif column == "variant":
                classification = "Categorical experiment group"
            elif column in date_fields:
                classification = "Assignment/signup date or timestamp"
            elif column in outcome_columns:
                classification = "Binary outcome (0/1)"
            elif column in eligibility_columns:
                classification = "Binary eligibility flag (0/1)"
            else:
                classification = "Other dataset field"
            field_rows.append(
                {
                    "Column": column,
                    "Data Type": str(profile["data"][column].dtype),
                    "Classification": classification,
                }
            )
        st.dataframe(pd.DataFrame(field_rows), hide_index=True, width="stretch")
        numeric_columns = [
            column
            for column in profile["data"].columns
            if pd.api.types.is_numeric_dtype(profile["data"][column])
        ]
        binary_numeric_columns = [
            column
            for column in numeric_columns
            if set(profile["data"][column].dropna().unique()) <= {0, 1}
        ]
        continuous_columns = [
            column for column in numeric_columns if column not in binary_numeric_columns
        ]
        categorical_values = {
            dimension: profile["data"][dimension].dropna().unique().tolist()
            for dimension in profile["dimensions"]
        }
        st.caption(f"Detected categorical segment values: {categorical_values}")
        if continuous_columns:
            st.caption(f"Other numeric measures: {continuous_columns}")
        else:
            st.caption(
                "No continuous numeric measures are present; numeric outcome and "
                f"eligibility fields are binary 0/1 flags ({len(binary_numeric_columns)} columns)."
            )
        st.markdown(
            """
            - **Source:** local `data/ab_test_dataset.csv`; statistical cross-checks
              use `data/ab_test_results.csv` and `outputs/experiments/ab_test_summary.csv`.
            - **Categorical variable:** a field containing group labels rather than
              a measured amount; `variant` is the usable category in this file.
            - **Data quality:** checks for missing cells, repeated user IDs/rows,
              valid variant labels, and complete binary core outcomes. Duplicates
              can overcount users; missing outcomes can bias denominators.
            - **Outcomes:** binary indicators are summarized as successes divided by
              valid eligible users. The Conversion Index is paid conversions divided
              by onboarding completions within each variant.
            - **P-value:** under the null hypothesis of equal group rates, it is the
              probability of seeing a difference at least this extreme from random
              variation. It is not the probability that the null hypothesis is true.
            - **Statistical significance:** at α = 0.05, an unadjusted p-value below
              0.05 is significant for this two-sided pooled two-proportion z-test.
              The added raw tests are shown beside existing Holm-adjusted results;
              they do not replace the validated experiment analysis.
            - **Balanced groups:** similar assignment counts make a rate comparison
              easier to interpret, but do not by themselves confirm correct randomization.
            - **Limitations:** the local assignment data has experiment variants but
              no acquisition-channel, platform, device-tier, or region attributes.
            """
        )
        if summary_matches is True:
            st.success(
                "The available onboarding and paid metrics match the validated "
                "experiment summary's counts, rates, and uplifts."
            )
        elif summary_matches is False:
            st.warning(
                "At least one available onboarding or paid metric differs from the "
                "validated experiment summary; review the local source files."
            )
        else:
            st.info("No comparable rows were available in the validated experiment summary.")


def show_overview() -> None:
    funnel = DOCUMENTED_RESULTS["funnel"]
    retention = DOCUMENTED_RESULTS["retention_pct"]
    revenue = DOCUMENTED_RESULTS["monetization"]
    funnel_metrics = calculate_funnel_metrics(funnel)
    summary, raw_results, assignments = get_ab_data()
    primary = None
    if summary is not None and {"experiment_name", "metric"} <= set(summary.columns):
        matching = summary[
            (summary["experiment_name"] == "onboarding_flow_v2")
            & (summary["metric"] == "onboarding_completion")
        ]
        if not matching.empty:
            required_columns = {
                "control_conversion_rate",
                "treatment_conversion_rate",
                "absolute_uplift",
                "relative_uplift",
                "confidence_interval_lower",
                "confidence_interval_upper",
                "p_value",
                "statistically_significant",
            }
            if required_columns <= set(matching.columns):
                primary = matching.iloc[0]
    guardrail = None
    if summary is not None and {"experiment_name", "metric"} <= set(summary.columns):
        matching_guardrail = summary[
            (summary["experiment_name"] == "onboarding_flow_v2")
            & (summary["metric"] == "paid_conversion")
        ]
        if not matching_guardrail.empty and {
            "absolute_uplift",
            "statistically_significant",
        } <= set(matching_guardrail.columns):
            guardrail = matching_guardrail.iloc[0]

    st.markdown('<div class="eyebrow">PRODUCT ANALYTICS &amp; EXPERIMENTATION</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-title">Product Analytics &amp; User Retention Dashboard</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-subtitle">User Journey • Retention • Experimentation • Predictive Analytics</div>',
        unsafe_allow_html=True,
    )
    source_label("Documented project analysis · Previously reported BigQuery results")

    st.markdown("#### Project snapshot")
    card_values = [
        ("Total Users", format_compact_count(funnel["Signup"]), "34,000 signups"),
        (
            "Trial Users",
            format_compact_count(funnel["Trial"]),
            f"{100 * funnel['Trial'] / funnel['Signup']:.2f}% of signups",
        ),
        (
            "Paid Users",
            format_compact_count(funnel["Paid"]),
            f"{100 * funnel['Paid'] / funnel['Signup']:.2f}% of signups",
        ),
        ("D30 Retention", f"{retention['D30']:.2f}%", "Exact-day app_open"),
        ("Net Revenue", f"${revenue['Net Revenue'] / 1000:.1f}K", "After refunds"),
    ]
    first_row = st.columns(3, gap="medium")
    for column, (label, value, detail) in zip(first_row, card_values[:3]):
        with column:
            render_kpi(label, value, detail)
    second_row = st.columns(2, gap="medium")
    for column, (label, value, detail) in zip(second_row, card_values[3:]):
        with column:
            render_kpi(label, value, detail)

    st.markdown("")
    journey_col, retention_col = st.columns([1.15, 0.85], gap="large")

    with journey_col:
        st.markdown("### User journey")
        st.markdown(
            '<div class="section-caption">Signup → Onboarding → Trial → Paid</div>',
            unsafe_allow_html=True,
        )
        source_label("Source: documented funnel counts · conversions and losses derived from these counts")
        st.plotly_chart(
            make_funnel_chart(funnel_metrics),
            width="stretch",
            config={"displayModeBar": False},
        )
        step_cols = st.columns(3, gap="small")
        for index, row in enumerate(funnel_metrics.iloc[1:].itertuples()):
            with step_cols[index]:
                render_kpi(
                    f"{funnel_metrics.iloc[index]['stage']} → {row.stage}",
                    f"{row.conversion_pct:.2f}%",
                    f"{row.dropoff_users:,} users lost",
                )

    with retention_col:
        st.markdown("### Retention snapshot")
        st.markdown(
            '<div class="section-caption">Return activity at exact calendar days after signup</div>',
            unsafe_allow_html=True,
        )
        source_label("Source: documented project analysis")
        st.plotly_chart(
            make_retention_chart(retention),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.markdown(
            '<div class="insight-card">Retention declines most sharply between the early '
            'engagement stages, highlighting the importance of continued user engagement '
            'after onboarding.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    revenue_col, experiment_col = st.columns([1.05, 0.95], gap="large")
    with revenue_col:
        st.markdown("### Revenue snapshot")
        source_label("Source: documented project analysis")
        revenue_cards = [
            ("Gross Revenue", f"${revenue['Gross Revenue'] / 1000:.1f}K"),
            ("Refunds", f"${revenue['Refunds']:,.2f}"),
            ("Net Revenue", f"${revenue['Net Revenue'] / 1000:.1f}K"),
        ]
        rev_cols = st.columns(3, gap="small")
        for column, (label, value) in zip(rev_cols, revenue_cards):
            with column:
                render_kpi(label, value, "USD")
        st.plotly_chart(
            make_revenue_chart(revenue),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.caption(
            f"Revenue per payer: ${revenue['Revenue per Payer']:.2f} · "
            f"Cancellation rate: {revenue['Cancellation Rate']:.2f}% · Revenue ≠ profit."
        )

    with experiment_col:
        st.markdown("### Onboarding Flow Experiment")
        if primary is None:
            st.info("The local validated A/B summary is not available.")
        else:
            source_label("Source: local A/B experiment summary")
            counts_text = ""
            if assignments is not None and {"variant", "user_id"} <= set(assignments.columns):
                counts = assignments.groupby("variant")["user_id"].nunique()
                counts_text = (
                    f"Control {int(counts.get('control', 0)):,} · "
                    f"Treatment {int(counts.get('treatment', 0)):,} users"
                )
            st.caption(counts_text)
            st.plotly_chart(
                make_ab_chart(primary),
                width="stretch",
                config={"displayModeBar": False},
            )
            uplift = float(primary["absolute_uplift"])
            p_value = float(primary["p_value"])
            st.markdown(
                f'<div class="insight-card"><div class="insight-title">'
                f'Treatment increased onboarding completion by {uplift:.2f} percentage points.</div>'
                f'Relative uplift: {float(primary["relative_uplift"]):+.2f}% · '
                f'p-value: {p_value:.6f} · 95% CI: '
                f'[{float(primary["confidence_interval_lower"]):+.2f}, '
                f'{float(primary["confidence_interval_upper"]):+.2f}] pp</div>',
                unsafe_allow_html=True,
            )

    st.markdown("")
    st.markdown("### Key analytics insights")
    insights = build_overview_insights(funnel_metrics, retention, primary, guardrail)
    for start in range(0, len(insights), 2):
        insight_columns = st.columns(2, gap="medium")
        for column, (title, body) in zip(insight_columns, insights[start : start + 2]):
            with column:
                render_insight(title, body)

    with st.expander("Data Sources & Methodology"):
        st.markdown(
            """
            - **Funnel, retention, and monetization:** project-level results
              previously documented from the BigQuery SQL analysis in
              `README.md`. Stage conversion and drop-off shown here are derived
              from the documented stage counts.
            - **A/B experiment:** local `outputs/experiments/ab_test_summary.csv`,
              `data/ab_test_results.csv`, and `data/ab_test_dataset.csv`.
              The summary contains the project's existing two-proportion tests
              and confidence intervals.
            - **SQL layer:** queries in `sql/` target the project's BigQuery
              tables and cleaned views. This app does not execute SQL or query
              BigQuery.
            - **Unavailable detailed exports:** the local segment, cohort,
              activity, and SQL result CSVs are empty or header-only, so this
              overview does not invent their values.
            """
        )


def show_methodology_page() -> None:
    st.markdown("## Data & Methodology")
    st.markdown(
        "A concise inventory of the local assets behind the current dashboard foundation."
    )
    inventory = pd.DataFrame(
        [
            ("`data/ab_test_dataset.csv`", "11,462 assignment-level rows; 16 columns", "Variant counts, binary outcomes, data quality, and user-level comparison"),
            ("`data/ab_test_results.csv`", "6 metric rows", "Existing statistical test and multiple-comparison results"),
            ("`outputs/experiments/ab_test_summary.csv`", "2 metric rows", "Executive A/B experiment snapshot"),
            ("`outputs/dashboard/`", "A/B populated; other files header-only", "Dashboard export templates"),
            ("`outputs/funnel/`, `outputs/retention/`, `outputs/sql/`", "Header-only or empty files", "No local channel/platform/device/region segment result rows"),
            ("`dashboard/dashboard.png`", "Archived dashboard image", "Reference to previously rendered project analysis"),
            ("`sql/01`–`sql/11`", "BigQuery analysis layer", "Data quality, funnel, segmentation, retention, monetization, and experiment queries"),
        ],
        columns=["File or folder", "Local status", "What it can support"],
    )
    st.dataframe(inventory, hide_index=True, width="stretch")
    st.markdown("### Current calculation sources")
    st.markdown(
        """
        - **Loaded from local CSVs:** A/B sample counts, conversion rates,
          uplifts, confidence intervals, p-values, and significance labels.
        - **Calculated in the app:** funnel stage-to-stage rates and user
          drop-offs, derived from documented stage counts; compact KPI display
          values; local user-outcome rates, percentage-point differences,
          conversion indices, data-quality checks, and two-proportion tests.
        - **Displayed from documented results:** overall funnel counts,
          D1/D7/D30 retention, and monetization values in `README.md`.
        - **User Funnel segment comparison:** local experiment assignments
          support a Control-versus-Treatment comparison. Rates use all assigned
          users as the denominator; this is an experiment-population comparison,
          not a broad acquisition, platform, device, or region analysis.
        - **User & Segment Analysis:** the local assignment file supports the
          `variant` category and onboarding, trial, paid, and exact-day
          retention outcomes. Calculated raw test p-values appear beside the
          existing Holm-adjusted results from `data/ab_test_results.csv`.
        - **Not locally recalculated:** BigQuery-derived results. The app does
          not claim a local BigQuery run.
        """
    )



# Phase 9 pages read only validated local outputs and documented historical analysis.
RETENTION_DIR = PROJECT_ROOT / "outputs" / "retention"
EVALUATION_DIR = PROJECT_ROOT / "outputs" / "evaluation"
CLEANING_REPORT_PATH = PROJECT_ROOT / "outputs" / "cleaned_data" / "data_quality_report.csv"
LOCAL_DATA_PATH = PROJECT_ROOT / "data" / "ab_test_dataset.csv"


def _load_dashboard_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        st.error(f"Required dashboard data is missing: {path.relative_to(PROJECT_ROOT)}")
        return pd.DataFrame()
    return pd.read_csv(path)


def _dashboard_header(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def show_overview() -> None:
    _dashboard_header(
        "Product Analytics &amp; User Retention",
        "Mobile subscription user journey, retention, experimentation &amp; predictive analytics",
    )
    funnel = _load_dashboard_csv(RETENTION_DIR / "funnel_summary.csv")
    retention = _load_dashboard_csv(RETENTION_DIR / "overall_retention.csv")
    variant = _load_dashboard_csv(RETENTION_DIR / "retention_by_variant.csv")
    if any(frame.empty for frame in (funnel, retention, variant)):
        return
    f = funnel.set_index("stage")
    r = retention.set_index("metric").retention_rate
    kpis = [
        ("Total Users", f"{int(f.loc['Assigned','users']):,}"),
        ("Onboarding", f"{f.loc['Onboarding Completed','conversion_from_previous']:.2%}"),
        ("Paid Conversion", f"{f.loc['Paid Conversion','users']/f.loc['Assigned','users']:.2%}"),
        ("D1 Retention", f"{r['D1']:.2%}"),
        ("D7 Retention", f"{r['D7']:.2%}"),
        ("D30 Retention", f"{r['D30']:.2%}"),
    ]
    source_label("11,462 experiment-assignment users &bull; Locally reproducible analysis")
    for offset in range(0, len(kpis), 3):
        cols = st.columns(3, gap="medium")
        for col, (label, value) in zip(cols, kpis[offset:offset + 3]):
            with col:
                st.metric(label, value)
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("### User Funnel")
        chart = go.Figure(go.Funnel(
            x=funnel["users"], y=funnel["stage"],
            text=funnel["users"].map(lambda value: f"{int(value):,}"),
            textinfo="text", textposition="inside",
            insidetextfont=dict(color="#FFFFFF", size=14),
            marker=dict(color=["#2563EB", "#3B82F6", "#16A34A", "#15803D"]),
            hovertemplate="%{y}<br>%{x:,.0f} users<extra></extra>",
        ))
        chart.update_layout(height=360, margin=dict(l=8, r=8, t=15, b=8), showlegend=False,
                            xaxis=dict(title="Users", tickformat=",.0f"))
        st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
    with right:
        st.markdown("### Retention Overview")
        chart = px.line(
            retention, x="metric", y="retention_rate", markers=True,
            text=retention.retention_rate.map(lambda value: f"{value:.1%}"),
        )
        chart.update_traces(textposition="top center", line_color=COLORS["teal"], hovertemplate="%{x}: %{y:.2%}<extra></extra>")
        chart.update_layout(height=360, xaxis_title="Retention day", yaxis_title="Eligible users retained", yaxis_tickformat=".0%", margin=dict(l=8, r=8, t=15, b=8))
        st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
    st.markdown("### Control vs Treatment Retention")
    chart = go.Figure()
    for name, color in (("control", COLORS["blue"]), ("treatment", COLORS["coral"])):
        chart.add_trace(go.Bar(name=name.title(), x=variant.metric, y=variant[f"{name}_rate"] * 100, marker_color=color, text=(variant[f"{name}_rate"] * 100).map(lambda value: f"{value:.2f}%"), textposition="outside"))
    chart.update_layout(barmode="group", height=340, xaxis_title="", yaxis_title="Retention (%)", margin=dict(l=8, r=8, t=15, b=8), legend=dict(orientation="h", y=1.12))
    st.plotly_chart(chart, width="stretch", config={"displayModeBar": False})
    st.markdown("### Key Insights")
    st.markdown(
        "- The largest absolute funnel loss is between assignment and onboarding: **5,171 users**.\n"
        "- Onboarding-to-trial is the weakest funnel step at **29.79%**.\n"
        "- Treatment onboarding is **56.54%** vs **53.20%** for Control (+3.35 pp); paid conversion is **9.46%** vs **10.15%** (-0.69 pp, not significant).\n"
        "- Retention declines most from D1 to D7 (**-22.38 pp**)."
    )
    st.caption("The local assignment file has no revenue, acquisition, device, platform, or regional dimensions.")

def show_funnel_page() -> None:
    _dashboard_header("User Funnel", "Ordered progression using the validated Phase 3 stage and eligibility logic")
    source_label("Locally reproducible analysis | outputs/retention/funnel_summary.csv")
    frame = _load_dashboard_csv(RETENTION_DIR / "funnel_summary.csv")
    if frame.empty: return
    total = int(frame.iloc[0].users)
    paid = int(frame.iloc[-1].users)
    a,b = st.columns(2)
    a.metric("Assigned to Paid", f"{paid/total:.2%}", f"{paid:,} of {total:,} users")
    b.metric("Largest stage loss", f"{int(frame.iloc[0].dropoff_users):,}", "Assigned to Onboarding")
    left,right=st.columns([1.1,.9],gap="large")
    with left:
        fig=px.funnel(frame,x="users",y="stage",category_orders={"stage":["Assigned","Onboarding Completed","Trial Started","Paid Conversion"]})
        fig.update_layout(height=440,margin=dict(l=10,r=10,t=20,b=10),showlegend=False)
        st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})
    with right:
        display=frame.rename(columns={"stage":"Stage","users":"Users","conversion_from_previous":"Stage conversion","dropoff_users":"Drop-off users","dropoff_rate":"Drop-off rate"}).copy()
        display["Stage conversion"]=display["Stage conversion"].map(lambda x:f"{x:.2%}")
        display["Drop-off rate"]=display["Drop-off rate"].map(lambda x:f"{x:.2%}")
        st.dataframe(display,hide_index=True,width="stretch")
    st.markdown("### What the local funnel shows")
    st.markdown(
        f"- **Onboarding:** {int(frame.iloc[1].users):,} of {total:,} assigned users ({frame.iloc[1].conversion_from_previous:.2%}).\n"
        f"- **Trial:** {int(frame.iloc[2].users):,} users; {frame.iloc[2].conversion_from_previous:.2%} of onboarding completers.\n"
        f"- **Paid:** {paid:,} users; {frame.iloc[3].conversion_from_previous:.2%} of trial starters and {paid/total:.2%} of all assigned users."
    )
    st.caption("Stage-to-stage conversion uses the preceding ordered stage. Assigned-to-paid is an end-to-end rate, not the Paid stage conversion.")


def show_retention_page() -> None:
    _dashboard_header("Retention &amp; Cohorts", "Exact-day retention and monthly assignment-cohort views")
    source_label("Locally reproducible analysis | Phase 8 retention outputs")
    overall=_load_dashboard_csv(RETENTION_DIR/"overall_retention.csv")
    variant=_load_dashboard_csv(RETENTION_DIR/"retention_by_variant.csv")
    cohort=_load_dashboard_csv(RETENTION_DIR/"assignment_cohorts.csv")
    decay=_load_dashboard_csv(RETENTION_DIR/"retention_decay.csv")
    if any(df.empty for df in (overall,variant,cohort,decay)): return
    cols=st.columns(3)
    for col,row in zip(cols,overall.itertuples(index=False)):
        col.metric(f"{row.metric} Retention",f"{row.retention_rate:.2%}",f"{row.retained_users:,} / {row.eligible_users:,} eligible")
    st.markdown("### Control vs Treatment")
    fig=go.Figure()
    for variant_name,color in [("control",COLORS["blue"]),("treatment",COLORS["coral"])]:
        fig.add_trace(go.Bar(name=variant_name.title(),x=variant.metric,y=variant[f"{variant_name}_rate"]*100,marker_color=color,text=(variant[f"{variant_name}_rate"]*100).map(lambda x:f"{x:.2f}%"),textposition="outside"))
    fig.update_layout(barmode="group",height=380,yaxis_title="Retention (%)",xaxis_title="",margin=dict(l=10,r=10,t=20,b=10),legend=dict(orientation="h",y=1.12))
    st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})
    v=variant.copy(); v["Control"] = v.control_rate.map(lambda x:f"{x:.2%}"); v["Treatment"] = v.treatment_rate.map(lambda x:f"{x:.2%}"); v["Treatment minus Control"] = v.difference_pp.map(lambda x:f"{x:+.2f} pp")
    st.dataframe(v[["metric","Control","Treatment","Treatment minus Control"]].rename(columns={"metric":"Retention day"}),hide_index=True,width="stretch")
    st.markdown("### Assignment Cohorts")
    st.caption("Cohorts are grouped by assignment month from assigned_at; they are not acquisition or signup cohorts.")
    fig=go.Figure()
    for day,color in [("d1",COLORS["blue"]),("d7",COLORS["gold"]),("d30",COLORS["teal"])]:
        fig.add_trace(go.Scatter(x=cohort.assignment_cohort,y=cohort[f"{day}_retention"]*100,mode="lines+markers",name=day.upper(),line=dict(color=color,width=2),hovertemplate="Assignment cohort %{x}<br>Retention %{y:.2f}%<extra></extra>"))
    fig.update_layout(height=400,xaxis_title="Assignment month",yaxis_title="Eligible users retained (%)",margin=dict(l=10,r=10,t=20,b=10),legend=dict(orientation="h",y=1.12))
    st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})
    cohort_display=cohort[["assignment_cohort","assigned_users","d1_retention","d7_retention","d30_retention"]].copy()
    for c in ("d1_retention","d7_retention","d30_retention"): cohort_display[c]=cohort_display[c].map(lambda x:f"{x:.2%}")
    st.dataframe(cohort_display.rename(columns={"assignment_cohort":"Assignment Cohort","assigned_users":"Assigned Users","d1_retention":"D1","d7_retention":"D7","d30_retention":"D30"}),hide_index=True,width="stretch")
    st.markdown("### Retention decay")
    d=decay.copy(); d["Start rate"]=d.start_rate.map(lambda x:f"{x:.2%}"); d["End rate"]=d.end_rate.map(lambda x:f"{x:.2%}"); d["Change"]=d.change_pp.map(lambda x:f"{x:+.2f} pp")
    st.dataframe(d[["transition","Start rate","End rate","Change"]].rename(columns={"transition":"Transition"}),hide_index=True,width="stretch")


def show_ab_page() -> None:
    _dashboard_header("A/B Experiment", "Control vs Treatment Outcomes")
    source_label("Locally reproducible analysis | Existing Phase 4 results")
    st.info("Two-sided pooled two-proportion z-test | alpha = 0.05 | no multiple-comparison adjustment. Statistical significance is not automatic causal proof; this is an analysis of the provided experiment dataset.")
    frame = _load_dashboard_csv(RETENTION_DIR / "ab_experiment_summary.csv")
    if frame.empty:
        return
    labels = {
        "onboarding_completed": "Onboarding", "trial_started": "Trial",
        "paid_conversion": "Paid Conversion", "d1_retained": "D1",
        "d7_retained": "D7", "d30_retained": "D30",
    }
    # Phase 4 stores rates on a 0-100 scale; differences and CI bounds are already pp.
    display = pd.DataFrame({
        "Metric": frame.metric.map(labels),
        "Control": frame.control_rate.map(lambda value: f"{value:.2f}%"),
        "Treatment": frame.treatment_rate.map(lambda value: f"{value:.2f}%"),
        "Difference (pp)": frame.difference_pp.map(lambda value: f"{value:+.2f} pp"),
        "p-value": frame.p_value.map(lambda value: f"{value:.6f}"),
        "95% CI": frame.apply(lambda row: f"[{row.ci_lower_pp:+.2f}, {row.ci_upper_pp:+.2f}] pp", axis=1),
        "Significant?": frame.significant_at_0_05.map(lambda value: "Yes" if value else "No"),
    })
    st.dataframe(display, hide_index=True, width="stretch", column_config={
        "Metric": st.column_config.TextColumn(width="medium"),
        "Control": st.column_config.TextColumn(width="small"),
        "Treatment": st.column_config.TextColumn(width="small"),
        "Difference (pp)": st.column_config.TextColumn(width="small"),
        "p-value": st.column_config.TextColumn(width="small"),
        "95% CI": st.column_config.TextColumn(width="medium"),
        "Significant?": st.column_config.TextColumn(width="small"),
    })
    onboarding = frame.loc[frame.metric.eq("onboarding_completed")].iloc[0]
    paid = frame.loc[frame.metric.eq("paid_conversion")].iloc[0]
    left, right = st.columns(2, gap="large")
    with left, st.container(border=True):
        st.markdown("#### Onboarding result")
        st.markdown(f"Control **{onboarding.control_rate:.2f}%** | Treatment **{onboarding.treatment_rate:.2f}%**")
        st.metric("Difference", f"{onboarding.difference_pp:+.2f} pp", help=f"p = {onboarding.p_value:.6f}; 95% CI [{onboarding.ci_lower_pp:+.2f}, {onboarding.ci_upper_pp:+.2f}] pp")
    with right, st.container(border=True):
        st.markdown("#### Paid conversion guardrail")
        st.markdown(f"Control **{paid.control_rate:.2f}%** | Treatment **{paid.treatment_rate:.2f}%**")
        st.metric("Difference", f"{paid.difference_pp:+.2f} pp", help=f"p = {paid.p_value:.6f}; 95% CI [{paid.ci_lower_pp:+.2f}, {paid.ci_upper_pp:+.2f}] pp")
        st.caption("This difference is not statistically significant.")
    st.caption("No overall experiment winner is declared. Statistical significance does not establish causality.")

def show_ml_page() -> None:
    _dashboard_header("ML Retention Prediction", "Phase 7 held-out evaluation | Positive class: D30 retention")
    metrics = _load_dashboard_csv(EVALUATION_DIR / "model_comparison.csv")
    cm = _load_dashboard_csv(EVALUATION_DIR / "confusion_matrices.csv")
    roc = _load_dashboard_csv(EVALUATION_DIR / "roc_curve_data.csv")
    pr = _load_dashboard_csv(EVALUATION_DIR / "precision_recall_curve_data.csv")
    if any(frame.empty for frame in (metrics, cm, roc, pr)):
        return
    cols = st.columns(4, gap="medium")
    for col, label, value in zip(cols, ("Models", "Test Users", "Target", "Positive Users"), ("3", "2,293", "D30 Retention", "338")):
        col.metric(label, value)
    st.warning("Class imbalance: 9,770 non-retained users vs 1,692 retained users. Accuracy alone is insufficient.")
    st.markdown("Logistic Regression and Decision Tree predicted no positive users at the default threshold; their 85.26% accuracy is majority-class accuracy and must not be interpreted alone.")
    st.markdown("### Model Comparison")
    display = metrics.rename(columns={"model":"Model","accuracy":"Accuracy","precision":"Precision","recall":"Recall","f1_score":"F1","roc_auc":"ROC-AUC"}).copy()
    for column in ("Accuracy", "Precision", "Recall", "F1", "ROC-AUC"):
        display[column] = display[column].map(lambda value: f"{value:.4f}")
    st.dataframe(display, hide_index=True, width="stretch")
    knn = metrics.loc[metrics.model.eq("K-Nearest Neighbors")].iloc[0]
    st.caption(f"KNN: precision {knn.precision:.4f}, recall {knn.recall:.4f}, F1 {knn.f1_score:.4f}, ROC-AUC {knn.roc_auc:.4f}. No model is labeled best.")
    st.markdown("### ROC Curves")
    fig = go.Figure()
    for name, group in roc.groupby("model", sort=False):
        auc_value = metrics.loc[metrics.model.eq(name), "roc_auc"].iloc[0]
        fig.add_trace(go.Scatter(x=group.fpr, y=group.tpr, mode="lines", name=f"{name} (AUC {auc_value:.3f})"))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Chance", line=dict(dash="dash", color="#8994A0")))
    fig.update_layout(height=390, xaxis_title="False positive rate", yaxis_title="True positive rate", xaxis=dict(range=[0, 1]), yaxis=dict(range=[0, 1]), margin=dict(l=8, r=8, t=15, b=8), legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.markdown("### Precision-Recall Curves")
    fig = go.Figure()
    for name, group in pr.groupby("model", sort=False):
        fig.add_trace(go.Scatter(x=group.recall, y=group.precision, mode="lines", name=name))
    fig.add_hline(y=1692/11462, line_dash="dash", line_color="#8994A0", annotation_text="Positive-class prevalence")
    fig.update_layout(height=390, xaxis_title="Recall for retained users", yaxis_title="Precision for predicted retained users", xaxis=dict(range=[0, 1]), yaxis=dict(range=[0, 1]), margin=dict(l=8, r=8, t=15, b=8), legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.markdown("### Confusion Matrices")
    cols = st.columns(3, gap="medium")
    for col, row in zip(cols, cm.itertuples(index=False)):
        with col, st.container(border=True):
            st.markdown(f"**{row.model}**")
            table = pd.DataFrame([[row.true_negative, row.false_positive], [row.false_negative, row.true_positive]], index=["Actual not retained", "Actual retained"], columns=["Predicted not retained", "Predicted retained"])
            st.dataframe(table, width="stretch")
    st.caption("Evaluation uses the Phase 6 test set. Results describe this dataset only; they do not establish causality, production readiness, or broader generalization.")

def show_sql_page() -> None:
    _dashboard_header("SQL Analysis", "Query inventory and methodology context")
    sql_files = sorted((PROJECT_ROOT / "sql").glob("*.sql"))
    c1, c2, c3 = st.columns(3)
    c1.metric("SQL analysis files", str(len(sql_files)))
    c2.metric("Query result exports", str(len(list((PROJECT_ROOT / "outputs" / "sql").glob("*.csv")))))
    c3.metric("Queries executed by dashboard", "0")
    st.info("Historical/documented project analysis uses the original BigQuery tables. Those user, event, subscription, and payment exports are not available locally. This dashboard displays the query inventory; it does not run SQL or claim local reproduction of the historical results.")
    topic_map = {
        "01_data_quality.sql":"Data quality and cleaning", "02_funnel.sql":"Ordered product funnel",
        "03_segmentation.sql":"Funnel segmentation", "04_retention.sql":"Exact-day retention",
        "05_monetization.sql":"Monetization", "06_ab_test_dataset.sql":"A/B dataset preparation",
        "07_product_kpis.sql":"Product KPIs", "08_funnel_segment_analysis.sql":"Funnel segment analysis",
        "09_user_activity_analysis.sql":"User activity", "10_funnel_summary.sql":"Funnel summary",
        "11_cohort_retention.sql":"Cohort retention",
    }
    st.markdown("### Topics covered")
    for start in range(0, len(sql_files), 3):
        cols = st.columns(3, gap="medium")
        for col, path in zip(cols, sql_files[start:start + 3]):
            with col, st.container(border=True):
                st.markdown(f"**{topic_map.get(path.name, path.stem)}**")
                st.caption(path.name)
    st.markdown("### Local query result availability")
    result_files = sorted((PROJECT_ROOT / "outputs" / "sql").glob("*.csv"))
    rows = [{"Result file": path.name, "Status": "Populated" if path.stat().st_size else "Empty (0 bytes)", "Size": f"{path.stat().st_size:,} bytes"} for path in result_files]
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    left, right = st.columns(2, gap="large")
    with left, st.container(border=True):
        st.markdown("**Documented project analysis**")
        st.caption("Historical full-product findings in the README and SQL work, based on source tables unavailable in this local repository.")
    with right, st.container(border=True):
        st.markdown("**Locally reproducible analysis**")
        st.caption("The supplied user-level experiment dataset and generated EDA, statistical, retention, cohort, and ML evaluation outputs.")
    st.caption("SQL files 01-11 are preserved and were not modified or executed by this app.")

def show_documented_monetization() -> None:
    _dashboard_header("Documented Monetization", "Historical project-level results from the original BigQuery analysis")
    st.info("Documented project analysis | values below are historical README results and were not recomputed from the local experiment CSV.")
    values=DOCUMENTED_RESULTS["monetization"]
    cols=st.columns(3)
    for col,key in zip(cols,("Gross Revenue","Refunds","Net Revenue")):
        col.metric(key,f"${values[key]:,.2f}")
    st.markdown(f"Revenue per payer: **${values['Revenue per Payer']:.2f}** | Paid cancellation rate: **{values['Cancellation Rate']:.2f}%**")
    st.caption("The local dataset contains no revenue or payment fields. Revenue must not be interpreted as profit.")


def show_methodology_page() -> None:
    _dashboard_header("Data &amp; Methodology", "Local dataset, analytical methods, and provenance")
    data = _load_dashboard_csv(LOCAL_DATA_PATH)
    if data.empty:
        return
    quality = _load_dashboard_csv(CLEANING_REPORT_PATH)
    with st.expander("Dataset", expanded=True):
        cols = st.columns(3)
        cols[0].metric("Assignment users", f"{len(data):,}")
        cols[1].metric("Columns", str(len(data.columns)))
        cols[2].metric("Unique user IDs", f"{data.user_id.nunique():,}")
        st.caption("Raw file: data/ab_test_dataset.csv. Raw source is preserved; a separate cleaned copy is used for analysis.")
        st.code(" | ".join(data.columns), language=None)
    with st.expander("Data Cleaning", expanded=False):
        if not quality.empty:
            st.dataframe(quality, hide_index=True, width="stretch")
        st.caption("Quality checks cover missingness, duplicate identifiers/rows, variants, binary flags, dates, and eligibility consistency.")
    with st.expander("Statistical Analysis", expanded=False):
        st.markdown("Phase 4 compares Control and Treatment proportions with two-sided pooled two-proportion z-tests and unpooled 95% confidence intervals. Alpha is 0.05 per test; no multiple-comparison adjustment is applied in the six-test summary. Retention uses eligible-user denominators, and monthly cohorts use assigned_at.")
    with st.expander("Machine Learning", expanded=False):
        st.markdown("The D30-retention target uses five binary inputs. One stratified 80/20 split (random_state=42) is shared by Logistic Regression, Decision Tree, and KNN. StandardScaler is fit inside training-only pipelines for Logistic Regression and KNN. Evaluation reports class-specific metrics, ROC-AUC, and confusion matrices.")
    st.markdown("### Data Limitations")
    st.markdown("The local source contains 11,462 experiment-assignment users, not the original event/subscription/payment exports. It has no revenue, acquisition channel, device/platform, region, demographics, or event history. No such dimensions are fabricated. Historical BigQuery findings are labeled documented project analysis; computations from local files are labeled locally reproducible analysis.")

def show_workflow_page() -> None:
    _dashboard_header("Project Workflow", "A viva-ready view of the analysis sequence")
    stages=["Data Collection","Data Cleaning","EDA","Statistical Analysis","Feature Engineering","ML Model Training","ML Evaluation","Retention & A/B Analysis","Dashboard"]
    for i,stage in enumerate(stages):
        st.markdown(f"<div class='kpi-card'><div class='kpi-value' style='font-size:1.1rem'>{i+1}. {stage}</div></div>",unsafe_allow_html=True)
        if i<len(stages)-1: st.markdown("<div style='text-align:center;color:#2A9D8F;font-size:1.35rem'>&darr;</div>",unsafe_allow_html=True)
    st.caption("Each stage uses the available local experiment data; SQL/Tableau-era full-product findings remain documented project analysis where source exports are absent.")

def main() -> None:
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">Product Analytics</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-caption">User Retention Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-caption">Mobile Subscription Analytics</div>', unsafe_allow_html=True)
        page = st.radio("Navigate", PAGES, label_visibility="collapsed")
        page = page.split(" ", 1)[1]
        st.divider()
        st.caption("Owner: Anushka Jain")

    if page == "Executive Overview":
        show_overview()
    elif page == "User Funnel":
        show_funnel_page()
    elif page == "User & Segment Analysis":
        show_user_segment_page()
    elif page == "Retention & Cohorts":
        show_retention_page()
    elif page == "A/B Experiment":
        show_ab_page()
    elif page == "ML Retention Prediction":
        show_ml_page()
    elif page == "SQL Analysis":
        show_sql_page()
    elif page == "Documented Monetization":
        show_documented_monetization()
    elif page == "Data & Methodology":
        show_methodology_page()
    elif page == "Project Workflow":
        show_workflow_page()


if __name__ == "__main__":
    main()
