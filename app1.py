import streamlit as st
import akshare as ak
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="中国宏观经济指标看板", page_icon="📊", layout="wide")

# ============ 工具函数 ============
def parse_chinese_date(date_str):
    """解析'2026年08月份'格式的日期"""
    try:
        date_str = str(date_str).replace("年", "-").replace("月份", "").replace("月", "")
        return pd.to_datetime(date_str, format="%Y-%m")
    except:
        return pd.NaT

def parse_quarter(quarter_str):
    """解析'2026年第1-2季度'格式的日期"""
    try:
        quarter_str = str(quarter_str)
        year = quarter_str.split("年")[0]
        if "1-4" in quarter_str:
            return pd.to_datetime(f"{year}-12-01")
        elif "1-3" in quarter_str:
            return pd.to_datetime(f"{year}-09-01")
        elif "1-2" in quarter_str:
            return pd.to_datetime(f"{year}-06-01")
        elif "第1季度" in quarter_str:
            return pd.to_datetime(f"{year}-03-01")
        else:
            return pd.NaT
    except:
        return pd.NaT

def safe_metric(col, label, value, prev=None, suffix=""):
    """安全显示指标卡片"""
    if pd.isna(value):
        col.metric(label, "暂无数据")
    elif prev is not None and not pd.isna(prev):
        delta = value - prev
        col.metric(label, f"{value}{suffix}", delta=f"{delta:.1f}{suffix}")
    else:
        col.metric(label, f"{value}{suffix}")

# ============ 数据加载 ============
@st.cache_data(ttl=3600)
def load_cpi():
    df = ak.macro_china_cpi()
    df["日期"] = df["月份"].apply(parse_chinese_date)
    df["同比"] = pd.to_numeric(df["全国-同比增长"], errors="coerce")
    df = df.dropna(subset=["日期", "同比"])
    df = df.sort_values("日期").reset_index(drop=True)
    return df

@st.cache_data(ttl=3600)
def load_ppi():
    df = ak.macro_china_ppi()
    df["日期"] = df["月份"].apply(parse_chinese_date)
    df["同比"] = pd.to_numeric(df["当月同比增长"], errors="coerce")
    df = df.dropna(subset=["日期", "同比"])
    df = df.sort_values("日期").reset_index(drop=True)
    return df

@st.cache_data(ttl=3600)
def load_pmi():
    df = ak.macro_china_pmi()
    df["日期"] = df["月份"].apply(parse_chinese_date)
    df["制造业PMI"] = pd.to_numeric(df["制造业-指数"], errors="coerce")
    df["非制造业PMI"] = pd.to_numeric(df["非制造业-指数"], errors="coerce")
    df = df.dropna(subset=["日期", "制造业PMI"])
    df = df.sort_values("日期").reset_index(drop=True)
    return df

@st.cache_data(ttl=3600)
def load_gdp():
    df = ak.macro_china_gdp()
    df["日期"] = df["季度"].apply(parse_quarter)
    df["GDP同比"] = pd.to_numeric(df["国内生产总值-同比增长"], errors="coerce")
    df = df.dropna(subset=["日期", "GDP同比"])
    df = df.sort_values("日期").reset_index(drop=True)
    return df

@st.cache_data(ttl=3600)
def load_m2():
    df = ak.macro_china_supply_of_money()
    df["日期"] = pd.to_datetime(df["统计时间"], format="%Y.%m", errors="coerce")
    df["M2同比"] = pd.to_numeric(df["货币和准货币（广义货币M2）同比增长"], errors="coerce")
    df = df.dropna(subset=["日期", "M2同比"])
    df = df.sort_values("日期").reset_index(drop=True)
    return df

@st.cache_data(ttl=3600)
def load_trade():
    df = ak.macro_china_hgjck()
    df["日期"] = df["月份"].apply(parse_chinese_date)
    df["出口额"] = pd.to_numeric(df["当月出口额-金额"], errors="coerce") / 1e8  # 转亿美元
    df["进口额"] = pd.to_numeric(df["当月进口额-金额"], errors="coerce") / 1e8
    df["贸易差额"] = df["出口额"] - df["进口额"]
    df["出口同比"] = pd.to_numeric(df["当月出口额-同比增长"], errors="coerce")
    df = df.dropna(subset=["日期", "贸易差额"])
    df = df.sort_values("日期").reset_index(drop=True)
    return df

