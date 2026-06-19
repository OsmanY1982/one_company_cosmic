"""
Chart Window - 桌面端数据可视化窗口
PyQt5 + PyQtChart 实现
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QLabel, QPushButton, QDateEdit,
    QTabWidget, QGridLayout, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtChart import (
    QChart, QChartView, QLineSeries, QBarSeries, QBarSet,
    QPieSeries, QPieSlice, QBarCategoryAxis, QValueAxis
)
from PyQt5.QtGui import QColor, QPainter

from services.chart_service import ChartService, ChartType


class ChartWidget(QFrame):
    """图表组件"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QVBoxLayout(self)
        
        # 标题
        if self.title:
            title_label = QLabel(self.title)
            title_label.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 10px;
            """)
            layout.addWidget(title_label)
        
        # 图表视图
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumHeight(300)
        layout.addWidget(self.chart_view)
    
    def set_chart(self, chart: QChart):
        """设置图表"""
        self.chart_view.setChart(chart)


class DashboardWidget(QFrame):
    """仪表盘组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QGridLayout(self)
        layout.setSpacing(15)
        
        # 数据卡片
        self.cards = {}
        metrics = [
            ("今日订单", "0", "#4CAF50"),
            ("今日营收", "¥0.00", "#2196F3"),
            ("本周订单", "0", "#FF9800"),
            ("本周营收", "¥0.00", "#9C27B0"),
            ("本月订单", "0", "#F44336"),
            ("本月营收", "¥0.00", "#00BCD4"),
            ("总客户", "0", "#795548"),
            ("总产品", "0", "#607D8B"),
        ]
        
        for i, (title, value, color) in enumerate(metrics):
            row = i // 4
            col = i % 4
            
            card = self.create_card(title, value, color)
            layout.addWidget(card, row, col)
            self.cards[title] = card
    
    def create_card(self, title: str, value: str, color: str) -> QFrame:
        """创建数据卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 15px;
            }}
            QLabel {{
                color: white;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; opacity: 0.9;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        value_label.setObjectName("value")
        layout.addWidget(value_label)
        
        return card
    
    def update_data(self, data: dict):
        """更新数据"""
        updates = {
            "今日订单": str(data.get("today", {}).get("orders", 0)),
            "今日营收": f"¥{data.get('today', {}).get('revenue', 0):.2f}",
            "本周订单": str(data.get("week", {}).get("orders", 0)),
            "本周营收": f"¥{data.get('week', {}).get('revenue', 0):.2f}",
            "本月订单": str(data.get("month", {}).get("orders", 0)),
            "本月营收": f"¥{data.get('month', {}).get('revenue', 0):.2f}",
            "总客户": str(data.get("total_customers", 0)),
            "总产品": str(data.get("total_products", 0)),
        }
        
        for title, value in updates.items():
            if title in self.cards:
                card = self.cards[title]
                value_label = card.findChild(QLabel, "value")
                if value_label:
                    value_label.setText(value)


class ChartWindow(QMainWindow):
    """数据可视化窗口"""
    
    def __init__(self):
        super().__init__()
        self.service = ChartService()
        self.init_ui()
        self.load_data()
        
        # 定时刷新
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(60000)  # 60秒刷新
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("数据可视化")
        self.setGeometry(50, 50, 1200, 800)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        # 时间范围选择
        toolbar.addWidget(QLabel("时间范围:"))
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        toolbar.addWidget(self.start_date)
        
        toolbar.addWidget(QLabel("至"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        toolbar.addWidget(self.end_date)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新数据")
        refresh_btn.clicked.connect(self.load_data)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addStretch()
        
        # 导出按钮
        export_btn = QPushButton("导出报表")
        export_btn.clicked.connect(self.export_report)
        toolbar.addWidget(export_btn)
        
        layout.addLayout(toolbar)
        
        # 标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 仪表盘页
        self.dashboard_tab = QWidget()
        self.init_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "仪表盘")
        
        # 销售趋势页
        self.sales_tab = QWidget()
        self.init_sales_tab()
        self.tabs.addTab(self.sales_tab, "销售趋势")
        
        # 产品分析页
        self.product_tab = QWidget()
        self.init_product_tab()
        self.tabs.addTab(self.product_tab, "产品分析")
        
        # 客户分析页
        self.customer_tab = QWidget()
        self.init_customer_tab()
        self.tabs.addTab(self.customer_tab, "客户分析")
    
    def init_dashboard_tab(self):
        """初始化仪表盘页"""
        layout = QVBoxLayout(self.dashboard_tab)
        
        # 仪表盘
        self.dashboard = DashboardWidget()
        layout.addWidget(self.dashboard)
        
        # 快捷图表
        charts_layout = QHBoxLayout()
        
        self.quick_chart1 = ChartWidget("本周销售趋势")
        charts_layout.addWidget(self.quick_chart1)
        
        self.quick_chart2 = ChartWidget("产品分类占比")
        charts_layout.addWidget(self.quick_chart2)
        
        layout.addLayout(charts_layout)
    
    def init_sales_tab(self):
        """初始化销售趋势页"""
        layout = QVBoxLayout(self.sales_tab)
        
        # 销售趋势图
        self.sales_chart = ChartWidget("销售趋势")
        layout.addWidget(self.sales_chart)
        
        # 月度对比图
        self.monthly_chart = ChartWidget("月度对比")
        layout.addWidget(self.monthly_chart)
    
    def init_product_tab(self):
        """初始化产品分析页"""
        layout = QVBoxLayout(self.product_tab)
        
        # 分类分布图
        self.category_chart = ChartWidget("产品分类分布")
        layout.addWidget(self.category_chart)
        
        # 热销排行图
        self.top_chart = ChartWidget("热销产品 TOP10")
        layout.addWidget(self.top_chart)
    
    def init_customer_tab(self):
        """初始化客户分析页"""
        layout = QVBoxLayout(self.customer_tab)
        
        # 客户价值分布
        self.customer_chart = ChartWidget("客户价值分布")
        layout.addWidget(self.customer_chart)
    
    def load_data(self):
        """加载数据"""
        try:
            # 仪表盘数据
            dashboard_data = self.service.get_dashboard_data()
            self.dashboard.update_data(dashboard_data)
            
            # 销售趋势
            sales_data = self.service.get_sales_trend(days=30)
            self.update_line_chart(self.sales_chart, sales_data)
            
            # 本周趋势（快捷）
            week_data = self.service.get_sales_trend(days=7)
            self.update_line_chart(self.quick_chart1, week_data)
            
            # 产品分类
            category_data = self.service.get_product_category_distribution()
            self.update_pie_chart(self.category_chart, category_data)
            self.update_pie_chart(self.quick_chart2, category_data)
            
            # 月度对比
            monthly_data = self.service.get_monthly_comparison(months=6)
            self.update_bar_chart(self.monthly_chart, monthly_data)
            
            # 热销产品
            top_data = self.service.get_top_products(limit=10)
            self.update_bar_chart(self.top_chart, top_data)
            
            # 客户分析
            customer_data = self.service.get_customer_analysis()
            self.update_pie_chart(self.customer_chart, customer_data)
            
        except Exception as e:
            print(f"加载数据失败: {e}")
    
    def update_line_chart(self, widget: ChartWidget, data: dict):
        """更新折线图"""
        chart = QChart()
        chart.setTitle(data.get("title", ""))
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        
        for dataset in datasets:
            series = QLineSeries()
            series.setName(dataset.get("label", ""))
            
            values = dataset.get("data", [])
            for i, value in enumerate(values):
                series.append(i, value)
            
            # 设置颜色
            color = QColor(dataset.get("borderColor", "#000000"))
            pen = series.pen()
            pen.setColor(color)
            pen.setWidth(2)
            series.setPen(pen)
            
            chart.addSeries(series)
        
        # 设置坐标轴
        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        chart.addAxis(axis_x, Qt.AlignBottom)
        
        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignLeft)
        
        for series in chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
        
        widget.set_chart(chart)
    
    def update_bar_chart(self, widget: ChartWidget, data: dict):
        """更新柱状图"""
        chart = QChart()
        chart.setTitle(data.get("title", ""))
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        
        series = QBarSeries()
        
        for dataset in datasets:
            bar_set = QBarSet(dataset.get("label", ""))
            
            values = dataset.get("data", [])
            for value in values:
                bar_set.append(value)
            
            # 设置颜色
            color = QColor(dataset.get("backgroundColor", "#000000"))
            bar_set.setColor(color)
            
            series.append(bar_set)
        
        chart.addSeries(series)
        
        # 设置坐标轴
        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        chart.addAxis(axis_x, Qt.AlignBottom)
        
        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignLeft)
        
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        
        widget.set_chart(chart)
    
    def update_pie_chart(self, widget: ChartWidget, data: dict):
        """更新饼图"""
        chart = QChart()
        chart.setTitle(data.get("title", ""))
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        series = QPieSeries()
        
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        
        if datasets:
            values = datasets[0].get("data", [])
            colors = datasets[0].get("backgroundColor", [])
            
            for i, (label, value) in enumerate(zip(labels, values)):
                slice_ = series.append(label, value)
                if i < len(colors):
                    slice_.setColor(QColor(colors[i]))
        
        chart.addSeries(series)
        widget.set_chart(chart)
    
    def export_report(self):
        """导出报表"""
        # TODO: 实现报表导出功能
        pass


# 便捷函数
def show_chart_window():
    """显示图表窗口"""
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = ChartWindow()
    window.show()
    return window
