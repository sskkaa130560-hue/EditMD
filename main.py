"""
EditMD — Markdown Editor
Desktop application for creating, viewing and editing Markdown files.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import markdown
from tkinterweb import HtmlFrame
import re


# ─── Color themes ──────────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "bg": "#1e1e2e",
        "fg": "#cdd6f4",
        "sidebar_bg": "#181825",
        "sidebar_fg": "#bac2de",
        "editor_bg": "#1e1e2e",
        "editor_fg": "#cdd6f4",
        "menu_bg": "#313244",
        "menu_fg": "#cdd6f4",
        "accent": "#89b4fa",
        "accent2": "#a6e3a1",
        "border": "#45475a",
        "select_bg": "#45475a",
        "line_num_bg": "#181825",
        "line_num_fg": "#6c7086",
        "status_bg": "#313244",
        "status_fg": "#a6adc8",
        "tree_select": "#45475a",
        "insert_bg": "#f5e0dc",
    },
    "light": {
        "bg": "#eff1f5",
        "fg": "#4c4f69",
        "sidebar_bg": "#e6e9ef",
        "sidebar_fg": "#4c4f69",
        "editor_bg": "#eff1f5",
        "editor_fg": "#4c4f69",
        "menu_bg": "#ccd0da",
        "menu_fg": "#4c4f69",
        "accent": "#1e66f5",
        "accent2": "#40a02b",
        "border": "#bcc0cc",
        "select_bg": "#bcc0cc",
        "line_num_bg": "#e6e9ef",
        "line_num_fg": "#9ca0b0",
        "status_bg": "#ccd0da",
        "status_fg": "#5c5f77",
        "tree_select": "#bcc0cc",
        "insert_bg": "#dc8a78",
    },
}


# ─── Markdown syntax patterns ──────────────────────────────────────────────────
MD_PATTERNS = [
    ("header1",    r"^#{1}\s.*$",          "bold",    18),
    ("header2",    r"^#{2}\s.*$",          "bold",    16),
    ("header3",    r"^#{3}\s.*$",          "bold",    14),
    ("header4",    r"^#{4,6}\s.*$",        "bold",    12),
    ("bold",       r"\*\*[^*]+\*\*",       "bold",    None),
    ("italic",     r"(?<!\*)\*[^*]+\*(?!\*)", "italic", None),
    ("code_block", r"^```.*$",             "mono",    None),
    ("inline_code",r"`[^`]+`",            "mono",    None),
    ("link",       r"\[.+?\]\(.+?\)",     "underline", None),
    ("list_item",  r"^\s*[-*+]\s.*$",     "normal",   None),
    ("blockquote", r"^>\s.*$",            "italic",   None),
    ("hr",         r"^[-*_]{3,}$",        "normal",   None),
]


class LineNumbers(tk.Canvas):
    """Line numbers gutter for the text editor."""

    def __init__(self, parent, text_widget, theme, **kwargs):
        super().__init__(parent, width=50, highlightthickness=0, **kwargs)
        self.text_widget = text_widget
        self.theme = theme
        self._apply_theme()
        self.bind("<Button-1>", self._on_click)

    def attach(self, text_widget):
        """Bind to a text widget after it's been created."""
        self.text_widget = text_widget
        self.text_widget.bind("<<Change>>", self._redraw)
        self.text_widget.bind("<Configure>", self._redraw)

    def _apply_theme(self):
        t = THEMES[self.theme]
        self.configure(bg=t["line_num_bg"])

    def _redraw(self, event=None):
        self.delete("all")
        t = THEMES[self.theme]
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = int(str(i).split(".")[0])
            self.create_text(
                45, y, anchor="ne", text=str(linenum),
                font=("Consolas", 10), fill=t["line_num_fg"]
            )
            i = self.text_widget.index(f"{i}+1line")

    def _on_click(self, event):
        idx = self.text_widget.index(f"@0,{event.y}")
        line = int(str(idx).split(".")[0])
        self.text_widget.mark_set("insert", f"{line}.0")
        self.text_widget.focus_set()


