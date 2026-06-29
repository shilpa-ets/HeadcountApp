import os
import streamlit as st
import pandas as pd
import numpy as np


# =========================================================
# CONFIGURATION
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "Data.xlsx")

DEFAULT_STAGE_SLA_DAYS = 5


# =========================================================
# DATE PARSING
# =========================================================
def parse_mixed_excel_date(value):
    """
    Handles:
    1. Excel serial dates like 45920
    2. Normal date strings like 06/24/2026
    3. Already parsed datetime values
    """
    if pd.isna(value):
        return pd.NaT

    if isinstance(value, (int, float, np.integer, np.floating)):
        return pd.to_datetime(value, unit="D", origin="1899-12-30", errors="coerce")

    return pd.to_datetime(value, errors="coerce")


# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_session_analytics_data(file_path):
    request_df = pd.read_excel(file_path, sheet_name="Request", engine="openpyxl")
    workflow_df = pd.read_excel(file_path, sheet_name="Workflow", engine="openpyxl")
    wf_details_df = pd.read_excel(file_path, sheet_name="WFDetails", engine="openpyxl")

    return request_df, workflow_df, wf_details_df


# =========================================================
# PREPARE DATA
# =========================================================
def prepare_session_analytics_data(request_df, workflow_df, wf_details_df):
    request_df = request_df.copy()
    workflow_df = workflow_df.copy()
    wf_details_df = wf_details_df.copy()

    # -----------------------------------------------------
    # Current Workflow Level
    # Your Request sheet has both WorkFlowLevel and WorkflowLevel.
    # This combines both safely.
    # -----------------------------------------------------
    if "WorkFlowLevel" in request_df.columns and "WorkflowLevel" in request_df.columns:
        request_df["CurrentWorkflowLevel"] = request_df["WorkFlowLevel"].combine_first(
            request_df["WorkflowLevel"]
        )
    elif "WorkFlowLevel" in request_df.columns:
        request_df["CurrentWorkflowLevel"] = request_df["WorkFlowLevel"]
    elif "WorkflowLevel" in request_df.columns:
        request_df["CurrentWorkflowLevel"] = request_df["WorkflowLevel"]
    else:
        request_df["CurrentWorkflowLevel"] = np.nan

    request_df["CurrentWorkflowLevel"] = pd.to_numeric(
        request_df["CurrentWorkflowLevel"],
        errors="coerce"
    )

    # -----------------------------------------------------
    # Workflow Details Dates
    # -----------------------------------------------------
    wf_details_df["WorkflowDate"] = wf_details_df["Date"].apply(parse_mixed_excel_date)
    wf_details_df["WorkflowLevel"] = pd.to_numeric(
        wf_details_df["WorkflowLevel"],
        errors="coerce"
    )

    # -----------------------------------------------------
    # Workflow Master
    # -----------------------------------------------------
    workflow_df["WorkFlowLevel"] = pd.to_numeric(
        workflow_df["WorkFlowLevel"],
        errors="coerce"
    )

    workflow_map = workflow_df.set_index("WorkFlowLevel")[
        "WorkFlowLevel_Description"
    ].to_dict()

    # -----------------------------------------------------
    # Request workflow summary
    # -----------------------------------------------------
    wf_summary = (
        wf_details_df.dropna(subset=["WorkflowDate"])
        .groupby("REQ")
        .agg(
            FirstWorkflowDate=("WorkflowDate", "min"),
            LatestWorkflowDate=("WorkflowDate", "max"),
            MaxCompletedWorkflowLevel=("WorkflowLevel", "max"),
        )
        .reset_index()
    )

    merged_df = request_df.merge(
        wf_summary,
        left_on="Request ID",
        right_on="REQ",
        how="left"
    )

    today = pd.Timestamp.today().normalize()

    merged_df["RequestAgeDays"] = (
        today - merged_df["FirstWorkflowDate"]
    ).dt.days

    merged_df["CurrentStageAgeDays"] = (
        today - merged_df["LatestWorkflowDate"]
    ).dt.days

    merged_df["RequestAgeDays"] = merged_df["RequestAgeDays"].fillna(0)
    merged_df["CurrentStageAgeDays"] = merged_df["CurrentStageAgeDays"].fillna(0)

    merged_df["CurrentWorkflowDescription"] = merged_df["CurrentWorkflowLevel"].map(
        workflow_map
    )

    return request_df, workflow_df, wf_details_df, merged_df, workflow_map