@st.cache_data(ttl=3600)
def load_lpr():
    df = ak.macro_china_lpr()
    df["日期"] = pd.to_datetime(df["TRADE_DATE"], errors="coerce")
    df["LPR1Y"] = pd.to_numeric(df["LPR1Y"], errors="coerce")
    df["LPR5Y"] = pd.to_numeric(df["LPR5Y"], errors="coerce")
    df = df.dropna(subset=["日期"])
    df = df.sort_values("日期").reset_index(drop=True)
    return df

@st.cache_data(ttl=3600)
def load_shrzgm():
    df = ak.macro_china_shrzgm()
    df["月份"] = pd.to_datetime(df["月份"], format="%Y%m")
    for col in df.columns:
        if col != "月份":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["社会融资规模增量"])
    df = df.sort_values("月份").reset_index(drop=True)
    return df

# ============ 侧边栏 ============
st.sidebar.title("📊 宏观经济看板")
page = st.sidebar.radio("导航", ["📈 总览仪表盘", "🔍 指标详情分析"])

# ============ 总览仪表盘 ============
if page == "📈 总览仪表盘":
    st.title("中国宏观经济指标总览")
    st.caption(f"数据来源：akshare | 更新时间：{datetime.now().strftime('%Y-%m-%d')}")
    st.divider()

    # 加载所有数据
    cpi = load_cpi()
    ppi = load_ppi()
    pmi = load_pmi()
    gdp = load_gdp()
    m2 = load_m2()
    trade = load_trade()
    lpr = load_lpr()
    shrz = load_shrzgm()

    # ---- 关键数值卡片 ----
    st.subheader("最新关键指标")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        v = cpi.iloc[-1]
        prev = cpi.iloc[-2] if len(cpi) > 1 else None
        safe_metric(col1, "CPI 同比", v["同比"], prev["同比"] if prev is not None else None, "%")
    with col2:
        v = ppi.iloc[-1]
        prev = ppi.iloc[-2] if len(ppi) > 1 else None
        safe_metric(col2, "PPI 同比", v["同比"], prev["同比"] if prev is not None else None, "%")
    with col3:
        v = pmi.iloc[-1]
        prev = pmi.iloc[-2] if len(pmi) > 1 else None
        safe_metric(col3, "制造业PMI", v["制造业PMI"], prev["制造业PMI"] if prev is not None else None)
    with col4:
        v = gdp.iloc[-1]
        safe_metric(col4, "GDP 同比", v["GDP同比"], suffix="%")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        v = m2.iloc[-1]
        prev = m2.iloc[-2] if len(m2) > 1 else None
        safe_metric(col5, "M2 同比", v["M2同比"], prev["M2同比"] if prev is not None else None, "%")
    with col6:
        v = trade.iloc[-1]
        prev = trade.iloc[-2] if len(trade) > 1 else None
        safe_metric(col6, "贸易差额", round(v["贸易差额"], 1), round(prev["贸易差额"], 1) if prev is not None else None, "亿美元")
    with col7:
        v = lpr.iloc[-1]
        safe_metric(col7, "LPR 1年", v["LPR1Y"], suffix="%")
    with col8:
        v = shrz.iloc[-1]
        safe_metric(col8, "社融增量", v["社会融资规模增量"], suffix="亿元")

    st.divider()

    # ---- 走势对比图 ----
    st.subheader("物价指标走势（CPI vs PPI 同比）")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=cpi.tail(60)["日期"], y=cpi.tail(60)["同比"], name="CPI同比", line=dict(color="#e74c3c", width=2)))
    fig1.add_trace(go.Scatter(x=ppi.tail(60)["日期"], y=ppi.tail(60)["同比"], name="PPI同比", line=dict(color="#3498db", width=2)))
    fig1.update_layout(template="plotly_white", height=400, legend=dict(x=0, y=1), xaxis_title="日期", yaxis_title="同比(%)")
    st.plotly_chart(fig1, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("PMI 走势（制造业 vs 非制造业）")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=pmi.tail(60)["日期"], y=pmi.tail(60)["制造业PMI"], name="制造业PMI", line=dict(color="#2ecc71", width=2)))
        fig2.add_trace(go.Scatter(x=pmi.tail(60)["日期"], y=pmi.tail(60)["非制造业PMI"], name="非制造业PMI", line=dict(color="#f39c12", width=2)))
        fig2.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="荣枯线 50")
        fig2.update_layout(template="plotly_white", height=350, xaxis_title="日期", yaxis_title="PMI")
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.subheader("GDP 同比增速")
        gdp_recent = gdp[~gdp["季度"].str.contains("1-4季度")].tail(20)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=gdp_recent["日期"], y=gdp_recent["GDP同比"], marker_color="#f39c12", text=gdp_recent["GDP同比"], textposition="outside"))
        fig3.update_layout(template="plotly_white", height=350, xaxis_title="日期", yaxis_title="GDP同比(%)", showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("M2 货币供应同比")
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=m2.tail(60)["日期"], y=m2.tail(60)["M2同比"], mode="lines", fill="tozeroy", line=dict(color="#9b59b6", width=2)))
        fig4.update_layout(template="plotly_white", height=350, xaxis_title="日期", yaxis_title="M2同比(%)", showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

    with col_d:
        st.subheader("进出口走势")
        trade_recent = trade.tail(60)
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(x=trade_recent["日期"], y=trade_recent["出口额"], name="出口", line=dict(color="#2ecc71", width=2)))
        fig5.add_trace(go.Scatter(x=trade_recent["日期"], y=trade_recent["进口额"], name="进口", line=dict(color="#e74c3c", width=2)))
        fig5.update_layout(template="plotly_white", height=350, xaxis_title="日期", yaxis_title="亿美元")
        st.plotly_chart(fig5, use_container_width=True)

    col_e, col_f = st.columns(2)
    with col_e:
        st.subheader("贸易差额")
        trade_recent = trade.tail(60)
        colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in trade_recent["贸易差额"]]
        fig6 = go.Figure()
        fig6.add_trace(go.Bar(x=trade_recent["日期"], y=trade_recent["贸易差额"], marker_color=colors))
        fig6.update_layout(template="plotly_white", height=350, xaxis_title="日期", yaxis_title="亿美元", showlegend=False)
        st.plotly_chart(fig6, use_container_width=True)

    with col_f:
        st.subheader("LPR 利率走势")
        fig7 = go.Figure()
        fig7.add_trace(go.Scatter(x=lpr.tail(60)["日期"], y=lpr.tail(60)["LPR1Y"], name="1年期LPR", line=dict(color="#3498db", width=2)))
        fig7.add_trace(go.Scatter(x=lpr.tail(60)["日期"], y=lpr.tail(60)["LPR5Y"], name="5年期LPR", line=dict(color="#e67e22", width=2)))
        fig7.update_layout(template="plotly_white", height=350, xaxis_title="日期", yaxis_title="利率(%)")
        st.plotly_chart(fig7, use_container_width=True)

    st.subheader("社会融资规模增量")
    fig8 = go.Figure()
    fig8.add_trace(go.Bar(x=shrz.tail(36)["月份"], y=shrz.tail(36)["社会融资规模增量"], marker_color="#3498db"))
    fig8.update_layout(template="plotly_white", height=400, xaxis_title="月份", yaxis_title="亿元", showlegend=False)
    st.plotly_chart(fig8, use_container_width=True)

