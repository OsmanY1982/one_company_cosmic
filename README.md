# 一人公司宇宙版

> 一个人也能运转的 AI 驱动企业管理系统

[![GitHub release](https://img.shields.io/github/v/release/OsmanY1982/one_company_cosmic?include_prereleases)](https://github.com/OsmanY1982/one_company_cosmic/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20arm64-lightgrey)](https://github.com/OsmanY1982/one_company_cosmic/releases)

## 简介

一人公司宇宙版是一套面向独立创业者和小微企业的桌面端管理工具，覆盖销售、采购、财务、人事、库存全流程，内置 AI 知识库、智能天象模拟、语音/图像识别、云端数据同步等高级能力。

**核心理念**：一个人 + 一套系统 = 一个公司。用 AI 把重复事务自动化，把精力留给创意和决策。

## 下载安装

| 渠道 | 链接 |
|------|------|
| **GitHub Release** | [下载 DMG](https://github.com/OsmanY1982/one_company_cosmic/releases/latest) |
| Gitee（国内镜像） | [前往下载](https://gitee.com/opc1688/one_company_cosmic/releases) |

> **系统要求**：macOS 14+、Apple Silicon（M1/M2/M3/M4）

安装步骤：
1. 下载 `OneCompanyCosmic-v*-arm64.dmg`
2. 双击打开，将「一人公司宇宙版.app」拖入 Applications 文件夹
3. 首次运行若提示"无法验证开发者"，前往 **系统设置 → 隐私与安全性 → 仍要打开**

## 功能模块

| 模块 | 说明 |
|------|------|
| 销售管理 | 客户、订单、报价、合同全流程 |
| 采购管理 | 供应商、采购单、入库、对账 |
| 财务管理 | 收支记账、发票管理、资金流水 |
| 人事管理 | 员工档案、考勤、薪资 |
| 库存管理 | 出入库、库存预警、盘点 |
| AI 知识库 | 文档上传、智能问答、规则引擎 |
| 太阳系探索 | 三维天象模拟可视化 |
| 云同步 | 基于 Supabase 的多端数据同步 |
| 语音/图像 | 语音指令、OCR 识别、二维码 |

## 技术栈

- **界面**：Python + PyQt5
- **数据库**：SQLite（本地）+ Supabase（云端）
- **AI**：本地语音识别（faster-whisper）、OCR（PIL/barcode）
- **打包**：PyInstaller → macOS .app + .dmg

## 参与开发

欢迎贡献代码、反馈问题、提交需求。

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/xxx`
3. 提交更改：`git commit -m "feat: xxx"`
4. 推送分支：`git push origin feature/xxx`
5. 提交 Pull Request

### 本地开发环境

```bash
git clone https://github.com/OsmanY1982/one_company_cosmic.git
cd one_company_cosmic
pip install -r requirements.txt
python main.py
```

## 赞助支持

如果这个项目对你有帮助，欢迎赞助支持开发维护。

[![Sponsor](https://img.shields.io/badge/Sponsor-❤️-ff69b4)](https://github.com/OsmanY1982)

| 方式 | 入口 |
|------|------|
| GitHub Sponsors | [点击赞助](https://github.com/sponsors/OsmanY1982) |
| 微信赞赏 | 请在 Issue 中留言获取赞赏码 |
| 支付宝 | 请在 Issue 中留言获取收款码 |

所有赞助者将列入 README 致谢名单。

## 开源协议

[MIT License](LICENSE)

---

**一人公司宇宙版** —— 一个人，也能星辰大海。