# =========================================================
# CALCULATE METRICS
# =========================================================
def calculate_session_metrics(wf_details_df, merged_df, workflow_map):
    wf_pivot = wf_details_df.pivot_table(
        index="REQ",
        columns="WorkflowLevel",
        values="WorkflowDate",
        aggfunc="min"
    )

    # Average turnaround time: level 1 to level 7
    avg_turnaround = 0
    if 1 in wf_pivot.columns and 7 in wf_pivot.columns:
        turnaround_days = (wf_pivot[7] - wf_pivot[1]).dt.days.dropna()
        if not turnaround_days.empty:
            avg_turnaround = round(turnaround_days.mean())

    # Mean role approval time: level 1 to level 2
    mean_role_approval = 0
    if 1 in wf_pivot.columns and 2 in wf_pivot.columns:
        approval_days = (wf_pivot[2] - wf_pivot[1]).dt.days.dropna()
        if not approval_days.empty:
            mean_role_approval = round(approval_days.mean())

    # Requests waiting
    # Assuming level 8 is the final workflow stage.
    requests_waiting = merged_df[
        merged_df["CurrentWorkflowLevel"].fillna(0) < 8
    ].shape[0]

    # Requests needing attention based on SLA
    attention_needed = merged_df[
        merged_df["CurrentStageAgeDays"] > DEFAULT_STAGE_SLA_DAYS
    ].shape[0]

    # Comp Review aging
    # Using level 4 as People Process / Comp Review equivalent.
    comp_review_df = merged_df[merged_df["CurrentWorkflowLevel"] == 4]

    if not comp_review_df.empty:
        comp_review_aging = round(comp_review_df["CurrentStageAgeDays"].mean())
    else:
        comp_review_aging = 0

    # Average wait time between workflow stages
    stage_waits = []

    if workflow_map:
        max_level = int(max(workflow_map.keys()))
    else:
        max_level = 8

    for level in range(1, max_level):
        if level in wf_pivot.columns and level + 1 in wf_pivot.columns:
            days = (wf_pivot[level + 1] - wf_pivot[level]).dt.days.dropna()

            if not days.empty:
                stage_waits.append(
                    {
                        "Level": level,
                        "Stage": workflow_map.get(level, f"Level {level}"),
                        "NextStage": workflow_map.get(level + 1, f"Level {level + 1}"),
                        "AvgDays": round(days.mean(), 1),
                    }
                )

    step_wait_df = pd.DataFrame(stage_waits)

    return {
        "avg_turnaround": avg_turnaround,
        "mean_role_approval": mean_role_approval,
        "requests_waiting": requests_waiting,
        "attention_needed": attention_needed,
        "comp_review_aging": comp_review_aging,
        "step_wait_df": step_wait_df,
    }


# =========================================================
# REQUEST DISTRIBUTION
# =========================================================
def derive_status_bucket(row):
    """
    Since the current file does not have a true RequestStatus column,
    this derives status from CurrentWorkflowLevel.
    """
    level = row.get("CurrentWorkflowLevel")

    if pd.isna(level):
        return "Unknown"

    level = int(level)

    if level == 2:
        return "Ready or queued"
    elif level in [3, 5, 6, 7, 8]:
        return "In review"
    elif level == 4:
        return "Needs revision or comp"
    else:
        return "Ready or queued"


def calculate_request_distribution(merged_df):
    df = merged_df.copy()

    if "RequestStatus" in df.columns:
        df["StatusBucket"] = df["RequestStatus"].fillna("Unknown")
    else:
        df["StatusBucket"] = df.apply(derive_status_bucket, axis=1)

    dist = (
        df["StatusBucket"]
        .value_counts()
        .reset_index()
    )

    dist.columns = ["Status", "Count"]

    desired_order = [
        "Ready or queued",
        "In review",
        "Needs revision or comp",
        "Returned",
        "Unknown"
    ]

    for status in desired_order:
        if status not in dist["Status"].values:
            dist = pd.concat(
                [
                    dist,
                    pd.DataFrame({"Status": [status], "Count": [0]})
                ],
                ignore_index=True
            )

    dist["SortOrder"] = dist["Status"].apply(
        lambda x: desired_order.index(x) if x in desired_order else 999
    )

    dist = dist.sort_values("SortOrder").drop(columns=["SortOrder"])

    total = dist["Count"].sum()
    dist["Percent"] = np.where(
        total > 0,
        round((dist["Count"] / total) * 100, 0).astype(int),
        0
    )

    dist["LegendLabel"] = dist["Status"] + " · " + dist["Percent"].astype(str) + "%"

    return dist