# ============ 指标详情页 ============
elif page == "🔍 指标详情分析":
    st.title("指标详情分析")

    indicator = st.selectbox("选择指标", [
        "CPI 同比", "PPI 同比", "PMI 制造业", "GDP 同比",
        "M2 同比", "进出口", "LPR 利率", "社会融资规模"
    ])

    if indicator == "CPI 同比":
        df = load_cpi()
        df_show = df.tail(120)
        min_date, max_date = df_show["日期"].min().date(), df_show["日期"].max().date()
        date_range = st.slider("选择时间范围", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="YYYY-MM-DD")
        df_filtered = df_show[(df_show["日期"].dt.date >= date_range[0]) & (df_show["日期"].dt.date <= date_range[1])]

        st.subheader("📊 CPI 同比走势")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_filtered["日期"], y=df_filtered["同比"], mode="lines+markers", name="CPI同比", line=dict(color="#e74c3c", width=2)))
        fig.update_layout(template="plotly_white", height=500, xaxis_title="日期", yaxis_title="CPI同比(%)")
        st.plotly_chart(fig, use_container_width=True)

        latest = df.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新CPI同比", f"{latest['同比']}%")
        col2.metric("最高值", f"{df['同比'].max()}%")
        col3.metric("最低值", f"{df['同比'].min()}%")
        col4.metric("均值", f"{df['同比'].mean():.2f}%")

    elif indicator == "PPI 同比":
        df = load_ppi()
        df_show = df.tail(120)
        min_date, max_date = df_show["日期"].min().date(), df_show["日期"].max().date()
        date_range = st.slider("选择时间范围", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="YYYY-MM-DD")
        df_filtered = df_show[(df_show["日期"].dt.date >= date_range[0]) & (df_show["日期"].dt.date <= date_range[1])]

        st.subheader("📊 PPI 同比走势")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_filtered["日期"], y=df_filtered["同比"], mode="lines+markers", name="PPI同比", line=dict(color="#3498db", width=2)))
        fig.update_layout(template="plotly_white", height=500, xaxis_title="日期", yaxis_title="PPI同比(%)")
        st.plotly_chart(fig, use_container_width=True)

        latest = df.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新PPI同比", f"{latest['同比']}%")
        col2.metric("最高值", f"{df['同比'].max()}%")
        col3.metric("最低值", f"{df['同比'].min()}%")
        col4.metric("均值", f"{df['同比'].mean():.2f}%")

    elif indicator == "PMI 制造业":
        df = load_pmi()
        df_show = df.tail(120)
        min_date, max_date = df_show["日期"].min().date(), df_show["日期"].max().date()
        date_range = st.slider("选择时间范围", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="YYYY-MM-DD")
        df_filtered = df_show[(df_show["日期"].dt.date >= date_range[0]) & (df_show["日期"].dt.date <= date_range[1])]

        st.subheader("📊 PMI 走势")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_filtered["日期"], y=df_filtered["制造业PMI"], mode="lines+markers", name="制造业PMI", line=dict(color="#2ecc71", width=2)))
        fig.add_trace(go.Scatter(x=df_filtered["日期"], y=df_filtered["非制造业PMI"], mode="lines+markers", name="非制造业PMI", line=dict(color="#f39c12", width=2)))
        fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="荣枯线 50")
        fig.update_layout(template="plotly_white", height=500, xaxis_title="日期", yaxis_title="PMI")
        st.plotly_chart(fig, use_container_width=True)

        latest = df.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新制造业PMI", f"{latest['制造业PMI']}")
        col2.metric("最新非制造业PMI", f"{latest['非制造业PMI']}")
        col3.metric("制造业最高", f"{df['制造业PMI'].max()}")
        col4.metric("制造业最低", f"{df['制造业PMI'].min()}")

    elif indicator == "GDP 同比":
        df = load_gdp()
        df_show = df[~df["季度"].str.contains("1-4季度")]
        min_date, max_date = df_show["日期"].min().date(), df_show["日期"].max().date()
        date_range = st.slider("选择时间范围", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="YYYY-MM-DD")
        df_filtered = df_show[(df_show["日期"].dt.date >= date_range[0]) & (df_show["日期"].dt.date <= date_range[1])]

        st.subheader("📊 GDP 同比增速")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_filtered["日期"], y=df_filtered["GDP同比"], marker_color="#f39c12", text=df_filtered["GDP同比"], textposition="outside"))
        fig.update_layout(template="plotly_white", height=500, xaxis_title="日期", yaxis_title="GDP同比(%)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        latest = df.iloc[0]  # 最新在第一行
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新GDP同比", f"{latest['GDP同比']}%")
        col2.metric("最高值", f"{df_show['GDP同比'].max()}%")
        col3.metric("最低值", f"{df_show['GDP同比'].min()}%")
        col4.metric("均值", f"{df_show['GDP同比'].mean():.2f}%")

    elif indicator == "M2 同比":
        df = load_m2()
        df_show = df.tail(120)
        min_date, max_date = df_show["日期"].min().date(), df_show["日期"].max().date()
        date_range = st.slider("选择时间范围", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="YYYY-MM-DD")
        df_filtered = df_show[(df_show["日期"].dt.date >= date_range[0]) & (df_show["日期"].dt.date <= date_range[1])]

        st.subheader("📊 M2 同比增速")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_filtered["日期"], y=df_filtered["M2同比"], mode="lines", fill="tozeroy", line=dict(color="#9b59b6", width=2)))
        fig.update_layout(template="plotly_white", height=500, xaxis_title="日期", yaxis_title="M2同比(%)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        latest = df.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新M2同比", f"{latest['M2同比']}%")
        col2.metric("最高值", f"{df['M2同比'].max()}%")
        col3.metric("最低值", f"{df['M2同比'].min()}%")
        col4.metric("均值", f"{df['M2同比'].mean():.2f}%")

    elif indicator == "进出口":
        df = load_trade()
        df_show = df.tail(120)
        min_date, max_date = df_show["日期"].min().date(), df_show["日期"].max().date()
        date_range = st.slider("选择时间范围", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="YYYY-MM-DD")
        df_filtered = df_show[(df_show["日期"].dt.date >= date_range[0]) & (df_show["日期"].dt.date <= date_range[1])]

        st.subheader("📊 进出口走势")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_filtered["日期"], y=df_filtered["出口额"], name="出口", line=dict(color="#2ecc71", width=2)))
        fig.add_trace(go.Scatter(x=df_filtered["日期"], y=df_filtered["进口额"], name="进口", line=dict(color="#e74c3c", width=2)))
        fig.add_trace(go.Scatter(x=df_filtered["日期"], y=df_filtered["贸易差额"], name="贸易差额", line=dict(color="#3498db", width=2, dash="dash")))
        fig.update_layout(template="plotly_white", height=500, xaxis_title="日期", yaxis_title="亿美元")
        st.plotly_chart(fig, use_container_width=True)

        latest = df.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新出口额", f"{latest['出口额']:.1f}亿美元")
        col2.metric("最新进口额", f"{latest['进口额']:.1f}亿美元")
        col3.metric("最新贸易差额", f"{latest['贸易差额']:.1f}亿美元")
        col4.metric("最新出口同比", f"{latest['出口同比']}%")

    elif indicator == "LPR 利率":
        df = load_lpr()
        df_show = df.tail(120)
        min_date, max_date = df_show["日期"].min().date(), df_show["日期"].max().date()
        date_range = st.slider("选择时间范围", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="YYYY-MM-DD")
        df_filtered = df_show[(df_show["日期"].dt.date >= date_range[0]) & (df_show["日期"].dt.date <= date_range[1])]

        st.subheader("📊 LPR 利率走势")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_filtered["日期"], y=df_filtered["LPR1Y"], mode="lines+markers", name="1年期LPR", line=dict(color="#3498db", width=2)))
        fig.add_trace(go.Scatter(x=df_filtered["日期"], y=df_filtered["LPR5Y"], mode="lines+markers", name="5年期LPR", line=dict(color="#e67e22", width=2)))
        fig.update_layout(template="plotly_white", height=500, xaxis_title="日期", yaxis_title="利率(%)")
        st.plotly_chart(fig, use_container_width=True)

        latest = df.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新1年LPR", f"{latest['LPR1Y']}%")
        col2.metric("最新5年LPR", f"{latest['LPR5Y']}%")
        col3.metric("1年LPR最低", f"{df['LPR1Y'].min()}%")
        col4.metric("5年LPR最低", f"{df['LPR5Y'].min()}%")

    elif indicator == "社会融资规模":
        df = load_shrzgm()
        df_show = df.tail(60)
        min_date, max_date = df_show["月份"].min().date(), df_show["月份"].max().date()
        date_range = st.slider("选择时间范围", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="YYYY-MM")
        df_filtered = df_show[(df_show["月份"].dt.date >= date_range[0]) & (df_show["月份"].dt.date <= date_range[1])]

        st.subheader("📊 社会融资规模增量")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_filtered["月份"], y=df_filtered["社会融资规模增量"], name="社融增量", marker_color="#3498db"))
        fig.add_trace(go.Bar(x=df_filtered["月份"], y=df_filtered["其中-人民币贷款"], name="人民币贷款", marker_color="#e74c3c"))
        fig.update_layout(template="plotly_white", height=500, barmode="group", xaxis_title="月份", yaxis_title="亿元")
        st.plotly_chart(fig, use_container_width=True)

        latest = df.iloc[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("最新社融增量", f"{latest['社会融资规模增量']}亿元")
        col2.metric("其中人民币贷款", f"{latest['其中-人民币贷款']}亿元")
        col3.metric("其中企业债券", f"{latest['其中-企业债券']}亿元")

        st.subheader("社融结构占比（最新月）")
        labels = ["人民币贷款", "委托贷款外币贷款", "委托贷款", "信托贷款", "未贴现银行承兑汇票", "企业债券", "股票融资"]
        values = [
            latest["其中-人民币贷款"], latest["其中-委托贷款外币贷款"],
            latest["其中-委托贷款"], latest["其中-信托贷款"],
            latest["其中-未贴现银行承兑汇票"], latest["其中-企业债券"],
            latest["其中-非金融企业境内股票融资"]
        ]
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4)])
        fig_pie.update_layout(template="plotly_white", height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    st.markdown("**项目说明** | 数据来源：akshare 开源数据库 | 技术栈：Python + Streamlit + Plotly")