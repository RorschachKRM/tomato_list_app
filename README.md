# Tomato List

番茄钟 + 待办清单桌面应用。

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Python](https://img.shields.io/badge/python-3.9+-blue)

## 功能

- **番茄钟** — 专注 / 短休 / 长休三种模式，时长可自定义
- **专注计数** — 每日专注次数记录，跨天自动清零
- **待办清单** — 添加、勾选完成、删除、清空已完成
- **数据持久化** — 自动保存至 `%LOCALAPPDATA%\TomatoList\data.json`，启动恢复
- **现代界面** — CustomTkinter，跟随系统明/暗模式，圆角卡片风格
- **快捷键** — `Space` 开始/暂停计时，`Ctrl+N` 聚焦输入框

## 技术栈

| 层级 | 技术 |
|---|---|
| 语言 | Python 3.9+ |
| GUI | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) 5.x |
| 打包 | [PyInstaller](https://pyinstaller.org) 6.x |
| 存储 | JSON 文件 |

## 项目结构

```
tomato_list_app/
├── tomato_list.py
├── Tomato List.spec          # PyInstaller 打包配置
├── dist/
│   └── Tomato List.exe       # 打包后的可执行文件
└── README.md
```

## 开发

```bash
# 安装依赖
pip install customtkinter pyinstaller

# 运行
python tomato_list.py

# 打包为 exe
pyinstaller "Tomato List.spec"
```

## 分发

直接发送 `dist/Tomato List.exe`，免安装、双击运行。无注册表、无后台进程。

## 卸载

1. 删除 exe 文件
2. 删除数据目录 `%LOCALAPPDATA%\TomatoList\`

## 更新日志

### V2

- 从 ttkbootstrap 迁移至 CustomTkinter
- 支持跟随系统明/暗模式
- 圆角卡片风格，更现代的视觉
- 字体优化（Trebuchet MS）

### V1

- 基于 ttkbootstrap 主题的初始版本
- 番茄钟 + 待办清单基础功能
