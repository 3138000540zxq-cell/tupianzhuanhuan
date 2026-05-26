# 图片转换工具

一个基于 Tkinter 的桌面小工具，支持图片格式互转、图片合成 PDF、PDF 拆解为图片。

## 功能

- 图片格式互转：JPG、PNG、BMP、TIFF、WEBP、GIF、ICO。
- 支持 `.jpeg`、`.tiff` 等常见扩展名，图片列表可选择包含子文件夹。
- 自定义输出目录；包含子文件夹时会保留原目录层级。
- 可选择覆盖同名文件，或自动添加后缀避免重名。
- 图片合成 PDF，可按文件名排序并设置 DPI。
- PDF 拆解为 PNG/JPG，可设置 DPI 和页码范围，例如 `1-3,5,7-9`。

## 运行

```bash
pip install pillow pymupdf
python converter_v4_pro.py
```

Windows 下也可以运行启动器：

```bash
python launcher_converter_v4_pro.py
```

## 打包

项目已包含 PyInstaller 配置：

```bash
pip install pyinstaller pillow pymupdf
pyinstaller converter_v4_pro.spec
```