class MarkdownEditor(tk.Frame):
    """Text editor widget with Markdown syntax highlighting."""

    def __init__(self, parent, theme="dark", on_change=None):
        super().__init__(parent)
        self.theme = theme
        self.on_change = on_change
        self._build_ui()
        self._setup_tags()
        self._bind_events()

    def _build_ui(self):
        t = THEMES[self.theme]

        self.line_numbers = LineNumbers(self, None, self.theme)
        self.line_numbers.pack(side="left", fill="y")

        self.text = tk.Text(
            self,
            wrap="word",
            undo=True,
            maxundo=-1,
            font=("Consolas", 12),
            bg=t["editor_bg"],
            fg=t["editor_fg"],
            insertbackground=t["insert_bg"],
            selectbackground=t["select_bg"],
            selectforeground=t["fg"],
            relief="flat",
            padx=10,
            pady=10,
            spacing1=2,
            spacing3=2,
        )
        self.line_numbers.text_widget = self.text
        self.line_numbers.attach(self.text)

        self.scrollbar = ttk.Scrollbar(self, command=self.text.yview)
        self.text.configure(yscrollcommand=self._on_scroll)

        self.scrollbar.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

    def _on_scroll(self, *args):
        self.scrollbar.set(*args)
        self.line_numbers._redraw()

    def _setup_tags(self):
        t = THEMES[self.theme]
        self.text.tag_configure("header1", font=("Consolas", 18, "bold"), foreground=t["accent"])
        self.text.tag_configure("header2", font=("Consolas", 16, "bold"), foreground=t["accent"])
        self.text.tag_configure("header3", font=("Consolas", 14, "bold"), foreground=t["accent"])
        self.text.tag_configure("header4", font=("Consolas", 12, "bold"), foreground=t["accent"])
        self.text.tag_configure("bold", font=("Consolas", 12, "bold"), foreground=t["fg"])
        self.text.tag_configure("italic", font=("Consolas", 12, "italic"), foreground=t["fg"])
        self.text.tag_configure("mono", font=("Consolas", 11), foreground=t["accent2"],
                                background=t["sidebar_bg"])
        self.text.tag_configure("underline", foreground=t["accent"], underline=True)
        self.text.tag_configure("normal", foreground=t["fg"])
        self.text.tag_configure("code_block", font=("Consolas", 11), foreground=t["accent2"],
                                background=t["sidebar_bg"])

    def _bind_events(self):
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<ButtonRelease-1>", self._on_click)
        self.text.bind("<MouseWheel>", self._on_mousewheel)
        self.text.bind("<Tab>", self._on_tab)
        # Explicit clipboard bindings to ensure Ctrl+C/V/X work
        self.text.bind("<Control-v>", self._paste)
        self.text.bind("<Control-V>", self._paste)
        self.text.bind("<Control-c>", self._copy)
        self.text.bind("<Control-C>", self._copy)
        self.text.bind("<Control-x>", self._cut)
        self.text.bind("<Control-X>", self._cut)

    def _paste(self, event=None):
        try:
            clipboard = self.text.clipboard_get()
            try:
                self.text.delete("sel.first", "sel.last")
            except tk.TclError:
                pass
            self.text.insert("insert", clipboard)
            self.text.see("insert")
        except tk.TclError:
            pass
        return "break"

    def _copy(self, event=None):
        try:
            sel = self.text.get("sel.first", "sel.last")
            self.text.clipboard_clear()
            self.text.clipboard_append(sel)
        except tk.TclError:
            pass
        return "break"

    def _cut(self, event=None):
        try:
            sel = self.text.get("sel.first", "sel.last")
            self.text.clipboard_clear()
            self.text.clipboard_append(sel)
            self.text.delete("sel.first", "sel.last")
        except tk.TclError:
            pass
        return "break"

    def _on_tab(self, event):
        self.text.insert("insert", "    ")
        return "break"

    def _on_mousewheel(self, event):
        self.line_numbers._redraw()

    def _on_click(self, event=None):
        self.line_numbers._redraw()

    def _on_key_release(self, event=None):
        self._highlight_syntax()
        self.line_numbers._redraw()
        if self.on_change:
            self.on_change()

    def _highlight_syntax(self):
        """Apply syntax highlighting tags to the text content."""
        # Remove all existing tags
        for tag_name, _, _, _ in MD_PATTERNS:
            self.text.tag_remove(tag_name, "1.0", "end")

        content = self.text.get("1.0", "end-1c")
        lines = content.split("\n")

        in_code_block = False
        for line_idx, line in enumerate(lines):
            line_start = f"{line_idx + 1}.0"
            line_end = f"{line_idx + 1}.{len(line)}"

            # Code block toggle
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                self.text.tag_add("code_block", line_start, line_end)
                continue

            if in_code_block:
                self.text.tag_add("code_block", line_start, line_end)
                continue

            # Apply patterns
            for tag_name, pattern, _, _ in MD_PATTERNS:
                if tag_name == "code_block":
                    continue
                for match in re.finditer(pattern, line, re.MULTILINE):
                    start = f"{line_idx + 1}.{match.start()}"
                    end = f"{line_idx + 1}.{match.end()}"
                    self.text.tag_add(tag_name, start, end)

    def get_content(self):
        return self.text.get("1.0", "end-1c")

    def set_content(self, text):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self._highlight_syntax()
        self.line_numbers._redraw()

    def clear(self):
        self.text.delete("1.0", "end")
        self._highlight_syntax()

    def apply_theme(self, theme):
        self.theme = theme
        t = THEMES[theme]
        self.text.configure(
            bg=t["editor_bg"], fg=t["editor_fg"],
            insertbackground=t["insert_bg"],
            selectbackground=t["select_bg"],
        )
        self.line_numbers.theme = theme
        self.line_numbers._apply_theme()
        self._setup_tags()
        self._highlight_syntax()

    def get_cursor_pos(self):
        idx = self.text.index("insert")
        parts = idx.split(".")
        return int(parts[0]), int(parts[1])

    def get_word_count(self):
        content = self.get_content().strip()
        if not content:
            return 0
        return len(content.split())

    def get_char_count(self):
        return len(self.get_content())


