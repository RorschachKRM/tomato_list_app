# Tomato List

番茄钟 + 待办清单桌面应用。

## 技术栈

| 层级 | 技术 |
|------|------|
| 语言 | Python 3.9+ |
| GUI 框架 | tkinter（Python 内置） |
| UI 主题 | [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) 1.18（Flatly / Cosmo 等 Bootstrap 风格主题） |
| 打包工具 | [PyInstaller](https://pyinstaller.org) 6.x（`--onefile --windowed`） |
| 数据持久化 | JSON 文件（`%LOCALAPPDATA%\TomatoList\data.json`） |
| 安装包制作 | [Inno Setup](https://jrsoftware.org/isinfo.php)（`setup.iss`，可选） |

## 项目结构

```
tomato_list_app/
├── tomato_list.py          # 主程序源代码
├── setup.iss               # Inno Setup 安装包脚本（可选）
├── dist/
│   └── Tomato List.exe     # 打包后的可执行文件
└── README.md
```

## 开发

```bash
# 安装依赖
pip install ttkbootstrap pyinstaller

# 运行
python tomato_list.py

# 打包为 exe
pyinstaller --onefile --windowed --name "Tomato List" tomato_list.py
```

## 分发

- 直接发送 `dist/Tomato List.exe` 即可，免安装、双击运行
- 如需安装包，用 Inno Setup 编译 `setup.iss`

## 功能

- 番茄钟：专注 / 短休 / 长休 三种模式，可自定义时长
- 专注次数记录（按天重置）
- 待办清单：添加、勾选完成、删除、清空已完成
- 数据自动保存，启动恢复

## 卸载

应用为便携版，无安装痕迹、无注册表、无后台进程。彻底删除只需两步：

1. 删除 exe 文件
2. 删除数据目录 `%LOCALAPPDATA%\TomatoList\`

即打开文件资源管理器，地址栏输入 `%LOCALAPPDATA%`，找到 `TomatoList` 文件夹删除即可。
