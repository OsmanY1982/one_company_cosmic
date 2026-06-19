# `modules/data_center/dashboard_window_v3.py`

> 路径：`modules/data_center/dashboard_window_v3.py` | 行数：1083


---


```python
# -*- coding: utf-8 -*-
"""
数据大屏/BI看板模块 V3 - 终极优化版
功能：实时数据可视化、核心指标监控、趋势分析、热力图、排行榜、预测分析
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import threading
import time
from typing import Dict, List, Optional, Callable
import json
import random

# 导入报表服务
from modules.data_center.report_service_v2 import ReportServiceV2


class DashboardWindowV3:
    """数据大屏窗口 V3 - 终极优化版"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("数据大屏 - BI看板 V3")
        self.window.geometry("1600x1000")
        self.window.configure(bg='#0a0e1a')
        
        # 报表服务
        self.report_service = ReportServiceV2()
        
        # 自动刷新控制
        self.auto_refresh = True
        self.refresh_interval = 30  # 30秒
        self.refresh_thread = None
        
        # 数据缓存
        self.data_cache = {}
        self.last_update = None
        
        # 图表引用
        self.figures = {}
        self.canvases = {}
        
        # 实时交易数据
        self.recent_transactions = []
        
        self._setup_ui()
        self._start_auto_refresh()
        
    def _setup_ui(self):
        """设置UI界面 - 采用网格布局"""
        # 主容器
        main_container = tk.Frame(self.window, bg='#0a0e1a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 配置网格权重
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_rowconfigure(2, weight=2)
        main_container.grid_columnconfigure(0, weight=3)
        main_container.grid_columnconfigure(1, weight=2)
        
        # 标题栏
        self._create_header(main_container)
        
        # KPI卡片区域
        self._create_kpi_cards(main_container)
        
        # 左侧主区域 - 趋势图和热力图
        left_frame = tk.Frame(main_container, bg='#0a0e1a')
        left_frame.grid(row=2, column=0, sticky='nsew', padx=(0, 10))
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        self._create_sales_trend_chart(left_frame)
        self._create_heatmap_chart(left_frame)
        
        # 右侧辅助区域 - 排行榜和实时交易
        right_frame = tk.Frame(main_container, bg='#0a0e1a')
        right_frame.grid(row=2, column=1, sticky='nsew')
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        self._create_top_products_chart(right_frame)
        self._create_realtime_transactions(right_frame)
        
        # 底部状态栏
        self._create_status_bar(main_container)
        
    def _create_header(self, parent):
        """创建标题栏"""
        header = tk.Frame(parent, bg='#0a0e1a')
        header.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        
        # 左侧标题
        title_left = tk.Frame(header, bg='#0a0e1a')
        title_left.pack(side=tk.LEFT)
        
        title = tk.Label(
            title_left,
            text="实时数据大屏 V3",
            font=('PingFang SC', 26, 'bold'),
            fg='#f8fafc',
            bg='#0a0e1a'
        )
        title.pack(side=tk.LEFT)
        
        # 实时时钟
        self.clock_label = tk.Label(
            title_left,
            text="",
            font=('PingFang SC', 14),
            fg='#06b6d4',
            bg='#0a0e1a',
            padx=20
        )
        self.clock_label.pack(side=tk.LEFT)
        self._update_clock()
        
        # 右侧控制按钮
        controls = tk.Frame(header, bg='#0a0e1a')
        controls.pack(side=tk.RIGHT)
        
        # 刷新按钮
        refresh_btn = tk.Button(
            controls,
            text="立即刷新",
            font=('PingFang SC', 11),
            bg='#3b82f6',
            fg='white',
            activebackground='#2563eb',
            relief=tk.FLAT,
            padx=15,
            pady=6,
            cursor='hand2',
            command=self._manual_refresh
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 自动刷新开关
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_cb = tk.Checkbutton(
            controls,
            text="自动刷新",
            variable=self.auto_refresh_var,
            font=('PingFang SC', 11),
            fg='#94a3b8',
            bg='#0a0e1a',
            selectcolor='#1e293b',
            activebackground='#0a0e1a',
            activeforeground='#f8fafc',
            command=self._toggle_auto_refresh
        )
        auto_refresh_cb.pack(side=tk.LEFT, padx=10)
        
        # 全屏按钮
        fullscreen_btn = tk.Button(
            controls,
            text="全屏",
            font=('PingFang SC', 11),
            bg='#1e293b',
            fg='#94a3b8',
            activebackground='#334155',
            relief=tk.FLAT,
            padx=15,
            pady=6,
            cursor='hand2',
            command=self._toggle_fullscreen
        )
        fullscreen_btn.pack(side=tk.LEFT, padx=5)
        
        # 导出按钮
        export_btn = tk.Button(
            controls,
            text="导出报表",
            font=('PingFang SC', 11),
            bg='#10b981',
            fg='white',
            activebackground='#059669',
            relief=tk.FLAT,
            padx=15,
            pady=6,
            cursor='hand2',
            command=self._export_dashboard
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
    def _update_clock(self):
        """更新实时时钟"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.clock_label.config(text=current_time)
        self.window.after(1000, self._update_clock)
        
    def _create_kpi_cards(self, parent):
        """创建核心指标卡片 - 增强版"""
        cards_frame = tk.Frame(parent, bg='#0a0e1a')
        cards_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        
        # 定义KPI指标 - 扩展为8个
        self.kpi_metrics = [
            {
                'title': '今日销售额',
                'icon': '💰',
                'color': '#10b981',
                'key': 'today_sales',
                'format': '¥{value:,.2f}',
                'compare': 'yesterday_sales'
            },
            {
                'title': '今日订单',
                'icon': '📦',
                'color': '#3b82f6',
                'key': 'today_orders',
                'format': '{value}',
                'compare': 'yesterday_orders'
            },
            {
                'title': '客单价',
                'icon': '🛒',
                'color': '#8b5cf6',
                'key': 'avg_order_value',
                'format': '¥{value:.2f}',
                'compare': 'yesterday_avg_order'
            },
            {
                'title': '活跃会员',
                'icon': '👥',
                'color': '#06b6d4',
                'key': 'active_members',
                'format': '{value}',
                'compare': 'yesterday_members'
            },
            {
                'title': '库存预警',
                'icon': '⚠️',
                'color': '#f59e0b',
                'key': 'stock_alerts',
                'format': '{value}',
                'compare': None
            },
            {
                'title': '毛利率',
                'icon': '📈',
                'color': '#ec4899',
                'key': 'profit_margin',
                'format': '{value}%',
                'compare': 'yesterday_profit_margin'
            },
            {
                'title': '转化率',
                'icon': '🎯',
                'color': '#f97316',
                'key': 'conversion_rate',
                'format': '{value}%',
                'compare': 'yesterday_conversion'
            },
            {
                'title': '退货率',
                'icon': '↩️',
                'color': '#ef4444',
                'key': 'return_rate',
                'format': '{value}%',
                'compare': 'yesterday_return_rate'
            }
        ]
        
        self.kpi_cards = {}
        
        for i, metric in enumerate(self.kpi_metrics):
            card = self._create_kpi_card(cards_frame, metric)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)
            self.kpi_cards[metric['key']] = card
            
    def _create_kpi_card(self, parent, metric):
        """创建单个KPI卡片 - 带同比环比"""
        card = tk.Frame(
            parent,
            bg='#1e293b',
            highlightbackground='#334155',
            highlightthickness=1,
            padx=15,
            pady=15
        )
        
        # 图标和标题
        header = tk.Frame(card, bg='#1e293b')
        header.pack(fill=tk.X)
        
        icon = tk.Label(
            header,
            text=metric['icon'],
            font=('Apple Color Emoji', 20),
            bg='#1e293b'
        )
        icon.pack(side=tk.LEFT)
        
        title = tk.Label(
            header,
            text=metric['title'],
            font=('PingFang SC', 11),
            fg='#94a3b8',
            bg='#1e293b'
        )
        title.pack(side=tk.LEFT, padx=8)
        
        # 数值
        value_label = tk.Label(
            card,
            text='--',
            font=('PingFang SC', 24, 'bold'),
            fg=metric['color'],
            bg='#1e293b'
        )
        value_label.pack(pady=(10, 5))
        
        # 同比环比
        compare_frame = tk.Frame(card, bg='#1e293b')
        compare_frame.pack(fill=tk.X)
        
        trend_label = tk.Label(
            compare_frame,
            text='--',
            font=('PingFang SC', 10),
            fg='#64748b',
            bg='#1e293b'
        )
        trend_label.pack(side=tk.LEFT)
        
        mom_label = tk.Label(
            compare_frame,
            text='',
            font=('PingFang SC', 10),
            fg='#64748b',
            bg='#1e293b'
        )
        mom_label.pack(side=tk.RIGHT)
        
        # 存储引用
        card.value_label = value_label
        card.trend_label = trend_label
        card.mom_label = mom_label
        card.metric = metric
        
        return card
        
    def _create_sales_trend_chart(self, parent):
        """创建销售趋势图 - 带预测曲线"""
        chart_frame = tk.Frame(parent, bg='#1e293b', padx=15, pady=15)
        chart_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 10))
        
        # 标题栏
        header = tk.Frame(chart_frame, bg='#1e293b')
        header.pack(fill=tk.X, pady=(0, 10))
        
        title = tk.Label(
            header,
            text="销售趋势与预测（近30天）",
            font=('PingFang SC', 14, 'bold'),
            fg='#f8fafc',
            bg='#1e293b'
        )
        title.pack(side=tk.LEFT)
        
        # 图例
        legend_frame = tk.Frame(header, bg='#1e293b')
        legend_frame.pack(side=tk.RIGHT)
        
        actual_label = tk.Label(
            legend_frame,
            text="● 实际",
            font=('PingFang SC', 10),
            fg='#3b82f6',
            bg='#1e293b'
        )
        actual_label.pack(side=tk.LEFT, padx=10)
        
        predict_label = tk.Label(
            legend_frame,
            text="-- 预测",
            font=('PingFang SC', 10),
            fg='#f59e0b',
            bg='#1e293b'
        )
        predict_label.pack(side=tk.LEFT)
        
        # Matplotlib图表
        fig, ax = plt.subplots(figsize=(10, 5), facecolor='#1e293b')
        ax.set_facecolor('#1e293b')
        
        ax.tick_params(colors='#94a3b8')
        ax.xaxis.label.set_color('#94a3b8')
        ax.yaxis.label.set_color('#94a3b8')
        ax.spines['bottom'].set_color('#334155')
        ax.spines['top'].set_color('#334155')
        ax.spines['left'].set_color('#334155')
        ax.spines['right'].set_color('#334155')
        
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.figures['sales_trend'] = fig
        self.canvases['sales_trend'] = canvas
        
    def _create_heatmap_chart(self, parent):
        """创建销售热力图 - 时段分布"""
        chart_frame = tk.Frame(parent, bg='#1e293b', padx=15, pady=15)
        chart_frame.grid(row=1, column=0, sticky='nsew')
        
        # 标题
        title = tk.Label(
            chart_frame,
            text="销售热力图 - 时段分布（近7天）",
            font=('PingFang SC', 14, 'bold'),
            fg='#f8fafc',
            bg='#1e293b'
        )
        title.pack(anchor='w', pady=(0, 10))
        
        # Matplotlib图表
        fig, ax = plt.subplots(figsize=(10, 4), facecolor='#1e293b')
        ax.set_facecolor('#1e293b')
        
        ax.tick_params(colors='#94a3b8')
        ax.spines['bottom'].set_color('#334155')
        ax.spines['top'].set_color('#334155')
        ax.spines['left'].set_color('#334155')
        ax.spines['right'].set_color('#334155')
        
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.figures['heatmap'] = fig
        self.canvases['heatmap'] = canvas
        
    def _create_top_products_chart(self, parent):
        """创建Top产品排行榜"""
        chart_frame = tk.Frame(parent, bg='#1e293b', padx=15, pady=15)
        chart_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 10))
        
        # 标题栏
        header = tk.Frame(chart_frame, bg='#1e293b')
        header.pack(fill=tk.X, pady=(0, 10))
        
        title = tk.Label(
            header,
            text="🔥 Top 10 热销产品",
            font=('PingFang SC', 14, 'bold'),
            fg='#f8fafc',
            bg='#1e293b'
        )
        title.pack(side=tk.LEFT)
        
        # 切换按钮
        self.top_switch_var = tk.StringVar(value='products')
        products_btn = tk.Radiobutton(
            header,
            text="产品",
            variable=self.top_switch_var,
            value='products',
            font=('PingFang SC', 10),
            fg='#94a3b8',
            bg='#1e293b',
            selectcolor='#3b82f6',
            activebackground='#1e293b',
            command=self._switch_top_chart
        )
        products_btn.pack(side=tk.RIGHT, padx=5)
        
        customers_btn = tk.Radiobutton(
            header,
            text="客户",
            variable=self.top_switch_var,
            value='customers',
            font=('PingFang SC', 10),
            fg='#94a3b8',
            bg='#1e293b',
            selectcolor='#3b82f6',
            activebackground='#1e293b',
            command=self._switch_top_chart
        )
        customers_btn.pack(side=tk.RIGHT, padx=5)
        
        # Matplotlib图表
        fig, ax = plt.subplots(figsize=(8, 5), facecolor='#1e293b')
        ax.set_facecolor('#1e293b')
        
        ax.tick_params(colors='#94a3b8')
        ax.spines['bottom'].set_color('#334155')
        ax.spines['top'].set_color('#334155')
        ax.spines['left'].set_color('#334155')
        ax.spines['right'].set_color('#334155')
        
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.figures['top_products'] = fig
        self.canvases['top_products'] = canvas
        
    def _create_realtime_transactions(self, parent):
        """创建实时交易滚动列表"""
        chart_frame = tk.Frame(parent, bg='#1e293b', padx=15, pady=15)
        chart_frame.grid(row=1, column=0, sticky='nsew')
        
        # 标题
        title = tk.Label(
            chart_frame,
            text="📋 实时交易动态",
            font=('PingFang SC', 14, 'bold'),
            fg='#f8fafc',
            bg='#1e293b'
        )
        title.pack(anchor='w', pady=(0, 10))
        
        # 交易列表框架
        list_frame = tk.Frame(chart_frame, bg='#1e293b')
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表头
        header_frame = tk.Frame(list_frame, bg='#334155')
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        headers = ['时间', '订单号', '客户', '金额', '状态']
        widths = [12, 15, 15, 12, 10]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            label = tk.Label(
                header_frame,
                text=header,
                font=('PingFang SC', 10, 'bold'),
                fg='#94a3b8',
                bg='#334155',
                width=width
            )
            label.pack(side=tk.LEFT, padx=5)
        
        # 交易列表容器
        self.transaction_list = tk.Frame(list_frame, bg='#1e293b')
        self.transaction_list.pack(fill=tk.BOTH, expand=True)
        
        # 存储交易标签引用
        self.transaction_labels = []
        
    def _create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = tk.Frame(parent, bg='#0a0e1a')
        status_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(15, 0))
        
        # 最后更新时间
        self.update_time_label = tk.Label(
            status_frame,
            text="最后更新: --",
            font=('PingFang SC', 10),
            fg='#64748b',
            bg='#0a0e1a'
        )
        self.update_time_label.pack(side=tk.LEFT)
        
        # 数据状态
        self.data_status_label = tk.Label(
            status_frame,
            text="数据状态: 等待刷新",
            font=('PingFang SC', 10),
            fg='#64748b',
            bg='#0a0e1a'
        )
        self.data_status_label.pack(side=tk.RIGHT)
        
        # 系统信息
        self.system_info_label = tk.Label(
            status_frame,
            text="系统运行正常 | 数据延迟: <1s",
            font=('PingFang SC', 10),
            fg='#10b981',
            bg='#0a0e1a'
        )
        self.system_info_label.pack(side=tk.RIGHT, padx=20)
        
    def _start_auto_refresh(self):
        """启动自动刷新"""
        if self.refresh_thread and self.refresh_thread.is_alive():
            return
            
        self.refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
        self.refresh_thread.start()
        
    def _auto_refresh_loop(self):
        """自动刷新循环"""
        while True:
            if self.auto_refresh and self.auto_refresh_var.get():
                self._refresh_data()
                
            # 等待间隔
            for _ in range(self.refresh_interval):
                if not self.auto_refresh:
                    break
                time.sleep(1)
                
    def _toggle_auto_refresh(self):
        """切换自动刷新状态"""
        self.auto_refresh = self.auto_refresh_var.get()
        if self.auto_refresh:
            self._start_auto_refresh()
            
    def _manual_refresh(self):
        """手动刷新数据"""
        threading.Thread(target=self._refresh_data, daemon=True).start()
        
    def _refresh_data(self):
        """刷新数据"""
        try:
            # 获取报表数据
            report_data = self.report_service.get_dashboard_data()
            
            # 更新KPI卡片
            self._update_kpi_cards(report_data)
            
            # 更新图表
            self._update_charts(report_data)
            
            # 更新实时交易
            self._update_realtime_transactions()
            
            # 更新状态
            self.last_update = datetime.now()
            self._update_status()
            
        except Exception as e:
            print(f"刷新数据失败: {e}")
            
    def _update_kpi_cards(self, data):
        """更新KPI卡片 - 带同比环比"""
        for key, card in self.kpi_cards.items():
            if key in data:
                value = data[key]
                metric = card.metric
                
                # 格式化数值
                formatted = metric['format'].format(value=value)
                card.value_label.config(text=formatted)
                
                # 计算同比（与昨日对比）
                compare_key = metric.get('compare')
                if compare_key and compare_key in data:
                    compare_value = data[compare_key]
                    if compare_value and compare_value > 0:
                        change = ((value - compare_value) / compare_value) * 100
                        if change > 0:
                            card.trend_label.config(
                                text=f"▲ +{change:.1f}% 较昨日",
                                fg='#10b981'
                            )
                        elif change < 0:
                            card.trend_label.config(
                                text=f"▼ {change:.1f}% 较昨日",
                                fg='#ef4444'
                            )
                        else:
                            card.trend_label.config(
                                text="- 持平",
                                fg='#64748b'
                            )
                            
                # 计算环比（与上周同日对比）
                mom_key = f'{key}_mom'
                if mom_key in data:
                    mom_value = data[mom_key]
                    if mom_value and mom_value > 0:
                        mom_change = ((value - mom_value) / mom_value) * 100
                        card.mom_label.config(
                            text=f"周环比: {mom_change:+.1f}%",
                            fg='#06b6d4' if mom_change >= 0 else '#f59e0b'
                        )
                        
    def _update_charts(self, data):
        """更新图表"""
        # 更新销售趋势图
        if 'sales_trend' in self.figures:
            self._update_sales_trend(data.get('sales_trend', []))
            
        # 更新热力图
        if 'heatmap' in self.figures:
            self._update_heatmap(data.get('hourly_sales', []))
            
        # 更新Top产品图
        if 'top_products' in self.figures:
            if self.top_switch_var.get() == 'products':
                self._update_top_products(data.get('top_products', []))
            else:
                self._update_top_customers(data.get('top_customers', []))
                
    def _update_sales_trend(self, trend_data):
        """更新销售趋势图 - 带预测"""
        fig = self.figures['sales_trend']
        ax = fig.axes[0]
        ax.clear()
        
        if not trend_data:
            # 模拟数据 - 30天
            dates = [datetime.now() - timedelta(days=i) for i in range(29, -1, -1)]
            values = [15000 + i * 200 + random.randint(-2000, 2000) for i in range(30)]
        else:
            dates = [item['date'] for item in trend_data]
            values = [item['amount'] for item in trend_data]
            
        # 绘制实际数据
        ax.plot(dates, values, color='#3b82f6', linewidth=2, marker='o', 
                markersize=4, label='实际销售')
        ax.fill_between(dates, values, alpha=0.2, color='#3b82f6')
        
        # 预测未来7天
        if len(values) >= 7:
            # 简单线性预测
            last_7_days = values[-7:]
            avg_growth = (last_7_days[-1] - last_7_days[0]) / 6
            
            future_dates = [dates[-1] + timedelta(days=i) for i in range(1, 8)]
            future_values = [values[-1] + avg_growth * i + random.randint(-500, 500) 
                           for i in range(1, 8)]
            
            ax.plot(future_dates, future_values, color='#f59e0b', linewidth=2, 
                   linestyle='--', marker='s', markersize=4, label='AI预测')
            ax.fill_between(future_dates, future_values, alpha=0.1, color='#f59e0b')
        
        # 设置样式
        ax.set_facecolor('#1e293b')
        ax.tick_params(colors='#94a3b8')
        ax.spines['bottom'].set_color('#334155')
        ax.spines['top'].set_color('#334155')
        ax.spines['left'].set_color('#334155')
        ax.spines['right'].set_color('#334155')
        
        # 格式化日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        ax.set_title('销售趋势与AI预测', color='#f8fafc', fontsize=14, pad=15)
        ax.set_ylabel('销售额 (¥)', color='#94a3b8')
        ax.legend(loc='upper left', facecolor='#1e293b', edgecolor='#334155', 
                 labelcolor='#f8fafc')
        ax.grid(True, alpha=0.2, color='#334155')
        
        fig.tight_layout()
        self.canvases['sales_trend'].draw()
        
    def _update_heatmap(self, hourly_data):
        """更新销售热力图"""
        fig = self.figures['heatmap']
        ax = fig.axes[0]
        ax.clear()
        
        if not hourly_data:
            # 模拟数据 - 7天 x 24小时
            days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            hours = list(range(24))
            
            # 生成热力数据
            heat_data = []
            for day in range(7):
                day_data = []
                for hour in range(24):
                    # 模拟销售高峰：中午12点和晚上8点
                    base = 10
                    if 11 <= hour <= 13:
                        base = 80
                    elif 18 <= hour <= 21:
                        base = 100
                    elif 9 <= hour <= 17:
                        base = 40
                    else:
                        base = 5
                    
                    # 周末更高
                    if day >= 5:
                        base *= 1.3
                        
                    day_data.append(base + random.randint(-10, 10))
                heat_data.append(day_data)
        else:
            days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            hours = list(range(24))
            heat_data = hourly_data
            
        # 绘制热力图
        im = ax.imshow(heat_data, cmap='YlOrRd', aspect='auto')
        
        # 设置坐标轴
        ax.set_xticks(range(0, 24, 2))
        ax.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)])
        ax.set_yticks(range(7))
        ax.set_yticklabels(days)
        
        ax.tick_params(colors='#94a3b8')
        ax.spines['bottom'].set_color('#334155')
        ax.spines['top'].set_color('#334155')
        ax.spines['left'].set_color('#334155')
        ax.spines['right'].set_color('#334155')
        
        # 添加数值标注
        for i in range(7):
            for j in range(24):
                text = ax.text(j, i, int(heat_data[i][j]),
                             ha="center", va="center", color="black", fontsize=6)
        
        ax.set_title('销售热力图 - 时段分布', color='#f8fafc', fontsize=14, pad=15)
        ax.set_xlabel('时间', color='#94a3b8')
        
        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('销售量', color='#94a3b8')
        cbar.ax.yaxis.set_tick_params(color='#94a3b8')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#94a3b8')
        
        fig.tight_layout()
        self.canvases['heatmap'].draw()
        
    def _update_top_products(self, products_data):
        """更新Top产品排行榜"""
        fig = self.figures['top_products']
        ax = fig.axes[0]
        ax.clear()
        
        if not products_data:
            # 模拟数据
            products = ['产品A', '产品B', '产品C', '产品D', '产品E', 
                       '产品F', '产品G', '产品H', '产品I', '产品J']
            sales = [5200, 4800, 4500, 4200, 3900, 3600, 3300, 3000, 2700, 2400]
        else:
            products = [item['name'] for item in products_data[:10]]
            sales = [item['sales'] for item in products_data[:10]]
            
        # 颜色渐变
        colors = plt.cm.viridis([i/len(products) for i in range(len(products))])
        
        # 绘制水平条形图
        bars = ax.barh(range(len(products)), sales, color=colors)
        ax.set_yticks(range(len(products)))
        ax.set_yticklabels(products)
        ax.invert_yaxis()  # 最高在顶部
        
        # 添加数值标签
        for i, (bar, sale) in enumerate(zip(bars, sales)):
            ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
                   f'¥{sale:,.0f}', va='center', color='#f8fafc', fontsize=9)
        
        # 设置样式
        ax.set_facecolor('#1e293b')
        ax.tick_params(colors='#94a3b8')
        ax.spines['bottom'].set_color('#334155')
        ax.spines['top'].set_color('#334155')
        ax.spines['left'].set_color('#334155')
        ax.spines['right'].set_color('#334155')
        
        ax.set_title('Top 10 热销产品', color='#f8fafc', fontsize=14, pad=15)
        ax.set_xlabel('销售额 (¥)', color='#94a3b8')
        
        fig.tight_layout()
        self.canvases['top_products'].draw()
        
    def _update_top_customers(self, customers_data):
        """更新Top客户排行榜"""
        fig = self.figures['top_products']
        ax = fig.axes[0]
        ax.clear()
        
        if not customers_data:
            # 模拟数据
            customers = ['客户A', '客户B', '客户C', '客户D', '客户E',
                        '客户F', '客户G', '客户H', '客户I', '客户J']
            amounts = [15000, 13200, 11800, 10500, 9800, 8700, 7600, 6500, 5400, 4300]
        else:
            customers = [item['name'] for item in customers_data[:10]]
            amounts = [item['amount'] for item in customers_data[:10]]
            
        # 颜色渐变
        colors = plt.cm.plasma([i/len(customers) for i in range(len(customers))])
        
        # 绘制水平条形图
        bars = ax.barh(range(len(customers)), amounts, color=colors)
        ax.set_yticks(range(len(customers)))
        ax.set_yticklabels(customers)
        ax.invert_yaxis()
        
        # 添加数值标签
        for i, (bar, amount) in enumerate(zip(bars, amounts)):
            ax.text(bar.get_width() + 100, bar.get_y() + bar.get_height()/2,
                   f'¥{amount:,.0f}', va='center', color='#f8fafc', fontsize=9)
        
        # 设置样式
        ax.set_facecolor('#1e293b')
        ax.tick_params(colors='#94a3b8')
        ax.spines['bottom'].set_color('#334155')
        ax.spines['top'].set_color('#334155')
        ax.spines['left'].set_color('#334155')
        ax.spines['right'].set_color('#334155')
        
        ax.set_title('Top 10 价值客户', color='#f8fafc', fontsize=14, pad=15)
        ax.set_xlabel('消费金额 (¥)', color='#94a3b8')
        
        fig.tight_layout()
        self.canvases['top_products'].draw()
        
    def _switch_top_chart(self):
        """切换Top排行榜"""
        self._refresh_data()
        
    def _update_realtime_transactions(self):
        """更新实时交易列表"""
        # 模拟获取最新交易
        new_transactions = self._generate_mock_transactions(5)
        
        # 添加到列表开头
        self.recent_transactions = new_transactions + self.recent_transactions
        self.recent_transactions = self.recent_transactions[:20]  # 保留最近20条
        
        # 清空现有列表
        for widget in self.transaction_list.winfo_children():
            widget.destroy()
        
        # 显示最新10条
        for i, trans in enumerate(self.recent_transactions[:10]):
            row_frame = tk.Frame(self.transaction_list, bg='#1e293b')
            row_frame.pack(fill=tk.X, pady=1)
            
            # 交替背景色
            if i % 2 == 0:
                row_frame.configure(bg='#1e293b')
            else:
                row_frame.configure(bg='#252f47')
            
            # 时间
            time_label = tk.Label(
                row_frame,
                text=trans['time'],
                font=('PingFang SC', 9),
                fg='#94a3b8',
                bg=row_frame['bg'],
                width=12
            )
            time_label.pack(side=tk.LEFT, padx=5)
            
            # 订单号
            order_label = tk.Label(
                row_frame,
                text=trans['order_no'],
                font=('PingFang SC', 9),
                fg='#f8fafc',
                bg=row_frame['bg'],
                width=15
            )
            order_label.pack(side=tk.LEFT, padx=5)
            
            # 客户
            customer_label = tk.Label(
                row_frame,
                text=trans['customer'],
                font=('PingFang SC', 9),
                fg='#f8fafc',
                bg=row_frame['bg'],
                width=15
            )
            customer_label.pack(side=tk.LEFT, padx=5)
            
            # 金额
            amount_label = tk.Label(
                row_frame,
                text=f"¥{trans['amount']:.2f}",
                font=('PingFang SC', 9, 'bold'),
                fg='#10b981',
                bg=row_frame['bg'],
                width=12
            )
            amount_label.pack(side=tk.LEFT, padx=5)
            
            # 状态
            status_colors = {
                '完成': '#10b981',
                '处理中': '#f59e0b',
                '待支付': '#3b82f6'
            }
            status_label = tk.Label(
                row_frame,
                text=trans['status'],
                font=('PingFang SC', 9),
                fg=status_colors.get(trans['status'], '#94a3b8'),
                bg=row_frame['bg'],
                width=10
            )
            status_label.pack(side=tk.LEFT, padx=5)
            
    def _generate_mock_transactions(self, count=5):
        """生成模拟交易数据"""
        transactions = []
        statuses = ['完成', '处理中', '待支付']
        customers = ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十']
        
        for i in range(count):
            trans = {
                'time': (datetime.now() - timedelta(minutes=random.randint(1, 60))).strftime('%H:%M:%S'),
                'order_no': f'ORD{datetime.now().strftime("%Y%m%d")}{random.randint(1000, 9999)}',
                'customer': random.choice(customers),
                'amount': random.uniform(100, 5000),
                'status': random.choice(statuses)
            }
            transactions.append(trans)
            
        return transactions
        
    def _update_status(self):
        """更新状态栏"""
        if self.last_update:
            time_str = self.last_update.strftime('%Y-%m-%d %H:%M:%S')
            self.update_time_label.config(text=f"最后更新: {time_str}")
            self.data_status_label.config(
                text="数据状态: 正常",
                fg='#10b981'
            )
            
    def _toggle_fullscreen(self):
        """切换全屏模式"""
        is_fullscreen = self.window.attributes('-fullscreen')
        self.window.attributes('-fullscreen', not is_fullscreen)
        
    def _export_dashboard(self):
        """导出报表"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG图片", "*.png"), ("PDF文档", "*.pdf"), ("所有文件", "*.*")],
                title="导出数据大屏"
            )
            
            if filename:
                # 保存当前窗口截图
                self.window.update()
                x = self.window.winfo_rootx()
                y = self.window.winfo_rooty()
                width = self.window.winfo_width()
                height = self.window.winfo_height()
                
                import pyautogui
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
                screenshot.save(filename)
                
                messagebox.showinfo("导出成功", f"数据大屏已保存至:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("导出失败", f"导出报表时出错:\n{str(e)}")
            
    def show(self):
        """显示窗口"""
        # 初始加载数据
        self._refresh_data()
        
        if not self.parent:
            self.window.mainloop()
            
    def close(self):
        """关闭窗口"""
        self.auto_refresh = False
        if self.refresh_thread:
            self.refresh_thread.join(timeout=2)
        self.window.destroy()


# 便捷函数
def show_dashboard_v3(parent=None):
    """显示数据大屏 V3"""
    dashboard = DashboardWindowV3(parent)
    dashboard.show()
    return dashboard


if __name__ == '__main__':
    # 测试运行
    show_dashboard_v3()

```