class FileTree(tk.Frame):
    """File tree sidebar for navigating directories."""

    def __init__(self, parent, theme="dark", on_file_select=None):
        super().__init__(parent)
        self.theme = theme
        self.on_file_select = on_file_select
        self.current_dir = os.path.expanduser("~")
        self._build_ui()

    def _build_ui(self):
        t = THEMES[self.theme]

        # Header
        self.header = tk.Frame(self, bg=t["sidebar_bg"])
        self.header.pack(fill="x")

        self.dir_label = tk.Label(
            self.header, text="📁 Files", font=("Segoe UI", 10, "bold"),
            bg=t["sidebar_bg"], fg=t["sidebar_fg"], padx=8, pady=6, anchor="w"
        )
        self.dir_label.pack(side="left", fill="x", expand=True)

        self.browse_btn = tk.Button(
            self.header, text="📂", font=("Segoe UI", 9),
            bg=t["sidebar_bg"], fg=t["sidebar_fg"], relief="flat",
            command=self._browse_dir, cursor="hand2"
        )
        self.browse_btn.pack(side="right", padx=4)

        # Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "FileTree.Treeview",
            background=t["sidebar_bg"],
            foreground=t["sidebar_fg"],
            fieldbackground=t["sidebar_bg"],
            font=("Segoe UI", 10),
            rowheight=26,
        )
        style.configure(
            "FileTree.Treeview.Heading",
            background=t["menu_bg"],
            foreground=t["menu_fg"],
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "FileTree.Treeview",
            background=[("selected", t["tree_select"])],
            foreground=[("selected", t["accent"])],
        )

        self.tree = ttk.Treeview(self, style="FileTree.Treeview", show="tree")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)

        scrollbar = ttk.Scrollbar(self, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.load_directory(self.current_dir)

    def load_directory(self, path):
        self.current_dir = path
        self.tree.delete(*self.tree.get_children())
        t = THEMES[self.theme]
        self.dir_label.configure(text=f"📁 {os.path.basename(path) or path}")

        try:
            items = sorted(os.listdir(path), key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
        except PermissionError:
            return

        # Parent directory
        if os.path.dirname(path) != path:
            self.tree.insert("", "end", text="..  (up)", values=(os.path.dirname(path), "dir"),
                             open=False)

        for item in items:
            full = os.path.join(path, item)
            if item.startswith("."):
                continue
            if os.path.isdir(full):
                node = self.tree.insert("", "end", text=f"📁 {item}", values=(full, "dir"))
                # Add dummy child for lazy loading
                self.tree.insert(node, "end", text="loading...")
                self.tree.bind("<<TreeviewOpen>>", self._on_open_folder)
            elif item.lower().endswith((".md", ".markdown", ".txt", ".mdown")):
                icon = "📝" if item.lower().endswith((".md", ".markdown", ".mdown")) else "📄"
                self.tree.insert("", "end", text=f"{icon} {item}", values=(full, "file"))

    def _on_open_folder(self, event):
        item = self.tree.focus()
        children = self.tree.get_children(item)
        if len(children) == 1:
            text = self.tree.item(children[0], "text")
            if text == "loading...":
                self.tree.delete(children[0])
                path = self.tree.item(item, "values")[0]
                try:
                    sub_items = sorted(os.listdir(path),
                                      key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
                except PermissionError:
                    return
                for sub in sub_items:
                    full = os.path.join(path, sub)
                    if sub.startswith("."):
                        continue
                    if os.path.isdir(full):
                        node = self.tree.insert(item, "end", text=f"📁 {sub}", values=(full, "dir"))
                        self.tree.insert(node, "end", text="loading...")
                    elif sub.lower().endswith((".md", ".markdown", ".txt", ".mdown")):
                        icon = "📝" if sub.lower().endswith((".md", ".markdown", ".mdown")) else "📄"
                        self.tree.insert(item, "end", text=f"{icon} {sub}", values=(full, "file"))

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        values = self.tree.item(item, "values")
        if values and values[1] == "file" and self.on_file_select:
            self.on_file_select(values[0])

    def _on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        values = self.tree.item(item, "values")
        if values and values[1] == "dir":
            self.load_directory(values[0])

    def _browse_dir(self):
        path = filedialog.askdirectory(initialdir=self.current_dir)
        if path:
            self.load_directory(path)

    def apply_theme(self, theme):
        self.theme = theme
        t = THEMES[theme]
        self.header.configure(bg=t["sidebar_bg"])
        self.dir_label.configure(bg=t["sidebar_bg"], fg=t["sidebar_fg"])
        self.browse_btn.configure(bg=t["sidebar_bg"], fg=t["sidebar_fg"])
        style = ttk.Style()
        style.configure(
            "FileTree.Treeview",
            background=t["sidebar_bg"],
            foreground=t["sidebar_fg"],
            fieldbackground=t["sidebar_bg"],
        )
        style.map(
            "FileTree.Treeview",
            background=[("selected", t["tree_select"])],
            foreground=[("selected", t["accent"])],
        )


class PreviewPane(tk.Frame):
    """HTML preview pane for rendered Markdown."""

    def __init__(self, parent, theme="dark"):
        super().__init__(parent)
        self.theme = theme
        self._build_ui()

    def _build_ui(self):
        t = THEMES[self.theme]

        self.header = tk.Label(
            self, text="👁 Preview", font=("Segoe UI", 10, "bold"),
            bg=t["sidebar_bg"], fg=t["sidebar_fg"], padx=8, pady=6, anchor="w"
        )
        self.header.pack(fill="x")

        self.html = HtmlFrame(self, messages_enabled=False)
        self.html.pack(fill="both", expand=True)
        self._update_bg()

    def _update_bg(self):
        t = THEMES[self.theme]
        try:
            self.html.load_html(self._wrap_html(""))
        except Exception:
            pass

    def _wrap_html(self, body_html):
        t = THEMES[self.theme]
        bg = t["editor_bg"]
        fg = t["editor_fg"]
        accent = t["accent"]
        accent2 = t["accent2"]
        code_bg = t["sidebar_bg"]
        border = t["border"]
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Segoe UI', -apple-system, sans-serif;
    font-size: 14px; line-height: 1.7;
    color: {fg}; background: {bg};
    padding: 20px 24px;
    word-wrap: break-word;
}}
h1, h2, h3, h4, h5, h6 {{
    color: {accent}; margin: 18px 0 8px 0; font-weight: 600;
    border-bottom: 1px solid {border}; padding-bottom: 4px;
}}
h1 {{ font-size: 26px; }} h2 {{ font-size: 22px; }} h3 {{ font-size: 18px; }}
p {{ margin: 8px 0; }}
a {{ color: {accent}; text-decoration: underline; }}
code {{
    font-family: 'Consolas', 'Fira Code', monospace;
    background: {code_bg}; padding: 2px 6px; border-radius: 4px;
    font-size: 13px; color: {accent2};
}}
pre {{
    background: {code_bg}; padding: 14px; border-radius: 6px;
    overflow-x: auto; margin: 12px 0; border: 1px solid {border};
}}
pre code {{ background: none; padding: 0; color: {accent2}; }}
blockquote {{
    border-left: 4px solid {accent}; padding: 8px 16px;
    margin: 12px 0; background: {code_bg}; border-radius: 0 6px 6px 0;
    color: {fg};
}}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
th, td {{ border: 1px solid {border}; padding: 8px 12px; text-align: left; }}
th {{ background: {code_bg}; font-weight: 600; }}
ul, ol {{ padding-left: 28px; margin: 8px 0; }}
li {{ margin: 4px 0; }}
hr {{ border: none; border-top: 2px solid {border}; margin: 20px 0; }}
img {{ max-width: 100%; border-radius: 6px; }}
</style>
</head>
<body>{body_html}</body>
</html>"""

    def update_preview(self, md_text):
        extensions = [
            "markdown.extensions.tables",
            "markdown.extensions.fenced_code",
            "markdown.extensions.codehilite",
            "markdown.extensions.toc",
            "markdown.extensions.nl2br",
        ]
        try:
            html = markdown.markdown(md_text, extensions=extensions)
        except Exception as e:
            html = f"<p style='color:red;'>Error: {e}</p>"
        self.html.load_html(self._wrap_html(html))

    def apply_theme(self, theme):
        self.theme = theme
        t = THEMES[theme]
        self.header.configure(bg=t["sidebar_bg"], fg=t["sidebar_fg"])


# ─── Main Application ──────────────────────────────────────────────────────────
class EditMDApp:
    """Main application window."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EditMD — Markdown Editor")
        self.root.geometry("1400x850")
        self.root.minsize(800, 500)

        self.current_file = None
        self.theme = "dark"
        self.show_preview = True
        self._modified = False

        self._build_menu()
        self._build_ui()
        self._build_statusbar()
        self._bind_shortcuts()

        # Load file from command line argument
        import sys
        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            self._open_file(sys.argv[1])

        # Periodic status update
        self._update_status()

    # ── Menu ────────────────────────────────────────────────────────────────
    def _build_menu(self):
        t = THEMES[self.theme]
        menubar = tk.Menu(self.root, bg=t["menu_bg"], fg=t["menu_fg"],
                          activebackground=t["accent"], activeforeground=t["bg"],
                          relief="flat")

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=t["menu_bg"], fg=t["menu_fg"],
                            activebackground=t["accent"], activeforeground=t["bg"])
        file_menu.add_command(label="  New               Ctrl+N", command=self._new_file)
        file_menu.add_command(label="  Open              Ctrl+O", command=self._open_file_dialog)
        file_menu.add_command(label="  Save              Ctrl+S", command=self._save_file)
        file_menu.add_command(label="  Save As       Ctrl+Shift+S", command=self._save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="  Export HTML    Ctrl+E", command=self._export_html)
        file_menu.add_separator()
        file_menu.add_command(label="  Exit              Alt+F4", command=self._on_close)
        menubar.add_cascade(label=" File ", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0, bg=t["menu_bg"], fg=t["menu_fg"],
                            activebackground=t["accent"], activeforeground=t["bg"])
        edit_menu.add_command(label="  Undo              Ctrl+Z", command=lambda: self.editor.text.edit_undo())
        edit_menu.add_command(label="  Redo              Ctrl+Y", command=lambda: self.editor.text.edit_redo())
        edit_menu.add_separator()
        edit_menu.add_command(label="  Cut                 Ctrl+X", command=lambda: self.editor.text.event_generate("<<Cut>>"))
        edit_menu.add_command(label="  Copy              Ctrl+C", command=lambda: self.editor.text.event_generate("<<Copy>>"))
        edit_menu.add_command(label="  Paste              Ctrl+V", command=lambda: self.editor.text.event_generate("<<Paste>>"))
        edit_menu.add_separator()
        edit_menu.add_command(label="  Select All       Ctrl+A", command=self._select_all)
        edit_menu.add_command(label="  Find              Ctrl+F", command=self._find_dialog)
        edit_menu.add_separator()

        # Insert submenu
        insert_menu = tk.Menu(edit_menu, tearoff=0, bg=t["menu_bg"], fg=t["menu_fg"],
                              activebackground=t["accent"], activeforeground=t["bg"])
        insert_menu.add_command(label="  Bold            Ctrl+B", command=lambda: self._wrap_selection("**", "**"))
        insert_menu.add_command(label="  Italic           Ctrl+I", command=lambda: self._wrap_selection("*", "*"))
        insert_menu.add_command(label="  Code             Ctrl+`", command=lambda: self._wrap_selection("`", "`"))
        insert_menu.add_command(label="  Link              Ctrl+K", command=self._insert_link)
        insert_menu.add_command(label="  Image", command=self._insert_image)
        insert_menu.add_command(label="  Table", command=self._insert_table)
        insert_menu.add_command(label="  Horizontal Rule", command=lambda: self._insert_text("\n---\n"))
        edit_menu.add_cascade(label="  Insert", menu=insert_menu)
        menubar.add_cascade(label=" Edit ", menu=edit_menu)

        # View menu
        self.view_menu = tk.Menu(menubar, tearoff=0, bg=t["menu_bg"], fg=t["menu_fg"],
                                  activebackground=t["accent"], activeforeground=t["bg"])
        self.view_menu.add_checkbutton(label="  Preview             F3", onvalue=True, offvalue=False,
                                        command=self._toggle_preview, variable=tk.BooleanVar(value=True))
        self.view_menu.add_separator()
        self.view_menu.add_command(label="  🌙 Dark Theme", command=lambda: self._set_theme("dark"))
        self.view_menu.add_command(label="  ☀ Light Theme", command=lambda: self._set_theme("light"))
        self.view_menu.add_separator()
        self.view_menu.add_command(label="  Zoom In       Ctrl++", command=self._zoom_in)
        self.view_menu.add_command(label="  Zoom Out     Ctrl+-", command=self._zoom_out)
        menubar.add_cascade(label=" View ", menu=self.view_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=t["menu_bg"], fg=t["menu_fg"],
                            activebackground=t["accent"], activeforeground=t["bg"])
        help_menu.add_command(label="  Markdown Cheatsheet", command=self._show_cheatsheet)
        help_menu.add_command(label="  About", command=self._show_about)
        menubar.add_cascade(label=" Help ", menu=help_menu)

        self.root.config(menu=menubar)
        self.menubar = menubar

    # ── UI Layout ───────────────────────────────────────────────────────────
    def _build_ui(self):
        t = THEMES[self.theme]
        self.root.configure(bg=t["bg"])
        self.last_dir = os.path.expanduser("~")

        # Editor + Preview pane
        self.content_pane = tk.PanedWindow(self.root, orient="horizontal", bg=t["border"],
                                            sashwidth=4, sashrelief="flat")
        self.content_pane.pack(fill="both", expand=True)

        # Editor
        self.editor = MarkdownEditor(self.content_pane, self.theme, on_change=self._on_editor_change)
        self.content_pane.add(self.editor, minsize=300)

        # Preview
        self.preview = PreviewPane(self.content_pane, self.theme)
        self.content_pane.add(self.preview, minsize=300)

    # ── Status Bar ──────────────────────────────────────────────────────────
    def _build_statusbar(self):
        t = THEMES[self.theme]
        self.statusbar = tk.Frame(self.root, bg=t["status_bg"], height=28)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)

        self.status_file = tk.Label(
            self.statusbar, text=" No file open", font=("Segoe UI", 9),
            bg=t["status_bg"], fg=t["status_fg"], anchor="w"
        )
        self.status_file.pack(side="left", padx=8)

        self.status_info = tk.Label(
            self.statusbar, text="", font=("Segoe UI", 9),
            bg=t["status_bg"], fg=t["status_fg"], anchor="e"
        )
        self.status_info.pack(side="right", padx=8)

    def _update_status(self):
        line, col = self.editor.get_cursor_pos()
        words = self.editor.get_word_count()
        chars = self.editor.get_char_count()
        self.status_info.configure(text=f"Ln {line}, Col {col}  |  {words} words  |  {chars} chars")
        self.root.after(500, self._update_status)

    # ── File Operations ─────────────────────────────────────────────────────
    def _new_file(self):
        if self._check_save():
            self.current_file = None
            self.editor.clear()
            self.preview.update_preview("")
            self.status_file.configure(text=" New file")
            self.root.title("EditMD — New file")
            self._modified = False

    def _open_file_dialog(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Markdown files", "*.md *.markdown *.mdown"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
            initialdir=self.last_dir,
        )
        if path:
            self._open_file(path)

    def _open_file(self, path):
        if not os.path.isfile(path):
            return
        if self._modified and not self._check_save():
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.current_file = path
            self.editor.set_content(content)
            self.preview.update_preview(content)
            fname = os.path.basename(path)
            self.status_file.configure(text=f" {fname}")
            self.root.title(f"EditMD — {fname}")
            self.last_dir = os.path.dirname(path)
            self._modified = False
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file:\n{e}")

    def _save_file(self):
        if self.current_file:
            try:
                content = self.editor.get_content()
                with open(self.current_file, "w", encoding="utf-8") as f:
                    f.write(content)
                self._modified = False
                self.root.title(f"EditMD — {os.path.basename(self.current_file)}")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot save file:\n{e}")
        else:
            self._save_file_as()

    def _save_file_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[
                ("Markdown file", "*.md"),
                ("Markdown file", "*.markdown"),
                ("Text file", "*.txt"),
                ("All files", "*.*"),
            ],
            initialdir=self.last_dir,
        )
        if path:
            self.current_file = path
            self._save_file()
            self.last_dir = os.path.dirname(path)

    def _export_html(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML file", "*.html")],
            initialdir=self.last_dir,
        )
        if path:
            content = self.editor.get_content()
            extensions = [
                "markdown.extensions.tables",
                "markdown.extensions.fenced_code",
                "markdown.extensions.codehilite",
                "markdown.extensions.toc",
            ]
            html = markdown.markdown(content, extensions=extensions)
            full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{os.path.basename(self.current_file or "document")}</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 40px auto;
       padding: 0 20px; line-height: 1.7; color: #333; }}
