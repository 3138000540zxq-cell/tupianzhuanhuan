import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
from pathlib import Path
import fitz  # PyMuPDF，用于处理PDF读取

# --- 定义图片支持格式 ---
SUPPORTED_FORMATS = {
    "JPG": ".jpg", "PNG": ".png", "BMP": ".bmp", "TIFF": ".tif",
    "WEBP": ".webp", "GIF": ".gif", "ICO": ".ico"
}

class UniversalConverterApp:
    def __init__(self, root):
        self.root = root
        # --- 这里修改了软件名称 ---
        self.root.title("全能格式工厂 (图片 + PDF) ZXQ") 
        self.root.geometry("750x650")

        # 创建选项卡控件 (Notebook)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        # --- 选项卡 1：图片互转 ---
        self.tab_img = tk.Frame(self.notebook)
        self.notebook.add(self.tab_img, text="🖼️ 图片互转")
        self.init_image_tab()

        # --- 选项卡 2：PDF 工具箱 ---
        self.tab_pdf = tk.Frame(self.notebook)
        self.notebook.add(self.tab_pdf, text="📄 PDF 工具箱")
        self.init_pdf_tab()

    # ============================================================
    # 模块 1：图片互转功能
    # ============================================================
    def init_image_tab(self):
        # 1. 顶部
        top_frame = tk.LabelFrame(self.tab_img, text="1. 选择来源", padx=10, pady=10)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(top_frame, text="打开图片文件夹", command=self.select_img_folder).pack(side="left")
        self.lbl_img_path = tk.Label(top_frame, text="未选择", fg="gray")
        self.lbl_img_path.pack(side="left", padx=10)

        # 2. 列表
        list_frame = tk.Frame(self.tab_img)
        list_frame.pack(expand=True, fill="both", padx=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.img_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, yscrollcommand=scrollbar.set, font=("Consolas", 10))
        self.img_listbox.pack(side="left", expand=True, fill="both")
        scrollbar.config(command=self.img_listbox.yview)

        list_actions = tk.Frame(self.tab_img)
        list_actions.pack(fill="x", padx=10, pady=5)
        tk.Button(list_actions, text="全选", command=self.select_all_images, width=8).pack(side="left")
        tk.Button(list_actions, text="清空选择", command=self.clear_image_selection, width=10).pack(side="left", padx=5)
        tk.Button(list_actions, text="刷新列表", command=self.refresh_img_list, width=10).pack(side="left")

        # 3. 转换设置
        bottom_frame = tk.LabelFrame(self.tab_img, text="2. 转换设置", padx=10, pady=10)
        bottom_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(bottom_frame, text="转为:").grid(row=0, column=0, sticky="w")
        self.img_target_combo = ttk.Combobox(bottom_frame, values=list(SUPPORTED_FORMATS.keys()), state="readonly", width=8)
        self.img_target_combo.current(1) # 默认PNG
        self.img_target_combo.grid(row=0, column=1, sticky="w", padx=5)

        tk.Label(bottom_frame, text="质量(1-100):").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.img_quality_var = tk.StringVar(value="100")
        self.img_quality_spin = tk.Spinbox(bottom_frame, from_=1, to=100, width=6, textvariable=self.img_quality_var)
        self.img_quality_spin.grid(row=1, column=1, sticky="w", padx=5, pady=(6, 0))

        self.img_overwrite_var = tk.BooleanVar(value=True)
        self.img_overwrite_chk = tk.Checkbutton(bottom_frame, text="覆盖同名文件", variable=self.img_overwrite_var)
        self.img_overwrite_chk.grid(row=0, column=2, sticky="w", padx=(20, 0))

        tk.Label(bottom_frame, text="不覆盖时后缀:").grid(row=1, column=2, sticky="w", padx=(20, 0), pady=(6, 0))
        self.img_suffix_var = tk.StringVar(value="_converted")
        self.img_suffix_entry = tk.Entry(bottom_frame, width=12, textvariable=self.img_suffix_var)
        self.img_suffix_entry.grid(row=1, column=3, sticky="w", padx=5, pady=(6, 0))

        # 4. 输出设置
        output_frame = tk.LabelFrame(self.tab_img, text="3. 输出设置", padx=10, pady=10)
        output_frame.pack(fill="x", padx=10, pady=5)
        self.img_output_mode = tk.StringVar(value="same")
        tk.Radiobutton(output_frame, text="原目录", variable=self.img_output_mode, value="same", command=self.toggle_img_output).pack(side="left")
        tk.Radiobutton(output_frame, text="自定义目录", variable=self.img_output_mode, value="custom", command=self.toggle_img_output).pack(side="left", padx=10)
        self.img_output_path_var = tk.StringVar()
        self.img_output_entry = tk.Entry(output_frame, textvariable=self.img_output_path_var, width=35, state="disabled")
        self.img_output_entry.pack(side="left", padx=5)
        self.img_output_btn = tk.Button(output_frame, text="选择目录", command=self.select_img_output_folder, state="disabled")
        self.img_output_btn.pack(side="left")

        # 5. 执行与进度
        action_frame = tk.Frame(self.tab_img)
        action_frame.pack(fill="x", padx=10, pady=10)
        tk.Button(action_frame, text="开始转换", command=self.run_img_convert, bg="#4CAF50", fg="white").pack(side="right")
        self.img_status_var = tk.StringVar(value="等待操作")
        tk.Label(action_frame, textvariable=self.img_status_var, fg="blue").pack(side="left")
        self.img_progress = ttk.Progressbar(self.tab_img, mode="determinate")
        self.img_progress.pack(fill="x", padx=10, pady=(0, 10))

        self.img_current_folder = None
        self.img_files_map = [] # 存储 (文件名, 完整路径)

    def select_img_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.img_current_folder = Path(folder)
            self.lbl_img_path.config(text=f".../{self.img_current_folder.name}")
            self.refresh_img_list()

    def refresh_img_list(self):
        self.img_listbox.delete(0, tk.END)
        self.img_files_map = []
        
        # 扫描所有支持的图片
        if not self.img_current_folder:
            return
        for f in self.img_current_folder.iterdir():
            if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS.values():
                self.img_files_map.append(f)
                self.img_listbox.insert(tk.END, f.name)

    def select_all_images(self):
        if self.img_listbox.size() > 0:
            self.img_listbox.select_set(0, tk.END)

    def clear_image_selection(self):
        self.img_listbox.selection_clear(0, tk.END)

    def toggle_img_output(self):
        is_custom = self.img_output_mode.get() == "custom"
        state = "normal" if is_custom else "disabled"
        self.img_output_entry.config(state=state)
        self.img_output_btn.config(state=state)

    def select_img_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.img_output_path_var.set(folder)

    def get_img_output_dir(self):
        if self.img_output_mode.get() == "same":
            return self.img_current_folder
        custom = self.img_output_path_var.get().strip()
        if not custom:
            return None
        return Path(custom)

    def run_img_convert(self):
        indices = self.img_listbox.curselection()
        if not indices:
            messagebox.showwarning("提示", "请先选择图片")
            return
        output_dir = self.get_img_output_dir()
        if not output_dir:
            messagebox.showwarning("提示", "请先选择输出目录")
            return
        output_dir.mkdir(parents=True, exist_ok=True)

        target_ext = SUPPORTED_FORMATS[self.img_target_combo.get()]
        target_fmt = self.img_target_combo.get()
        success = 0
        failed = 0
        self.img_progress["maximum"] = len(indices)
        self.img_progress["value"] = 0
        self.img_status_var.set("正在转换...")

        try:
            quality = int(self.img_quality_var.get().strip())
            if quality < 1 or quality > 100:
                raise ValueError
        except ValueError:
            messagebox.showwarning("提示", "质量必须是 1-100 的整数")
            return
        
        for step, index in enumerate(indices, start=1):
            src = self.img_files_map[index]
            if self.img_overwrite_var.get():
                dst = output_dir / f"{src.stem}{target_ext}"
            else:
                suffix = self.img_suffix_var.get().strip() or "_converted"
                dst = output_dir / f"{src.stem}{suffix}{target_ext}"
            try:
                with Image.open(src) as img:
                    if target_fmt in ("JPG", "BMP"):
                        if img.mode != "RGB":
                            img = img.convert("RGB")
                    save_kwargs = {}
                    if target_fmt in ("JPG", "WEBP"):
                        save_kwargs["quality"] = quality
                    img.save(dst, **save_kwargs)
                    success += 1
            except Exception as e:
                failed += 1
                print(e)
            self.img_progress["value"] = step
            self.root.update_idletasks()
        
        self.img_status_var.set("转换完成")
        messagebox.showinfo("完成", f"成功转换 {success} 张图片，失败 {failed} 张")

    # ============================================================
    # 模块 2：PDF 工具箱
    # ============================================================
    def init_pdf_tab(self):
        # 功能 A: 图片合成 PDF
        frame_a = tk.LabelFrame(self.tab_pdf, text="功能 A: 多张图片合成一个 PDF", padx=10, pady=10)
        frame_a.pack(fill="x", padx=10, pady=10)

        tk.Label(frame_a, text="1. 点击按钮选择多张图片 -> 2. 输入PDF文件名 -> 3. 完成").pack(anchor="w")
        opts_a = tk.Frame(frame_a)
        opts_a.pack(fill="x", pady=5)
        self.pdf_sort_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opts_a, text="按文件名排序", variable=self.pdf_sort_var).pack(side="left")
        tk.Label(opts_a, text="分辨率(DPI):").pack(side="left", padx=(20, 0))
        self.pdf_dpi_var = tk.StringVar(value="600")
        tk.Spinbox(opts_a, from_=72, to=600, width=6, textvariable=self.pdf_dpi_var).pack(side="left", padx=5)
        tk.Button(frame_a, text="选择图片并合并为 PDF...", command=self.images_to_pdf, height=2, bg="#e1e1e1").pack(fill="x", pady=5)

        # 功能 B: PDF 拆解为图片
        frame_b = tk.LabelFrame(self.tab_pdf, text="功能 B: PDF 拆解为图片 (每一页转为一张图)", padx=10, pady=10)
        frame_b.pack(fill="x", padx=10, pady=10)

        tk.Label(frame_b, text="1. 点击按钮选择一个PDF文件 -> 2. 按设置导出图片").pack(anchor="w")
        opts_b = tk.Frame(frame_b)
        opts_b.pack(fill="x", pady=5)
        tk.Label(opts_b, text="输出格式:").pack(side="left")
        self.pdf_img_fmt = ttk.Combobox(opts_b, values=["PNG", "JPG"], state="readonly", width=6)
        self.pdf_img_fmt.current(0)
        self.pdf_img_fmt.pack(side="left", padx=5)
        tk.Label(opts_b, text="DPI:").pack(side="left", padx=(20, 0))
        self.pdf_img_dpi_var = tk.StringVar(value="600")
        tk.Spinbox(opts_b, from_=72, to=600, width=6, textvariable=self.pdf_img_dpi_var).pack(side="left", padx=5)
        tk.Label(opts_b, text="页码范围:").pack(side="left", padx=(20, 0))
        self.pdf_range_var = tk.StringVar(value="")
        tk.Entry(opts_b, width=18, textvariable=self.pdf_range_var).pack(side="left", padx=5)

        out_b = tk.Frame(frame_b)
        out_b.pack(fill="x", pady=5)
        tk.Label(out_b, text="输出目录(可选):").pack(side="left")
        self.pdf_out_var = tk.StringVar(value="")
        tk.Entry(out_b, textvariable=self.pdf_out_var, width=35).pack(side="left", padx=5)
        tk.Button(out_b, text="选择目录", command=self.select_pdf_output_folder).pack(side="left")

        tk.Button(frame_b, text="选择 PDF 并拆解...", command=self.pdf_to_images, height=2, bg="#e1e1e1").pack(fill="x", pady=5)

        self.pdf_status = tk.Label(self.tab_pdf, text="PDF工具准备就绪", fg="blue")
        self.pdf_status.pack(pady=10)
        self.pdf_progress = ttk.Progressbar(self.tab_pdf, mode="determinate")
        self.pdf_progress.pack(fill="x", padx=10, pady=(0, 10))

    def images_to_pdf(self):
        # 1. 多选图片
        file_paths = filedialog.askopenfilenames(
            title="选择要合并的图片 (按住Ctrl多选)",
            filetypes=[("Image Files", "*.jpg;*.png;*.bmp;*.tif")]
        )
        if not file_paths: return
        if self.pdf_sort_var.get():
            file_paths = sorted(file_paths, key=lambda p: Path(p).name.lower())

        # 2. 询问保存路径
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")],
            title="保存 PDF 为..."
        )
        if not save_path: return

        try:
            try:
                dpi = int(self.pdf_dpi_var.get().strip())
                if dpi < 72 or dpi > 600:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("提示", "DPI 必须是 72-600 的整数")
                return

            # 核心逻辑：Pillow 列表保存
            img_list = []
            first_img = None
            
            for p in file_paths:
                img = Image.open(p)
                if img.mode != 'RGB': img = img.convert('RGB')
                
                if first_img is None:
                    first_img = img
                else:
                    img_list.append(img)
            
            if first_img:
                first_img.save(save_path, "PDF", resolution=float(dpi), save_all=True, append_images=img_list)
                messagebox.showinfo("成功", f"PDF 已生成！\n路径: {save_path}")
            
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def pdf_to_images(self):
        # 1. 选择 PDF
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not pdf_path: return

        pdf_path = Path(pdf_path)
        custom_out = self.pdf_out_var.get().strip()
        output_folder = Path(custom_out) if custom_out else (pdf_path.parent / f"{pdf_path.stem}_images")
        output_folder.mkdir(parents=True, exist_ok=True)

        self.pdf_status.config(text="正在拆解 PDF...")
        self.root.update()

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            try:
                page_indices = self.parse_page_range(self.pdf_range_var.get(), total_pages)
            except ValueError:
                messagebox.showwarning("提示", "页码范围格式错误，例如: 1-3,5,7-9")
                return
            if not page_indices:
                messagebox.showwarning("提示", "未匹配到可导出的页码")
                return
            try:
                dpi = int(self.pdf_img_dpi_var.get().strip())
                if dpi < 72 or dpi > 600:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("提示", "DPI 必须是 72-600 的整数")
                return

            scale = dpi / 72.0
            matrix = fitz.Matrix(scale, scale)
            out_fmt = self.pdf_img_fmt.get()
            ext = ".png" if out_fmt == "PNG" else ".jpg"
            self.pdf_progress["maximum"] = len(page_indices)
            self.pdf_progress["value"] = 0

            for idx, page_no in enumerate(page_indices, start=1):
                page = doc.load_page(page_no)
                pix = page.get_pixmap(matrix=matrix)
                if out_fmt == "JPG" and pix.alpha:
                    pix = fitz.Pixmap(pix, 0)
                output_file = output_folder / f"page_{page_no+1:03d}{ext}"
                pix.save(str(output_file))
                
                self.pdf_status.config(text=f"正在导出第 {page_no+1} 页...")
                self.pdf_progress["value"] = idx
                self.root.update_idletasks()

            messagebox.showinfo("成功", f"拆解完成！\n图片保存在文件夹:\n{output_folder}")
            self.pdf_status.config(text="PDF工具准备就绪")
            
        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.pdf_status.config(text="发生错误")
        finally:
            self.pdf_progress["value"] = 0

    def select_pdf_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.pdf_out_var.set(folder)

    def parse_page_range(self, text, total_pages):
        text = (text or "").strip()
        if not text:
            return list(range(total_pages))

        pages = set()
        parts = re.split(r"[，,]+", text)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                left, right = part.split("-", 1)
                left = left.strip()
                right = right.strip()
                start = int(left) if left else 1
                end = int(right) if right else total_pages
                if start > end:
                    start, end = end, start
                for p in range(start, end + 1):
                    pages.add(p)
            else:
                pages.add(int(part))

        valid = [p for p in pages if 1 <= p <= total_pages]
        return sorted([p - 1 for p in valid])

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalConverterApp(root)
    root.mainloop()
