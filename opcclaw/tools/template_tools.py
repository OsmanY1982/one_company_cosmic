"""常用模板库 — 邮件/合同/报价/通知等一键生成"""

import os
from datetime import datetime

class TemplateTools:
    def __init__(self, data_dir): self.data_dir = data_dir
    
    templates = {
        "invoice": ("💰 发票通知模板", """尊敬的{customer_name}：

您好！您的订单 #{order_no} 已确认开票。

📋 开票信息:
- 金额: ¥{amount}
- 商品: {product}
- 开票日期: {date}
- 发票抬头: {company}

我们将尽快将电子发票发送至您的邮箱 {email}。

如有问题请随时联系。"""),
        
        "delivery_notice": ("🚚 发货通知模板", """尊敬的高价值客户 {name}:

您的订单 #{order_no} 已从仓库发出!

📦 物流信息:
- 快递公司: {courier}
- 运单号: {tracking}
- 预计送达: {est_date}

请您注意查收，如有疑问请联系客服。"""),
        
        "contract": ("📄 服务合同模板", """【合作协议】

甲方（服务方）：{company_name}
乙方（客户）：{client_name}

第一条 服务内容
{service_description}

第二条 费用条款
本合同总金额为人民币¥{amount}元整。

第三条 协议期限
本协议自 {start_date} 起至 {end_date} 止。

第四条 双方权利与义务
1. 甲方应按照约定提供服务
2. 乙方应按时支付相关费用

甲方签字：_____________  乙方签字：_____________
日期：{date}"""),
        
        "price_quotation": ("📊 报价单模板", """【产品报价单】

致：{company_name}
联系人：{contact}
电话：{phone}
日期：{quote_date}

| 序号 | 产品名称 | 单价(元) | 数量 | 小计(元) |
|------|----------|----------|------|----------|
"""),
        
        "meeting_minutes": ("📝 会议纪要模板", """# 会议纪要

会议主题：{topic}
时间：{datetime}
地点：{location}
主持人：{host}
记录人：{recorder}

## 议题一：{issue1}
{details1}

## 议题二：{issue2}
{details2}

## 待办事项
| 任务 | 负责人 | 截止日期 |
|------|--------|----------|
"""),
        
        "customer_survey": ("📊 客户满意度调查模板", """尊敬的{customer_name}：

感谢您选择我们的产品！为提供更好的服务，诚邀您参与以下简短调研。

1. 您对产品的整体满意度？
   □ 非常满意  □ 满意  □ 一般  □ 不满意  □ 非常不满意

2. 您是否愿意向朋友推荐我们的产品？
   □ 是  □ 否  □ 不确定

3. 您认为我们可以改进的地方？
   _____________________________________

您的反馈对我们非常重要，感谢您的配合！

祝您生活愉快！

{company_name} 客户服务团队
{survey_date}""")
    }
    
    def list_all_templates(self) -> dict:
        """列出所有可用模板"""
        result = {"templates": [], "categories": {}}
        for key, (title, content) in self.templates.items():
            info = {"key": key, "title": title, "length": len(content)}
            result["templates"].append(info)
            
            cat = "商务" if any(w in title for w in ["合同","报价","发票"]) else "运营" if any(w in title for w in ["交付","调查"]) else "沟通"
            if cat not in result["categories"]: result["categories"][cat] = []
            result["categories"][cat].append(key)
        
        return result
    
    def generate_template(self, template_key: str, **kwargs) -> dict:
        """根据模板键值生成内容"""
        if template_key not in self.templates:
            available = ", ".join(self.templates.keys())
            return {"error": f"未找到模板 '{template_key}'，可用：{available}"}
        
        title, content = self.templates[template_key]
        
        # 自动填充默认字段
        defaults = {
            "company": "OPCclaw 数字办公室",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "survey_date": datetime.now().strftime("%Y-%m-%d")
        }
        defaults.update({k:v for k,v in kwargs.items() if v})
        
        try:
            filled = content.format(**defaults)
        except KeyError as e:
            missing = str(e).strip("'")
            return {"error": f"缺少必填参数：{missing}。需填入的字段：{content.count('{')}", "content": content}
        
        return {
            "template": title,
            "content": filled,
            "placeholders_count": content.count("{}") - len(defaults),
            "status": "generated"
        }


def register_template_tools(registry, data_dir):
    from opcclaw.core.tool_registry import ToolDefinition
    t = TemplateTools(data_dir)
    registry.add_tool(ToolDefinition(name="list_all_templates", description="列出所有可用的模板：邮件/合同/报价/通知等分类", parameters={"type":"object","properties":{}}, handler=lambda: t.list_all_templates()))
    registry.add_tool(ToolDefinition(name="generate_template", description="按模板名生成文档内容", parameters={"type":"object","properties":{"template_key":{"type":"string","enum":["invoice","delivery_notice","contract","price_quotation","meeting_minutes","customer_survey"]}}}, handler=lambda template_key="invoice": t.generate_template(template_key)))