h1,h2,h3 {{ color: #1a1a2e; border-bottom: 1px solid #eee; padding-bottom: 6px; }}
code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 4px; font-size: 14px; }}
pre {{ background: #f4f4f4; padding: 16px; border-radius: 6px; overflow-x: auto; }}
pre code {{ background: none; padding: 0; }}
blockquote {{ border-left: 4px solid #ddd; padding: 8px 16px; margin: 12px 0;
              background: #f9f9f9; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 8px 12px; }}
th {{ background: #f4f4f4; }}
img {{ max-width: 100%; }}
</style>
</head>
<body>
{html}
</body>
</html>"""
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(full_html)
                messagebox.showinfo("Export", f"HTML exported to:\n{path}")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot export:\n{e}")

    def _check_save(self):
        if self._modified:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Save before continuing?"
            )
            if result is None:
                return False
            if result:
                self._save_file()
        return True

    # ── Editor Change Handler ───────────────────────────────────────────────
    def _on_editor_change(self):
        self._modified = True
        if self.current_file:
            self.root.title(f"EditMD — {os.path.basename(self.current_file)} *")
        else:
            self.root.title("EditMD — New file *")
        # Debounced preview update
        if hasattr(self, "_preview_timer"):
            self.root.after_cancel(self._preview_timer)
        self._preview_timer = self.root.after(300, self._update_preview)

    def _update_preview(self):
        self.preview.update_preview(self.editor.get_content())

    # ── View Toggles ────────────────────────────────────────────────────────
    def _toggle_preview(self):
        self.show_preview = not self.show_preview
        if self.show_preview:
            self.content_pane.add(self.preview, minsize=300)
        else:
            self.content_pane.forget(self.preview)

    def _set_theme(self, theme):
        self.theme = theme
        t = THEMES[theme]
        self.root.configure(bg=t["bg"])
        self.content_pane.configure(bg=t["border"])
        self.editor.apply_theme(theme)
        self.preview.apply_theme(theme)
        self.statusbar.configure(bg=t["status_bg"])
        self.status_file.configure(bg=t["status_bg"], fg=t["status_fg"])
        self.status_info.configure(bg=t["status_bg"], fg=t["status_fg"])
        # Rebuild menu with new theme colors
        self._build_menu()
        # Update preview
        self.preview.update_preview(self.editor.get_content())

    def _zoom_in(self):
        current = self.editor.text.cget("font")
        size = int(re.search(r"\d+", current).group())
        self.editor.text.configure(font=("Consolas", size + 1))

    def _zoom_out(self):
        current = self.editor.text.cget("font")
        size = int(re.search(r"\d+", current).group())
        if size > 8:
            self.editor.text.configure(font=("Consolas", size - 1))

    # ── Keyboard Shortcuts ──────────────────────────────────────────────────
    def _bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self._new_file())
        self.root.bind("<Control-N>", lambda e: self._new_file())
        self.root.bind("<Control-o>", lambda e: self._open_file_dialog())
        self.root.bind("<Control-O>", lambda e: self._open_file_dialog())
        self.root.bind("<Control-s>", lambda e: self._save_file())
        self.root.bind("<Control-S>", lambda e: self._save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self._save_file_as())
        self.root.bind("<Control-e>", lambda e: self._export_html())
        self.root.bind("<Control-E>", lambda e: self._export_html())
        self.root.bind("<Control-b>", lambda e: self._wrap_selection("**", "**"))
        self.root.bind("<Control-B>", lambda e: self._wrap_selection("**", "**"))
        self.root.bind("<Control-i>", lambda e: self._wrap_selection("*", "*"))
        self.root.bind("<Control-I>", lambda e: self._wrap_selection("*", "*"))
        self.root.bind("<Control-k>", lambda e: self._insert_link())
        self.root.bind("<Control-K>", lambda e: self._insert_link())
        self.root.bind("<Control-grave>", lambda e: self._wrap_selection("`", "`"))
        self.root.bind("<Control-f>", lambda e: self._find_dialog())
        self.root.bind("<Control-F>", lambda e: self._find_dialog())
        self.root.bind("<Control-a>", lambda e: self._select_all())
        self.root.bind("<Control-A>", lambda e: self._select_all())
        self.root.bind("<F3>", lambda e: self._toggle_preview())
        self.root.bind("<Control-equal>", lambda e: self._zoom_in())
        self.root.bind("<Control-minus>", lambda e: self._zoom_out())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Edit Helpers ────────────────────────────────────────────────────────
    def _wrap_selection(self, before, after):
        text = self.editor.text
        try:
            sel = text.get("sel.first", "sel.last")
            text.delete("sel.first", "sel.last")
            text.insert("sel.first", f"{before}{sel}{after}")
        except tk.TclError:
            text.insert("insert", f"{before}{after}")
            text.mark_set("insert", f"insert-{len(after)}c")

    def _insert_link(self):
        text = self.editor.text
        try:
            sel = text.get("sel.first", "sel.last")
            text.delete("sel.first", "sel.last")
            text.insert("sel.first", f"[{sel}](url)")
        except tk.TclError:
            text.insert("insert", "[link text](url)")

    def _insert_image(self):
        self.editor.text.insert("insert", "![alt text](image_url)")

    def _insert_table(self):
        table = "\n| Header 1 | Header 2 | Header 3 |\n|----------|----------|----------|\n| Cell 1   | Cell 2   | Cell 3   |\n| Cell 4   | Cell 5   | Cell 6   |\n"
        self.editor.text.insert("insert", table)

    def _insert_text(self, text):
        self.editor.text.insert("insert", text)

    def _select_all(self):
        self.editor.text.tag_add("sel", "1.0", "end")

    def _find_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Find & Replace")
        dialog.geometry("420x140")
        dialog.resizable(False, False)
        dialog.configure(bg=THEMES[self.theme]["bg"])
        dialog.transient(self.root)

        t = THEMES[self.theme]
        tk.Label(dialog, text="Find:", bg=t["bg"], fg=t["fg"]).grid(row=0, column=0, padx=8, pady=6, sticky="e")
        tk.Label(dialog, text="Replace:", bg=t["bg"], fg=t["fg"]).grid(row=1, column=0, padx=8, pady=6, sticky="e")

        find_var = tk.StringVar()
        repl_var = tk.StringVar()
        find_entry = tk.Entry(dialog, textvariable=find_var, width=35, font=("Consolas", 11),
                               bg=t["editor_bg"], fg=t["editor_fg"], insertbackground=t["fg"])
        repl_entry = tk.Entry(dialog, textvariable=repl_var, width=35, font=("Consolas", 11),
                               bg=t["editor_bg"], fg=t["editor_fg"], insertbackground=t["fg"])
        find_entry.grid(row=0, column=1, padx=8, pady=6)
        repl_entry.grid(row=1, column=1, padx=8, pady=6)
        find_entry.focus_set()

        def do_find():
            self.editor.text.tag_remove("found", "1.0", "end")
            query = find_var.get()
            if not query:
                return
            idx = "1.0"
            while True:
                idx = self.editor.text.search(query, idx, nocase=True, stopindex="end")
                if not idx:
                    break
                end_idx = f"{idx}+{len(query)}c"
                self.editor.text.tag_add("found", idx, end_idx)
                self.editor.text.tag_configure("found", background=t["accent"], foreground=t["bg"])
                idx = end_idx

        def do_replace():
            query = find_var.get()
            replacement = repl_var.get()
            if not query:
                return
            content = self.editor.get_content()
            new_content = content.replace(query, replacement)
            self.editor.set_content(new_content)
            self._on_editor_change()

        btn_frame = tk.Frame(dialog, bg=t["bg"])
        btn_frame.grid(row=2, column=0, columnspan=2, pady=8)
        tk.Button(btn_frame, text="Find All", command=do_find, bg=t["menu_bg"], fg=t["menu_fg"],
                  relief="flat", padx=12, cursor="hand2").pack(side="left", padx=4)
        tk.Button(btn_frame, text="Replace All", command=do_replace, bg=t["menu_bg"], fg=t["menu_fg"],
                  relief="flat", padx=12, cursor="hand2").pack(side="left", padx=4)

    # ── Help / About ────────────────────────────────────────────────────────
    def _show_cheatsheet(self):
        win = tk.Toplevel(self.root)
        win.title("Markdown Cheatsheet")
        win.geometry("600x500")
        t = THEMES[self.theme]
        win.configure(bg=t["bg"])

        text = tk.Text(win, font=("Consolas", 11), bg=t["editor_bg"], fg=t["editor_fg"],
                        relief="flat", padx=16, pady=16)
        text.pack(fill="both", expand=True)
        text.insert("1.0", """# Markdown Cheatsheet

## Headers
# H1  |  ## H2  |  ### H3  |  #### H4

## Emphasis
**bold**  |  *italic*  |  ~~strikethrough~~

## Lists
- Unordered item
- Another item
  - Nested item

1. Ordered item
2. Another item

## Links & Images
[Link text](https://example.com)
![Image alt](https://example.com/img.png)

## Code
Inline `code` in text

```python
def hello():
    print("Hello, World!")
```

## Blockquotes
> This is a blockquote
> It can span multiple lines

## Tables
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |

## Horizontal Rule
---

## Task Lists
- [ ] Unchecked task
- [x] Checked task
""")
        text.configure(state="disabled")

    def _show_about(self):
        messagebox.showinfo(
            "About EditMD",
            "EditMD — Markdown Editor\n\n"
            "Version 1.0\n\n"
            "A lightweight desktop application for\n"
            "creating, viewing and editing Markdown files.\n\n"
            "Built with Python + Tkinter"
        )

    # ── Close ───────────────────────────────────────────────────────────────
    def _on_close(self):
        if self._check_save():
            self.root.destroy()

    # ── Run ─────────────────────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = EditMDApp()
    app.run()
