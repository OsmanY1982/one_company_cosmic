# `modules/data_center/dashboard_window_v2.py`

> 路径：`modules/data_center/dashboard_window_v2.py` | 行数：639


---


```python
# -*- coding: utf-8 -*-
"""
数据大屏/BI看板模块 V2 - 增强版
提供实时数据可视化、核心指标监控、趋势分析
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

# 导入报表服务
from modules.report.report_service_v2 import ReportServiceV2


class DashboardWindowV2:
    """数据大屏窗口 V2"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("数据大屏 - BI看板 V2")
        self.window.geometry("1400x900")
        self.window.configure(bg='#0f172a')
        
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
        
        self._setup_ui()
        self._start_auto_refresh()
        
    def _setup_ui(self):
        """设置UI界面"""
        # 主容器
        main_container = tk.Frame(self.window, bg='#0f172a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题栏
        self._create_header(main_container)
        
        # 核心指标卡片
        self._create_kpi_cards(main_container)
        
        # 图表区域
        self._create_charts_area(main_container)
        
        # 底部状态栏
        self._create_status_bar(main_container)
        
    def _create_header(self, parent):
        """创建标题栏"""
        header = tk.Frame(parent, bg='#0f172a')
        header.pack(fill=tk.X, pady=(0, 20))
        
        # 标题
        title = tk.Label(
            header,
            text="实时数据大屏",
            font=('PingFang SC', 24, 'bold'),
            fg='#f8fafc',
            bg='#0f172a'
        )
        title.pack(side=tk.LEFT)
        
        # 控制按钮
        controls = tk.Frame(header, bg='#0f172a')
        controls.pack(side=tk.RIGHT)
        
        # 刷新按钮
        refresh_btn = tk.Button(
            controls,
            text="刷新",
            font=('PingFang SC', 12),
            bg='#3b82f6',
            fg='white',
            activebackground='#2563eb',
            relief=tk.FLAT,
            padx=20,
            pady=8,
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
            bg='#0f172a',
            selectcolor='#1e293b',
            activebackground='#0f172a',
            activeforeground='#f8fafc',
            command=self._toggle_auto_refresh
        )
        auto_refresh_cb.pack(side=tk.LEFT, padx=10)
        
        # 全屏按钮
        fullscreen_btn = tk.Button(
            controls,
            text="全屏",
            font=('PingFang SC', 12),
            bg='#1e293b',
            fg='#94a3b8',
            activebackground='#334155',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._toggle_fullscreen
        )
        fullscreen_btn.pack(side=tk.LEFT, padx=5)
        
    def _create_kpi_cards(self, parent):
        """创建核心指标卡片"""
        cards_frame = tk.Frame(parent, bg='#0f172a')
        cards_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 定义KPI指标
        self.kpi_metrics = [
            {
                'title': '今日销售额',
                'icon': '💰',
                'color': '#10b981',
                'key': 'today_sales',
                'format': '¥{value:,.2f}'
            },
            {
                'title': '今日订单',
                'icon': '📦',
                'color': '#3b82f6',
                'key': 'today_orders',
                'format': '{value}'
            },
            {
                'title': '活跃会员',
                'icon': '👥',
                'color': '#8b5cf6',
                'key': 'active_members',
                'format': '{value}'
            },
            {
                'title': '库存预警',
                'icon': '⚠️',
                'color': '#f59e0b',
                'key': 'stock_alerts',
                'format': '{value}'
            },
            {
                'title': '毛利率',
                'icon': '📈',
                'color': '#ec4899',
                'key': 'profit_margin',
                'format': '{value}%'
            },
            {
                'title': '客户满意度',
                'icon': '⭐',
                'color': '#06b6d4',
                'key': 'satisfaction',
                'format': '{value}'
            }
        ]
        
        self.kpi_cards = {}
        
        for i, metric in enumerate(self.kpi_metrics):
            card = self._create_kpi_card(cards_frame, metric)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
            self.kpi_cards[metric['key']] = card
            
    def _create_kpi_card(self, parent, metric):
        """创建单个KPI卡片"""
        card = tk.Frame(
            parent,
            bg='#1e293b',
            highlightbackground='#334155',
            highlightthickness=1,
            padx=20,
            pady=20
        )
        
        # 图标和标题
        header = tk.Frame(card, bg='#1e293b')
        header.pack(fill=tk.X)
        
        icon = tk.Label(
            header,
            text=metric['icon'],
            font=('Apple Color Emoji', 24),
            bg='#1e293b'
        )
        icon.pack(side=tk.LEFT)
        
        title = tk.Label(
            header,
            text=metric['title'],
            font=('PingFang SC', 12),
            fg='#94a3b8',
            bg='#1e293b'
        )
        title.pack(side=tk.LEFT, padx=10)
        
        # 数值
        value_label = tk.Label(
            card,
            text='--',
            font=('PingFang SC', 28, 'bold'),
            fg=metric['color'],
            bg='#1e293b'
        )
        value_label.pack(pady=(15, 5))
        
        # 趋势
        trend_label = tk.Label(
            card,
            text='--',
            font=('PingFang SC', 11),
            fg='#64748b',
            bg='#1e293b'
        )
        trend_label.pack()
        
        # 存储引用
        card.value_label = value_label
        card.trend_label = trend_label
        card.metric = metric
        
        return card
        
    def _create_charts_area(self, parent):
        """创建图表区域"""
        charts_frame = tk.Frame(parent, bg='#0f172a')
        charts_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左列 - 趋势图
        left_frame = tk.Frame(charts_frame, bg='#0f172a')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 销售趋势图
        self._create_sales_trend_chart(left_frame)
        
        # 右列 - 分布图
        right_frame = tk.Frame(charts_frame, bg='#0f172a')
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 产品分类饼图
        self._create_category_pie_chart(right_frame)
        
        # 会员增长图
        self._create_member_growth_chart(right_frame)
        
    def _create_sales_trend_chart(self, parent):
        """创建销售趋势图"""
        chart_frame = tk.Frame(parent, bg='#1e293b', padx=15, pady=15)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 标题
        title = tk.Label(
            chart_frame,
            text="销售趋势（近7天）",
            font=('PingFang SC', 14, 'bold'),
            fg='#f8fafc',
            bg='#1e293b'
        )
        title.pack(anchor='w', pady=(0, 10))
        
        # Matplotlib图表
        fig, ax = plt.subplots(figsize=(8, 5), facecolor='#1e293b')
        ax.set_facecolor('#1e293b')
        
        # 设置颜色
        ax.tick_params(colors='#94a3b8')
        ax.xaxis.label.set_color('#94a3b8')
        ax.yaxis.label.set_color('#94a3b8')
        ax.title.set_color('#f8fafc')
        ax.spines['bottom'].set_color('#334155')
        ax.spines['top'].set_color('#334155')
        ax.spines['left'].set_color('#334155')
        ax.spines['right'].set_color('#334155')
        
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.figures['sales_trend'] = fig
        self.canvases['sales_trend'] = canvas
        
    def _create_category_pie_chart(self, parent):
        """创建产品分类饼图"""
        chart_frame = tk.Frame(parent, bg='#1e293b', padx=15, pady=15)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 标题
        title = tk.Label(
            chart_frame,
            text="产品销售分布",
            font=('PingFang SC', 14, 'bold'),
            fg='#f8fafc',
            bg='#1e293b'
        )
        title.pack(anchor='w', pady=(0, 10))
        
        # Matplotlib图表
        fig, ax = plt.subplots(figsize=(6, 4), facecolor='#1e293b')
        ax.set_facecolor('#1e293b')
        
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.figures['category_pie'] = fig
        self.canvases['category_pie'] = canvas
        
    def _create_member_growth_chart(self, parent):
        """创建会员增长图"""
        chart_frame = tk.Frame(parent, bg='#1e293b', padx=15, pady=15)
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title = tk.Label(
            chart_frame,
            text="会员增长趋势",
            font=('PingFang SC', 14, 'bold'),
            fg='#f8fafc',
            bg='#1e293b'
        )
        title.pack(anchor='w', pady=(0, 10))
        
        # Matplotlib图表
        fig, ax = plt.subplots(figsize=(6, 4), facecolor='#1e293b')
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
        
        self.figures['member_growth'] = fig
        self.canvases['member_growth'] = canvas
        
    def _create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = tk.Frame(parent, bg='#0f172a')
        status_frame.pack(fill=tk.X, pady=(20, 0))
        
        # 最后更新时间
        self.update_time_label = tk.Label(
            status_frame,
            text="最后更新: --",
            font=('PingFang SC', 10),
            fg='#64748b',
            bg='#0f172a'
        )
        self.update_time_label.pack(side=tk.LEFT)
        
        # 数据状态
        self.data_status_label = tk.Label(
            status_frame,
            text="数据状态: 等待刷新",
            font=('PingFang SC', 10),
            fg='#64748b',
            bg='#0f172a'
        )
        self.data_status_label.pack(side=tk.RIGHT)
        
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
            
            # 更新状态
            self.last_update = datetime.now()
            self._update_status()
            
        except Exception as e:
            print(f"刷新数据失败: {e}")
            
    def _update_kpi_cards(self, data):
        """更新KPI卡片"""
        for key, card in self.kpi_cards.items():
            if key in data:
                value = data[key]
                metric = card.metric
                
                # 格式化数值
                formatted = metric['format'].format(value=value)
                card.value_label.config(text=formatted)
                
                # 计算趋势（模拟）
                trend = data.get(f'{key}_trend', 0)
                if trend > 0:
                    card.trend_label.config(
                        text=f"▲ +{trend}% 较昨日",
                        fg='#10b981'
                    )
                elif trend < 0:
                    card.trend_label.config(
                        text=f"▼ {trend}% 较昨日",
                        fg='#ef4444'
                    )
                else:
                    card.trend_label.config(
                        text="- 持平",
                        fg='#64748b'
                    )
                    
    def _update_charts(self, data):
        """更新图表"""
        # 更新销售趋势图
        if 'sales_trend' in self.figures:
            self._update_sales_trend(data.get('sales_trend', []))
            
        # 更新产品分类饼图
        if 'category_pie' in self.figures:
            self._update_category_pie(data.get('category_distribution', {}))
            
        # 更新会员增长图
        if 'member_growth' in self.figures:
            self._update_member_growth(data.get('member_growth', []))
            
    def _update_sales_trend(self, trend_data):
        """更新销售趋势图"""
        fig = self.figures['sales_trend']
        ax = fig.axes[0]
        ax.clear()
        
        if not trend_data:
            # 模拟数据
            dates = [datetime.now() - timedelta(days=i) for i in range(6, -1, -1)]
            values = [15000, 18000, 16500, 21000, 19500, 23000, 25000]
        else:
            dates = [item['date'] for item in trend_data]
            values = [item['amount'] for item in trend_data]
            
        # 绘制折线图
        ax.plot(dates, values, color='#3b82f6', linewidth=2, marker='o', markersize=6)
        ax.fill_between(dates, values, alpha=0.3, color='#3b82f6')
        
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
        
        ax.set_title('销售趋势', color='#f8fafc', fontsize=14, pad=15)
        ax.set_ylabel('销售额 (¥)', color='#94a3b8')
        ax.grid(True, alpha=0.2, color='#334155')
        
        fig.tight_layout()
        self.canvases['sales_trend'].draw()
        
    def _update_category_pie(self, category_data):
        """更新产品分类饼图"""
        fig = self.figures['category_pie']
        ax = fig.axes[0]
        ax.clear()
        
        if not category_data:
            # 模拟数据
            categories = ['电子产品', '服装', '食品', '家居', '其他']
            values = [35, 25, 20, 15, 5]
        else:
            categories = list(category_data.keys())
            values = list(category_data.values())
            
        # 颜色方案
        colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']
        
        # 绘制饼图
        wedges, texts, autotexts = ax.pie(
            values,
            labels=categories,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'color': '#f8fafc', 'fontsize': 10}
        )
        
        # 设置百分比文字颜色
        for autotext in autotexts:
            autotext.set_color('#1e293b')
            autotext.set_fontweight('bold')
            
        ax.set_facecolor('#1e293b')
        fig.tight_layout()
        self.canvases['category_pie'].draw()
        
    def _update_member_growth(self, growth_data):
        """更新会员增长图"""
        fig = self.figures['member_growth']
        ax = fig.axes[0]
        ax.clear()
        
        if not growth_data:
            # 模拟数据
            dates = [datetime.now() - timedelta(days=i) for i in range(29, -1, -1)]
            members = [100 + i * 5 + (i % 7) * 3 for i in range(30)]
        else:
            dates = [item['date'] for item in growth_data]
            members = [item['count'] for item in growth_data]
            
        # 绘制柱状图
        bars = ax.bar(dates, members, color='#10b981', alpha=0.7, width=0.6)
        
        # 高亮最新数据
        if bars:
            bars[-1].set_color='#06b6d4'
            
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
        
        ax.set_title('会员增长', color='#f8fafc', fontsize=14, pad=15)
        ax.set_ylabel('会员数', color='#94a3b8')
        ax.grid(True, alpha=0.2, color='#334155', axis='y')
        
        fig.tight_layout()
        self.canvases['member_growth'].draw()
        
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
def show_dashboard_v2(parent=None):
    """显示数据大屏 V2"""
    dashboard = DashboardWindowV2(parent)
    dashboard.show()
    return dashboard


if __name__ == '__main__':
    # 测试运行
    show_dashboard_v2()

```