# =========================================================
# WEEKLY THROUGHPUT
# =========================================================
def calculate_weekly_throughput(wf_details_df):
    df = wf_details_df.dropna(subset=["WorkflowDate"]).copy()

    if df.empty:
        return pd.DataFrame(columns=["WeekStart", "WeekLabel", "Count"])

    df["WeekStart"] = df["WorkflowDate"].dt.to_period("W").apply(
        lambda p: p.start_time
    )

    weekly = (
        df.groupby("WeekStart")
        .size()
        .reset_index(name="Count")
        .sort_values("WeekStart")
        .tail(6)
    )

    weekly["WeekLabel"] = [f"W{i + 1}" for i in range(len(weekly))]

    colors = ["#6EA04D", "#0E83A5", "#0E83A5", "#C87922", "#0E83A5", "#75A857"]
    weekly["Color"] = colors[:len(weekly)]

    return weekly[["WeekStart", "WeekLabel", "Count", "Color"]]


# =========================================================
# PAGE STYLING - SAFE CSS ONLY
# =========================================================
def apply_page_style():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #F7FAFC;
        }

        .block-container {
            padding-top: 1.2rem;
            padding-left: 1.2rem;
            padding-right: 1.2rem;
            max-width: 100%;
        }

        div[data-testid="stMetric"] {
            background-color: white;
            border: 1px solid #DDE6EF;
            padding: 22px 24px;
            border-radius: 18px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
            min-height: 130px;
        }

        div[data-testid="stMetricLabel"] {
            color: #526E8D;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        div[data-testid="stMetricValue"] {
            color: #062B4F;
            font-size: 44px;
            font-weight: 700;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white;
            border-radius: 18px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
        }

        h2, h3 {
            font-family: Georgia, 'Times New Roman', serif !important;
            color: #062B4F !important;
        }

        .section-subtitle {
            color: #526E8D;
            font-size: 16px;
            margin-top: -8px;
            margin-bottom: 22px;
        }

        .signal-card {
            background: white;
            border: 1px solid #DDE6EF;
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 16px;
        }

        .signal-title {
            color: #062B4F;
            font-weight: 800;
            font-size: 17px;
            margin-bottom: 8px;
        }

        .signal-body {
            color: #062B4F;
            font-size: 16px;
            line-height: 1.45;
        }

        .attention-pill {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: #FFF1E6;
            color: #A85400;
            font-weight: 700;
            font-size: 14px;
            white-space: nowrap;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# ALTAIR HELPER
# =========================================================
def get_altair():
    """
    Imports Altair only when needed.
    This prevents the full app from failing during startup if Altair is not available.
    """
    try:
        import altair as alt
        return alt
    except Exception:
        return None


# =========================================================
# RENDER HELPERS - SAFE CHARTS ONLY
# =========================================================
def render_step_wait_time(step_wait_df):
    """
    Screenshot-style horizontal bars.
    Uses Altair, not custom HTML, so it will not show raw HTML text.
    Bar names are fixed as requested.
    """
    if step_wait_df.empty:
        st.info("No workflow transition data available.")
        return

    alt = get_altair()

    display_names = [
        "JD Library Review",
        "BU HR Guidance",
        "Comp Review",
        "SLT Review",
        "TA Handoff"
    ]

    chart_df = step_wait_df.head(5).copy()
    chart_df["DisplayStage"] = display_names[:len(chart_df)]

    colors = ["#5D8F3F", "#B56516", "#C87922", "#0E83A5", "#75A857"]
    chart_df["Color"] = colors[:len(chart_df)]
    chart_df["StageOrder"] = range(len(chart_df))

    if alt is None:
        max_days = chart_df["AvgDays"].max()

        for _, row in chart_df.iterrows():
            label_col, progress_col, value_col = st.columns([2.5, 5, 0.8])

            with label_col:
                st.write(f"**{row['DisplayStage']}**")

            with progress_col:
                progress_value = 0 if max_days == 0 else float(row["AvgDays"] / max_days)
                st.progress(progress_value)

            with value_col:
                st.write(f"{row['AvgDays']}d")

        return

    base = alt.Chart(chart_df).encode(
        y=alt.Y(
            "DisplayStage:N",
            sort=display_names,
            title=None,
            axis=alt.Axis(
                labelColor="#062B4F",
                labelFontSize=14,
                labelFontWeight="bold",
                ticks=False,
                domain=False
            )
        )
    )

    background = base.mark_bar(
        cornerRadius=10,
        color="#EAF1F7",
        size=20
    ).encode(
        x=alt.X(
            "MaxValue:Q",
            title=None,
            axis=None,
            scale=alt.Scale(domain=[0, max(chart_df["AvgDays"].max(), 1)])
        )
    ).transform_calculate(
        MaxValue=str(max(chart_df["AvgDays"].max(), 1))
    )

    bars = base.mark_bar(
        cornerRadius=10,
        size=20
    ).encode(
        x=alt.X(
            "AvgDays:Q",
            title=None,
            axis=None,
            scale=alt.Scale(domain=[0, max(chart_df["AvgDays"].max(), 1)])
        ),
        color=alt.Color("Color:N", scale=None, legend=None),
        tooltip=[
            alt.Tooltip("DisplayStage:N", title="Stage"),
            alt.Tooltip("AvgDays:Q", title="Average Days")
        ]
    )

    text = base.mark_text(
        align="left",
        baseline="middle",
        dx=8,
        color="#526E8D",
        fontSize=14
    ).encode(
        x=alt.X("AvgDays:Q", title=None, axis=None),
        text=alt.Text("AvgDays:Q", format=".1f")
    ).transform_calculate(
        AvgDaysLabel="datum.AvgDays + 'd'"
    )

    day_text = base.mark_text(
        align="left",
        baseline="middle",
        dx=8,
        color="#526E8D",
        fontSize=14
    ).encode(
        x=alt.X(
            "LabelPosition:Q",
            title=None,
            axis=None,
            scale=alt.Scale(domain=[0, max(chart_df["AvgDays"].max(), 1)])
        ),
        text=alt.Text("AvgDaysLabel:N")
    ).transform_calculate(
        LabelPosition=str(max(chart_df["AvgDays"].max(), 1) * 1.03),
        AvgDaysLabel="datum.AvgDays + 'd'"
    )

    chart = (
        background + bars + day_text
    ).properties(
        height=240
    ).configure_view(
        strokeWidth=0
    )

    st.altair_chart(chart, use_container_width=True)


def render_request_distribution(distribution_df):
    """
    Donut chart like the screenshot.
    Uses Altair, not HTML.
    """
    if distribution_df.empty:
        st.info("No request distribution data available.")
        return

    alt = get_altair()

    plot_df = distribution_df[distribution_df["Count"] > 0].copy()

    if plot_df.empty:
        st.info("No request distribution data available.")
        return

    if alt is None:
        chart_df = plot_df[["Status", "Count"]].copy().set_index("Status")
        st.bar_chart(chart_df)
        st.dataframe(
            distribution_df[["Status", "Count", "Percent"]],
            use_container_width=True,
            hide_index=True
        )
        return

    color_domain = [
        "Ready or queued",
        "In review",
        "Needs revision or comp",
        "Returned",
        "Unknown"
    ]

    color_range = [
        "#5D8F3F",
        "#0E83A5",
        "#B56516",
        "#A8322B",
        "#999999"
    ]

    donut = (
        alt.Chart(plot_df)
        .mark_arc(innerRadius=70, outerRadius=120)
        .encode(
            theta=alt.Theta("Count:Q"),
            color=alt.Color(
                "Status:N",
                scale=alt.Scale(domain=color_domain, range=color_range),
                legend=None
            ),
            tooltip=[
                alt.Tooltip("Status:N", title="Status"),
                alt.Tooltip("Count:Q", title="Count"),
                alt.Tooltip("Percent:Q", title="Percent")
            ]
        )
        .properties(width=270, height=270)
    )

    legend = (
        alt.Chart(plot_df)
        .mark_text(
            align="left",
            baseline="middle",
            fontSize=15,
            color="#062B4F"
        )
        .encode(
            y=alt.Y(
                "Status:N",
                sort=color_domain,
                axis=None
            ),
            text=alt.Text("LegendLabel:N")
        )
        .properties(width=260, height=210)
    )

    legend_points = (
        alt.Chart(plot_df)
        .mark_point(
            filled=True,
            size=130
        )
        .encode(
            y=alt.Y(
                "Status:N",
                sort=color_domain,
                axis=None
            ),
            color=alt.Color(
                "Status:N",
                scale=alt.Scale(domain=color_domain, range=color_range),
                legend=None
            )
        )
        .properties(width=20, height=210)
    )

    combined = alt.hconcat(
        donut,
        alt.hconcat(legend_points, legend, spacing=6),
        spacing=20
    ).configure_view(
        strokeWidth=0
    )

    st.altair_chart(combined, use_container_width=True)


def render_weekly_throughput(weekly_df):
    """
    Screenshot-style weekly bars.
    Uses Altair, not custom HTML.
    """
    if weekly_df.empty:
        st.info("No weekly throughput data available.")
        return

    alt = get_altair()

    if alt is None:
        chart_df = weekly_df[["WeekLabel", "Count"]].copy().set_index("WeekLabel")
        st.bar_chart(chart_df)
        st.dataframe(
            weekly_df[["WeekLabel", "Count"]],
            use_container_width=True,
            hide_index=True
        )
        return

    chart = (
        alt.Chart(weekly_df)
        .mark_bar(
            cornerRadiusTopLeft=10,
            cornerRadiusTopRight=10
        )
        .encode(
            x=alt.X(
                "WeekLabel:N",
                title=None,
                sort=None,
                axis=alt.Axis(
                    labelColor="#526E8D",
                    labelFontSize=14,
                    domainColor="#DDE6EF",
                    tickSize=0
                )
            ),
            y=alt.Y(
                "Count:Q",
                title=None,
                axis=None
            ),
            color=alt.Color("Color:N", scale=None, legend=None),
            tooltip=[
                alt.Tooltip("WeekLabel:N", title="Week"),
                alt.Tooltip("Count:Q", title="Movements")
            ]
        )
        .properties(height=265)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(chart, use_container_width=True)


def render_process_signals(metrics, step_wait_df, distribution_df):
    signals = []

    if not step_wait_df.empty:
        longest = step_wait_df.head(5).copy()
        display_names = [
            "JD Library Review",
            "BU HR Guidance",
            "Comp Review",
            "SLT Review",
            "TA Handoff"
        ]
        longest["DisplayStage"] = display_names[:len(longest)]
        longest_row = longest.sort_values("AvgDays", ascending=False).iloc[0]

        signals.append(
            {
                "title": f"Longest wait is {longest_row['DisplayStage']}",
                "body": f"Requests spend the most time before moving from {longest_row['DisplayStage']} to the next stage."
            }
        )

    needs_revision_pct = 0
    needs_revision_row = distribution_df[
        distribution_df["Status"] == "Needs revision or comp"
    ]

    if not needs_revision_row.empty:
        needs_revision_pct = int(needs_revision_row["Percent"].iloc[0])

    signals.append(
        {
            "title": "Comp Review exception path",
            "body": f"{needs_revision_pct}% of requests are classified as Needs revision or comp based on current workflow level."
        }
    )

    signals.append(
        {
            "title": "Attention needed on aging requests",
            "body": f"{metrics['attention_needed']} requests have been waiting longer than the configured SLA of {DEFAULT_STAGE_SLA_DAYS} days."
        }
    )

    signals.append(
        {
            "title": "TA handoff tracking",
            "body": "Add CompletionDate or TAHandoffDate to measure final handoff stability more accurately."
        }
    )

    for signal in signals:
        st.markdown(
            f"""
            <div class="signal-card">
                <div class="signal-title">{signal["title"]}</div>
                <div class="signal-body">{signal["body"]}</div>
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# MAIN FUNCTION CALLED FROM app2.py
# =========================================================
def show():
    apply_page_style()

    try:
        request_df, workflow_df, wf_details_df = load_session_analytics_data(DATA_FILE)

        request_df, workflow_df, wf_details_df, merged_df, workflow_map = prepare_session_analytics_data(
            request_df,
            workflow_df,
            wf_details_df
        )

        metrics = calculate_session_metrics(
            wf_details_df,
            merged_df,
            workflow_map
        )

        distribution_df = calculate_request_distribution(merged_df)
        weekly_df = calculate_weekly_throughput(wf_details_df)

    except PermissionError:
        st.error(
            "Permission denied while reading Data.xlsx. "
            "Please close Data.xlsx if it is open in Excel, then stop and rerun Streamlit."
        )
        return

    except FileNotFoundError:
        st.error(
            "Data.xlsx was not found. Please keep Data.xlsx in the same folder as app2.py and session_analytics.py."
        )
        return

    except Exception as e:
        st.error("Unable to load or process Data.xlsx for Session Analytics.")
        st.exception(e)
        return

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------
    st.caption("PROCESS HEALTH")
    st.title("Session Analytics")
    st.write(
        "Operational view of headcount flow health, turnaround time, approval aging, "
        "and where requests wait the longest."
    )

    st.divider()

    # -----------------------------------------------------
    # KPI Cards
    # -----------------------------------------------------
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric(
            label="AVG TURNAROUND TIME",
            value=f"{metrics['avg_turnaround']}d"
        )
        st.caption("Submit to TA handoff")

    with kpi2:
        st.metric(
            label="MEAN ROLE APPROVAL TIME",
            value=f"{metrics['mean_role_approval']}d"
        )
        st.caption("Submit to SLT decision")

    with kpi3:
        st.metric(
            label="REQUESTS WAITING",
            value=f"{metrics['requests_waiting']}"
        )

        if metrics["attention_needed"] > 0:
            st.warning(f"{metrics['attention_needed']} need action")
        else:
            st.success("No aging requests")

    with kpi4:
        st.metric(
            label="COMP REVIEW AGING",
            value=f"{metrics['comp_review_aging']}d"
        )
        st.caption("Average open age")

    st.write("")

    # -----------------------------------------------------
    # Row 2
    # -----------------------------------------------------
    left_col, right_col = st.columns(2)

    with left_col:
        with st.container(border=True):
            st.subheader("Step Wait Time")
            st.markdown(
                '<div class="section-subtitle">Average days spent in each stage</div>',
                unsafe_allow_html=True
            )
            render_step_wait_time(metrics["step_wait_df"])

    with right_col:
        with st.container(border=True):
            st.subheader("Request Distribution")
            st.markdown(
                '<div class="section-subtitle">Current open queue by status</div>',
                unsafe_allow_html=True
            )
            render_request_distribution(distribution_df)

    st.write("")

    # -----------------------------------------------------
    # Row 3
    # -----------------------------------------------------
    bottom_left_col, bottom_right_col = st.columns(2)

    with bottom_left_col:
        with st.container(border=True):
            st.subheader("Weekly Throughput")
            st.markdown(
                '<div class="section-subtitle">Requests moved to next stage</div>',
                unsafe_allow_html=True
            )
            render_weekly_throughput(weekly_df)

    with bottom_right_col:
        with st.container(border=True):
            signal_title_col, signal_badge_col = st.columns([4, 1])

            with signal_title_col:
                st.subheader("Process Signals")

            with signal_badge_col:
                st.markdown(
                    '<div class="attention-pill">Attention needed</div>',
                    unsafe_allow_html=True
                )

            st.divider()
            render_process_signals(metrics, metrics["step_wait_df"], distribution_df)

    # -----------------------------------------------------
    # Debug Section
    # -----------------------------------------------------
    with st.expander("View calculated data"):
        st.subheader("KPI Inputs")
        st.write(
            {
                "Average Turnaround Days": metrics["avg_turnaround"],
                "Mean Role Approval Days": metrics["mean_role_approval"],
                "Requests Waiting": metrics["requests_waiting"],
                "Attention Needed": metrics["attention_needed"],
                "Comp Review Aging": metrics["comp_review_aging"],
                "Stage SLA Days": DEFAULT_STAGE_SLA_DAYS,
            }
        )

        st.subheader("Step Wait Time")
        st.dataframe(metrics["step_wait_df"], use_container_width=True)

        st.subheader("Request Distribution")
        st.dataframe(distribution_df, use_container_width=True)

        st.subheader("Weekly Throughput")
        st.dataframe(weekly_df, use_container_width=True)
