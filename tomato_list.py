import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import ToolTip
import json
import os
from datetime import datetime

# ── Data persistence ──
def _get_data_dir():
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    d = os.path.join(base, "TomatoList")
    os.makedirs(d, exist_ok=True)
    return d

DATA_FILE = os.path.join(_get_data_dir(), "data.json")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"sessions_today": 0, "session_date": "", "todos": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class TomatoListApp:
    def __init__(self):
        # Theme: flatly, litera, cosmo, minty, morph, sandstone, solar, superhero, darkly, vapor
        self.root = ttk.Window(themename="cosmo")
        self.root.title("Tomato List")
        self.root.geometry("440x680")
        self.root.minsize(380, 600)

        # Enable DPI awareness on Windows
        try:
            self.root.tk.call("tk", "scaling", 1.5)
        except Exception:
            pass
        self._set_dpi_aware()

        # State
        data = load_data()
        self.sessions_today = data["sessions_today"]
        self.session_date = data["session_date"]
        self.todos = data["todos"]

        today = datetime.now().strftime("%Y-%m-%d")
        if self.session_date != today:
            self.sessions_today = 0
            self.session_date = today

        self.mode = "focus"  # focus | short | long
        self.minutes = {"focus": 25, "short": 5, "long": 15}
        self.seconds_left = 25 * 60
        self.total_seconds = 25 * 60
        self.running = False
        self.after_id = None

        self._persist()
        self._build_ui()
        self._update_display()

    def _set_dpi_aware(self):
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI
        except Exception:
            try:
                from ctypes import windll
                windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    def _persist(self):
        save_data({
            "sessions_today": self.sessions_today,
            "session_date": self.session_date,
            "todos": self.todos,
        })

    # ── UI ──
    def _build_ui(self):
        root = self.root
        pad = 20

        # ── Header ──
        header = ttk.Label(root, text="🍅 Tomato List",
                           font=("Segoe UI", 22, "bold"),
                           bootstyle="inverse-dark")
        header.pack(pady=(pad, 12))

        # ── Timer Card ──
        self.timer_frame = ttk.Frame(root, bootstyle="dark", padding=0)
        self.timer_frame.pack(fill=tk.X, padx=pad, pady=(0, 12))

        # Mode tabs
        tab_outer = ttk.Frame(self.timer_frame, bootstyle="dark")
        tab_outer.pack(fill=tk.X, padx=16, pady=(16, 12))
        tab_inner = ttk.Frame(tab_outer, bootstyle="secondary")
        tab_inner.pack(fill=tk.X)

        self.tab_focus = ttk.Button(tab_inner, text="专注", bootstyle="primary",
                                     command=lambda: self._switch_mode("focus"))
        self.tab_focus.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 0))

        self.tab_short = ttk.Button(tab_inner, text="短休", bootstyle="primary-link",
                                     command=lambda: self._switch_mode("short"))
        self.tab_short.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=0)

        self.tab_long = ttk.Button(tab_inner, text="长休", bootstyle="primary-link",
                                    command=lambda: self._switch_mode("long"))
        self.tab_long.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=0)

        # Time display
        self.time_label = ttk.Label(self.timer_frame, text="25:00",
                                     font=("Consolas", 50, "bold"),
                                     bootstyle="inverse-dark")
        self.time_label.pack(pady=(10, 0))

        self.status_label = ttk.Label(self.timer_frame, text="准备专注",
                                       font=("Segoe UI", 10),
                                       bootstyle="inverse-secondary")
        self.status_label.pack()

        # Progress bar
        self.progress = ttk.Progressbar(self.timer_frame, length=320, mode=DETERMINATE,
                                         bootstyle="primary")
        self.progress.pack(pady=(16, 16), padx=30)
        self.progress["value"] = 0

        # Controls
        ctrl_frame = ttk.Frame(self.timer_frame, bootstyle="dark")
        ctrl_frame.pack(pady=(0, 8))

        self.btn_reset = ttk.Button(ctrl_frame, text="↺", bootstyle="secondary-outline",
                                     padding=(12, 8), command=self._reset_timer)
        ToolTip(self.btn_reset, "重置")
        self.btn_reset.pack(side=tk.LEFT, padx=8)

        self.btn_play = ttk.Button(ctrl_frame, text="▶  开始专注",
                                    bootstyle="primary", padding=(24, 10),
                                    command=self._toggle_timer)
        self.btn_play.pack(side=tk.LEFT, padx=8)

        # Session count
        self.session_label = ttk.Label(self.timer_frame, text="",
                                        font=("Segoe UI", 10),
                                        bootstyle="inverse-secondary")
        self.session_label.pack(pady=(6, 0))
        self._update_session_label()

        # Settings
        settings_frame = ttk.Frame(self.timer_frame, bootstyle="dark")
        settings_frame.pack(pady=(12, 16))

        self._make_setting(settings_frame, "专注 (分)", "focus", "primary")
        self._make_setting(settings_frame, "短休 (分)", "short", "success")
        self._make_setting(settings_frame, "长休 (分)", "long", "info")

        # ── Todo Card ──
        self.todo_frame = ttk.Frame(root, bootstyle="dark", padding=0)
        self.todo_frame.pack(fill=tk.BOTH, expand=True, padx=pad, pady=(0, pad))

        # Header
        todo_header = ttk.Frame(self.todo_frame, bootstyle="dark")
        todo_header.pack(fill=tk.X, padx=16, pady=(16, 8))

        ttk.Label(todo_header, text="待办事项",
                  font=("Segoe UI", 15, "bold"),
                  bootstyle="inverse-dark").pack(side=tk.LEFT)

        self.todo_count_label = ttk.Label(todo_header, text="0 项",
                                           font=("Segoe UI", 10),
                                           bootstyle="inverse-secondary")
        self.todo_count_label.pack(side=tk.RIGHT)

        # Input row
        input_frame = ttk.Frame(self.todo_frame, bootstyle="dark")
        input_frame.pack(fill=tk.X, padx=16, pady=(0, 10))

        self.todo_entry = ttk.Entry(input_frame, font=("Segoe UI", 11))
        self.todo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.todo_entry.bind("<Return>", lambda e: self._add_todo())

        self.btn_add = ttk.Button(input_frame, text="添加", bootstyle="primary",
                                   command=self._add_todo)
        self.btn_add.pack(side=tk.RIGHT)

        # Todo list area
        list_container = ttk.Frame(self.todo_frame, bootstyle="dark")
        list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        self.todo_canvas = tk.Canvas(list_container, highlightthickness=0, bd=0,
                                      bg=self.root.style.colors.dark)
        self.todo_scroll_frame = ttk.Frame(self.todo_canvas, bootstyle="dark")

        self.todo_scroll_frame.bind("<Configure>",
            lambda e: self.todo_canvas.configure(
                scrollregion=self.todo_canvas.bbox("all")))

        self.todo_canvas_window = self.todo_canvas.create_window(
            (0, 0), window=self.todo_scroll_frame, anchor="nw")

        self.todo_canvas.bind("<Configure>", self._on_canvas_resize)
        self.todo_canvas.bind("<MouseWheel>", self._on_mousewheel)

        self.todo_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Clear button
        btn_frame = ttk.Frame(self.todo_frame, bootstyle="dark")
        btn_frame.pack(fill=tk.X, padx=16, pady=(0, 12))
        self.clear_btn = ttk.Button(btn_frame, text="清空已完成",
                                     bootstyle="secondary-outline",
                                     command=self._clear_done)
        self.clear_btn.pack(side=tk.RIGHT)

        self._render_todos()

    def _make_setting(self, parent, label, mode, bootstyle):
        frame = ttk.Frame(parent, bootstyle="dark")
        frame.pack(side=tk.LEFT, padx=12)

        ttk.Label(frame, text=label, font=("Segoe UI", 8),
                  bootstyle="inverse-secondary").pack()

        sv = tk.StringVar(value=str(self.minutes[mode]))
        sv.trace_add("write", lambda *a, m=mode, v=sv: self._on_setting_change(m, v))

        entry = ttk.Entry(frame, textvariable=sv, font=("Segoe UI", 12, "bold"),
                          bootstyle=bootstyle, width=4, justify=CENTER)
        entry.pack(ipady=2, pady=(2, 0))
        setattr(self, f"setting_{mode}", entry)

    def _on_canvas_resize(self, event):
        self.todo_canvas.itemconfig(self.todo_canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.todo_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Timer Logic ──
    def _switch_mode(self, mode):
        if self.running:
            self._stop_timer()
        self.mode = mode
        self.seconds_left = self.minutes[mode] * 60
        self.total_seconds = self.seconds_left
        self._update_display()
        self._update_tabs()

    def _update_tabs(self):
        styles = {"focus": "primary", "short": "success", "long": "info"}
        tabs = [
            (self.tab_focus, "focus"),
            (self.tab_short, "short"),
            (self.tab_long, "long"),
        ]
        for btn, mode in tabs:
            if mode == self.mode:
                btn.configure(bootstyle=styles[mode])
            else:
                btn.configure(bootstyle="primary-link")

    def _update_session_label(self):
        self.session_label.configure(text=f"今日专注 {self.sessions_today} 次")

    def _on_setting_change(self, mode, sv):
        try:
            v = int(sv.get())
            v = max(1, min(120 if mode == "focus" else 30 if mode == "short" else 60, v))
        except ValueError:
            v = self.minutes[mode]
        self.minutes[mode] = v
        if self.mode == mode and not self.running:
            self.seconds_left = v * 60
            self.total_seconds = self.seconds_left
            self._update_display()

    def _toggle_timer(self):
        if self.running:
            self._stop_timer()
        else:
            self._start_timer()

    def _start_timer(self):
        if self.seconds_left <= 0:
            self.seconds_left = self.minutes[self.mode] * 60
            self.total_seconds = self.seconds_left

        self.running = True
        self.btn_play.configure(text="⏸  暂停", bootstyle="warning")
        mode_names = {"focus": "专注中…", "short": "短休中…", "long": "长休中…"}
        self.status_label.configure(text=mode_names[self.mode])
        self._update_tabs()
        self._tick()

    def _stop_timer(self):
        self.running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.btn_play.configure(text="▶  开始专注", bootstyle="primary")
        mode_names = {"focus": "准备专注", "short": "准备短休", "long": "准备长休"}
        self.status_label.configure(text=mode_names[self.mode])
        self._update_tabs()

    def _tick(self):
        if not self.running:
            return
        if self.seconds_left > 0:
            self.seconds_left -= 1
            self._update_display()
            self.after_id = self.root.after(1000, self._tick)
        else:
            self._finish_timer()

    def _finish_timer(self):
        self._stop_timer()
        if self.mode == "focus":
            self.sessions_today += 1
            self._update_session_label()
            self._persist()
            self._switch_mode("short")
        else:
            self._switch_mode("focus")
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(200, lambda: self.root.attributes("-topmost", False))

    def _reset_timer(self):
        self._stop_timer()
        self.seconds_left = self.minutes[self.mode] * 60
        self.total_seconds = self.seconds_left
        self._update_display()

    def _update_display(self):
        m = self.seconds_left // 60
        s = self.seconds_left % 60
        self.time_label.configure(text=f"{m:02d}:{s:02d}")

        progress_pct = (1 - self.seconds_left / self.total_seconds) * 100 \
            if self.total_seconds > 0 else 0
        self.progress["value"] = progress_pct

        # Color based on mode
        if self.running:
            colors = {"focus": "danger", "short": "success", "long": "info"}
            self.time_label.configure(bootstyle=colors[self.mode])
        else:
            self.time_label.configure(bootstyle="inverse-dark")

    # ── Todo Logic ──
    def _add_todo(self):
        text = self.todo_entry.get().strip()
        if not text:
            return
        self.todos.append({
            "id": int(datetime.now().timestamp() * 1000),
            "text": text[:200],
            "done": False,
        })
        self.todo_entry.delete(0, tk.END)
        self._persist()
        self._render_todos()

    def _toggle_todo(self, todo_id):
        for t in self.todos:
            if t["id"] == todo_id:
                t["done"] = not t["done"]
                break
        self._persist()
        self._render_todos()

    def _delete_todo(self, todo_id):
        self.todos = [t for t in self.todos if t["id"] != todo_id]
        self._persist()
        self._render_todos()

    def _clear_done(self):
        self.todos = [t for t in self.todos if not t["done"]]
        self._persist()
        self._render_todos()

    def _render_todos(self):
        for w in self.todo_scroll_frame.winfo_children():
            w.destroy()

        active = [t for t in self.todos if not t["done"]]
        done = [t for t in self.todos if t["done"]]
        all_todos = active + done

        if not all_todos:
            ttk.Label(self.todo_scroll_frame,
                      text="还没有任务\n添加一个开始吧",
                      font=("Segoe UI", 10),
                      bootstyle="inverse-secondary",
                      justify=CENTER).pack(pady=24)
            self.clear_btn.pack_forget()
        else:
            for todo in all_todos:
                self._create_todo_row(todo)
            if done:
                self.clear_btn.pack(side=tk.RIGHT)
            else:
                self.clear_btn.pack_forget()

        self.todo_count_label.configure(text=f"{len(active)} 项")

    def _create_todo_row(self, todo):
        row = ttk.Frame(self.todo_scroll_frame, bootstyle="dark")
        row.pack(fill=tk.X, padx=4, pady=1)

        # Check button
        if todo["done"]:
            check = ttk.Button(row, text="✓", bootstyle="success",
                                padding=(4, 4),
                                command=lambda t=todo: self._toggle_todo(t["id"]))
        else:
            check = ttk.Button(row, text="○", bootstyle="secondary-outline",
                                padding=(4, 4),
                                command=lambda t=todo: self._toggle_todo(t["id"]))
        check.pack(side=tk.LEFT, padx=(0, 10))

        # Text
        text_fg = "inverse-secondary" if todo["done"] else "inverse-dark"
        text_font = ("Segoe UI", 11, "overstrike" if todo["done"] else "normal")
        text_label = ttk.Label(row, text=todo["text"], font=text_font,
                                bootstyle=text_fg, anchor="w", wraplength=260)
        text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Delete
        del_btn = ttk.Button(row, text="×", bootstyle="secondary-link",
                              padding=(4, 4),
                              command=lambda t=todo: self._delete_todo(t["id"]))
        del_btn.pack(side=tk.RIGHT)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = TomatoListApp()
    app.run()
