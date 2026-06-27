"""Chart helpers — consistent Plotly figures for Odoo Mini HR Pro."""

import plotly.express as px
import plotly.graph_objects as go
from components.theme import COLORS

CHART_LAYOUT = dict(
    font_family='Cairo',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=10, r=10, t=44, b=10),
    title_font=dict(size=14, family='Cairo', color=COLORS['text']),
    legend=dict(font=dict(family='Cairo', size=11), orientation='h', y=-0.15),
)


def attendance_trend_chart(df, height=270):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['count'],
        mode='lines+markers',
        line=dict(color=COLORS['primary'], width=3, shape='spline'),
        marker=dict(
            size=6,
            color=COLORS['primary'],
            line=dict(color='#fff', width=2)
        ),
        fill='tozeroy',
        fillcolor="rgba(16,100,84,0.12)",
        name='الحضور',
        hovertemplate='<b>%{x}</b><br>حضور: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title='📈 اتجاه الحضور — آخر 30 يوم',
        height=height,
        xaxis=dict(showgrid=False, title=''),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLORS['border'],
            title='عدد الحاضرين',
            title_font_size=11
        ),
        **CHART_LAYOUT
    )
    return fig


def department_donut_chart(dept_df, height=270):
    colors = [
        COLORS['primary'],
        COLORS['primary_light'],
        COLORS['accent'],
        COLORS['info'],
        COLORS['warning'],
        COLORS['secondary'],
        COLORS['primary_dark'],
        COLORS['danger'],
    ]

    fig = px.pie(
        dept_df,
        names='القسم',
        values='العدد',
        title='🏢 توزيع الموظفين على الأقسام',
        color_discrete_sequence=colors,
        hole=0.5
    )

    fig.update_traces(
        textfont_family='Cairo',
        hovertemplate='<b>%{label}</b><br>%{value} موظف (%{percent})<extra></extra>'
    )

    fig.update_layout(height=height, **CHART_LAYOUT)
    return fig


def payroll_bar_chart(df, height=280):
    top = df.nlargest(8, 'صافي الراتب')

    fig = go.Figure(go.Bar(
        x=top['صافي الراتب'],
        y=top['اسم الموظف'],
        orientation='h',
        marker=dict(
            color=top['صافي الراتب'],
            colorscale=[
                [0, "rgba(16,100,84,0.2)"],
                [1, "rgba(16,100,84,1)"]
            ],
            line=dict(width=0)
        ),
        hovertemplate='<b>%{y}</b><br>%{x:,.0f} ج.م<extra></extra>',
        text=top['صافي الراتب'].apply(lambda x: f"{x:,.0f}"),
        textposition='inside',
        textfont=dict(family='Cairo', color='#fff', size=11)
    ))

    fig.update_layout(
        title='🏆 أعلى الرواتب',
        height=height,
        xaxis=dict(showgrid=True, gridcolor=COLORS['border']),
        yaxis=dict(showgrid=False, autorange='reversed'),
        **CHART_LAYOUT
    )

    return fig


def salary_distribution_chart(df, height=250):
    fig = px.histogram(
        df,
        x='صافي الراتب',
        nbins=10,
        title='📊 توزيع الرواتب',
        color_discrete_sequence=[COLORS['primary_light']]
    )

    fig.update_traces(
        marker_line_color=COLORS['primary'],
        marker_line_width=1.5,
        hovertemplate='%{x:,.0f} ج.م: %{y} موظف<extra></extra>'
    )

    fig.update_layout(
        height=height,
        xaxis_title='الراتب',
        yaxis_title='عدد الموظفين',
        **CHART_LAYOUT
    )

    return fig


def dept_cost_chart(df, height=250):
    dept_cost = df.groupby('القسم')['صافي الراتب'].sum().reset_index()
    dept_cost.columns = ['القسم', 'الإجمالي']
    dept_cost = dept_cost.sort_values('الإجمالي', ascending=False)

    fig = px.bar(
        dept_cost,
        x='القسم',
        y='الإجمالي',
        title='💰 تكلفة الرواتب بالأقسام',
        color='الإجمالي',
        color_continuous_scale=[
            [0, "rgba(16,100,84,0.2)"],
            [1, "rgba(16,100,84,1)"]
        ],
        text='الإجمالي'
    )

    fig.update_traces(
        texttemplate='%{text:,.0f}',
        textposition='outside',
        textfont=dict(family='Cairo', size=11),
        marker_line_width=0
    )

    fig.update_layout(
        height=height,
        coloraxis_showscale=False,
        xaxis_title='',
        yaxis_title='المبلغ (ج.م)',
        **CHART_LAYOUT
    )

    return fig