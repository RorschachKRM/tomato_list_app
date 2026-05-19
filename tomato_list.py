import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

def _get_data_dir():
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        base = os.path.expanduser("~")
    d = os.path.join(base, "TomatoList")
    os.makedirs(d, exist_ok=True)
    return d

DATA_FILE = os.path.join(_get_data_dir(), "data.json")

# ── Data ──
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

# ── Colors ──
TOMATO = "#e74c3c"
TOMATO_DARK = "#c0392b"
TOMATO_LIGHT = "#fce4e4"
GREEN = "#2ecc71"
GREEN_DARK = "#27ae60"
GREEN_LIGHT = "#e8f8ef"
BLUE = "#3498db"
BG = "#f5f5f5"
CARD = "#ffffff"
TEXT = "#2c3e50"
TEXT_LIGHT = "#95a5a6"
BORDER = "#e0e0e0"

class TomatoListApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tomato List")
        self.root.geometry("440x680")
        self.root.minsize(380, 600)
        self.root.configure(bg=BG)

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

    def _persist(self):
        save_data({
            "sessions_today": self.sessions_today,
            "session_date": self.session_date,
            "todos": self.todos,
        })

    # ── UI ──
    def _build_ui(self):
        # Main container
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        # Header
        header = tk.Label(main, text="🍅 Tomato List", font=("Segoe UI", 20, "bold"),
                          bg=BG, fg=TEXT)
        header.pack(pady=(0, 12))

        # ── Timer Card ──
        self.timer_frame = tk.Frame(main, bg=CARD, highlightthickness=0,
                                     bd=0, relief="flat")
        self.timer_frame.pack(fill=tk.X, pady=(0, 12))
        # Card shadow via border
        self.timer_frame.configure(highlightbackground=BORDER, highlightthickness=1)

        # Mode tabs
        tab_frame = tk.Frame(self.timer_frame, bg="#e8e8e8")
        tab_frame.pack(fill=tk.X, padx=16, pady=(16, 12))

        self.tab_focus = tk.Button(tab_frame, text="专注", font=("Segoe UI", 10, "bold"),
                                    bg=CARD, fg=TOMATO, relief="flat", bd=0,
                                    activebackground=CARD, activeforeground=TOMATO,
                                    padx=20, pady=6, cursor="hand2",
                                    command=lambda: self._switch_mode("focus"))
        self.tab_focus.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.tab_short = tk.Button(tab_frame, text="短休", font=("Segoe UI", 10, "bold"),
                                    bg="#e8e8e8", fg=TEXT_LIGHT, relief="flat", bd=0,
                                    activebackground=CARD, activeforeground=GREEN_DARK,
                                    padx=20, pady=6, cursor="hand2",
                                    command=lambda: self._switch_mode("short"))
        self.tab_short.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        self.tab_long = tk.Button(tab_frame, text="长休", font=("Segoe UI", 10, "bold"),
                                   bg="#e8e8e8", fg=TEXT_LIGHT, relief="flat", bd=0,
                                   activebackground=CARD, activeforeground=BLUE,
                                   padx=20, pady=6, cursor="hand2",
                                   command=lambda: self._switch_mode("long"))
        self.tab_long.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        # Time display
        self.time_label = tk.Label(self.timer_frame, text="25:00",
                                    font=("Consolas", 48, "bold"), bg=CARD, fg=TEXT)
        self.time_label.pack(pady=(8, 0))

        self.status_label = tk.Label(self.timer_frame, text="准备专注",
                                      font=("Segoe UI", 10), bg=CARD, fg=TEXT_LIGHT)
        self.status_label.pack()

        # Progress bar
        self.progress = ttk.Progressbar(self.timer_frame, length=320, mode="determinate")
        self.progress.pack(pady=(12, 12), padx=30)
        self.progress["value"] = 0

        # Controls
        ctrl_frame = tk.Frame(self.timer_frame, bg=CARD)
        ctrl_frame.pack(pady=(0, 8))

        self.btn_reset = tk.Button(ctrl_frame, text="↺", font=("Segoe UI", 14),
                                    bg="#e8e8e8", fg=TEXT_LIGHT, relief="flat", bd=0,
                                    width=3, height=1, cursor="hand2",
                                    activebackground="#ddd",
                                    command=self._reset_timer)
        self.btn_reset.pack(side=tk.LEFT, padx=10)

        self.btn_play = tk.Button(ctrl_frame, text="▶", font=("Segoe UI", 16),
                                   bg=TOMATO, fg="white", relief="flat", bd=0,
                                   width=4, height=1, cursor="hand2",
                                   activebackground=TOMATO_DARK, activeforeground="white",
                                   command=self._toggle_timer)
        self.btn_play.pack(side=tk.LEFT, padx=10)

        # Session count
        self.session_label = tk.Label(self.timer_frame, text="",
                                       font=("Segoe UI", 10), bg=CARD, fg=TEXT_LIGHT)
        self.session_label.pack(pady=(4, 0))
        self._update_session_label()

        # Settings
        settings_frame = tk.Frame(self.timer_frame, bg=CARD)
        settings_frame.pack(pady=(10, 16))

        self._make_setting(settings_frame, "专注", "focus", TOMATO, 0)
        self._make_setting(settings_frame, "短休", "short", GREEN_DARK, 1)
        self._make_setting(settings_frame, "长休", "long", BLUE, 2)

        # ── Todo Card ──
        self.todo_frame = tk.Frame(main, bg=CARD, highlightthickness=0)
        self.todo_frame.pack(fill=tk.BOTH, expand=True)
        self.todo_frame.configure(highlightbackground=BORDER, highlightthickness=1)

        todo_header = tk.Frame(self.todo_frame, bg=CARD)
        todo_header.pack(fill=tk.X, padx=16, pady=(16, 8))

        tk.Label(todo_header, text="待办事项", font=("Segoe UI", 14, "bold"),
                 bg=CARD, fg=TEXT).pack(side=tk.LEFT)

        self.todo_count_label = tk.Label(todo_header, text="0 项", font=("Segoe UI", 10),
                                          bg=CARD, fg=TEXT_LIGHT)
        self.todo_count_label.pack(side=tk.RIGHT)

        # Input row
        input_frame = tk.Frame(self.todo_frame, bg=CARD)
        input_frame.pack(fill=tk.X, padx=16, pady=(0, 8))

        self.todo_entry = tk.Entry(input_frame, font=("Segoe UI", 11),
                                    bg="#f8f8f8", fg=TEXT, relief="flat",
                                    highlightbackground=BORDER, highlightthickness=1,
                                    insertbackground=TEXT)
        self.todo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 6))
        self.todo_entry.bind("<Return>", lambda e: self._add_todo())

        add_btn = tk.Button(input_frame, text="添加", font=("Segoe UI", 10, "bold"),
                             bg=TOMATO, fg="white", relief="flat", bd=0, padx=16, pady=6,
                             cursor="hand2", activebackground=TOMATO_DARK,
                             activeforeground="white", command=self._add_todo)
        add_btn.pack(side=tk.RIGHT)

        # Todo list
        list_bg = tk.Frame(self.todo_frame, bg=CARD)
        list_bg.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        self.todo_canvas = tk.Canvas(list_bg, bg=CARD, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(list_bg, orient=tk.VERTICAL, command=self.todo_canvas.yview)
        self.todo_scroll_frame = tk.Frame(self.todo_canvas, bg=CARD)

        self.todo_scroll_frame.bind("<Configure>",
            lambda e: self.todo_canvas.configure(scrollregion=self.todo_canvas.bbox("all")))

        self.todo_canvas_window = self.todo_canvas.create_window((0, 0),
            window=self.todo_scroll_frame, anchor="nw", tags="self.todo_scroll_frame")

        self.todo_canvas.configure(yscrollcommand=scrollbar.set)

        self.todo_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind canvas resize
        self.todo_canvas.bind("<Configure>", self._on_canvas_resize)
        # Mouse wheel
        self.todo_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # Clear done button
        btn_frame = tk.Frame(self.todo_frame, bg=CARD)
        btn_frame.pack(fill=tk.X, padx=16, pady=(0, 12))
        self.clear_btn = tk.Button(btn_frame, text="清空已完成", font=("Segoe UI", 9),
                                    bg=CARD, fg=TEXT_LIGHT, relief="solid", bd=1,
                                    highlightbackground=BORDER, padx=12, pady=3,
                                    cursor="hand2", activebackground=TOMATO_LIGHT,
                                    command=self._clear_done)
        self.clear_btn.pack(side=tk.RIGHT)

        # Initial render
        self._render_todos()

    def _make_setting(self, parent, label, mode, color, col):
        frame = tk.Frame(parent, bg=CARD)
        frame.pack(side=tk.LEFT, padx=10)

        tk.Label(frame, text=label, font=("Segoe UI", 8), bg=CARD, fg=TEXT_LIGHT).pack()

        sv = tk.StringVar(value=str(self.minutes[mode]))
        sv.trace_add("write", lambda *a, m=mode, v=sv: self._on_setting_change(m, v))

        entry = tk.Entry(frame, textvariable=sv, font=("Segoe UI", 11, "bold"),
                         bg="#f8f8f8", fg=color, relief="flat", width=3,
                         justify="center", highlightbackground=BORDER, highlightthickness=1,
                         insertbackground=color)
        entry.pack(ipady=3)
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
        active_bg = CARD
        inactive_bg = "#e8e8e8"

        tabs = [
            (self.tab_focus, "focus", TOMATO),
            (self.tab_short, "short", GREEN_DARK),
            (self.tab_long, "long", BLUE),
        ]
        for btn, mode, color in tabs:
            if mode == self.mode:
                btn.configure(bg=active_bg, fg=color, activeforeground=color)
            else:
                btn.configure(bg=inactive_bg, fg=TEXT_LIGHT, activeforeground=color)

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
        self.btn_play.configure(text="⏸", bg=TOMATO_DARK)
        mode_names = {"focus": "专注中…", "short": "短休中…", "long": "长休中…"}
        self.status_label.configure(text=mode_names[self.mode])

        # Highlight card
        if self.mode == "focus":
            self.timer_frame.configure(highlightbackground=TOMATO, highlightthickness=2)
        else:
            self.timer_frame.configure(highlightbackground=GREEN, highlightthickness=2)

        self._tick()

    def _stop_timer(self):
        self.running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.btn_play.configure(text="▶", bg=TOMATO)
        mode_names = {"focus": "准备专注", "short": "准备短休", "long": "准备长休"}
        self.status_label.configure(text=mode_names[self.mode])
        self.timer_frame.configure(highlightbackground=BORDER, highlightthickness=1)

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
        # Bring window to front
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
        progress_pct = (1 - self.seconds_left / self.total_seconds) * 100 if self.total_seconds > 0 else 0
        self.progress["value"] = progress_pct

        # Color time text based on mode when running
        if self.running:
            if self.mode == "focus":
                self.time_label.configure(fg=TOMATO)
            else:
                self.time_label.configure(fg=GREEN)
        else:
            self.time_label.configure(fg=TEXT)

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
            empty_label = tk.Label(self.todo_scroll_frame,
                                    text="还没有任务\n添加一个开始吧",
                                    font=("Segoe UI", 10), bg=CARD, fg=TEXT_LIGHT)
            empty_label.pack(pady=20)
            self.clear_btn.pack_forget()
        else:
            for todo in all_todos:
                self._create_todo_row(todo)
            if done:
                self.clear_btn.pack(side=tk.RIGHT)
            else:
                self.clear_btn.pack_forget()

        active_count = len(active)
        self.todo_count_label.configure(text=f"{active_count} 项")

    def _create_todo_row(self, todo):
        row = tk.Frame(self.todo_scroll_frame, bg=CARD)
        row.pack(fill=tk.X, padx=6, pady=2)

        # Check button
        check_text = "✓" if todo["done"] else ""
        check_bg = GREEN if todo["done"] else CARD
        check_fg = "white" if todo["done"] else BORDER
        check_border = GREEN if todo["done"] else "#ccc"

        check = tk.Button(row, text=check_text, font=("Segoe UI", 10, "bold"),
                          bg=check_bg, fg=check_fg, relief="solid", bd=2,
                          width=2, height=1, cursor="hand2",
                          activebackground=GREEN_LIGHT if not todo["done"] else GREEN,
                          highlightbackground=check_border, highlightthickness=0)
        check.configure(command=lambda t=todo: self._toggle_todo(t["id"]))
        check.pack(side=tk.LEFT, padx=(0, 10))

        # Text
        text_fg = TEXT_LIGHT if todo["done"] else TEXT
        text_font = ("Segoe UI", 11, "overstrike" if todo["done"] else "normal")
        text_label = tk.Label(row, text=todo["text"], font=text_font,
                               bg=CARD, fg=text_fg, anchor="w")
        text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Delete button
        del_btn = tk.Button(row, text="×", font=("Segoe UI", 14),
                             bg=CARD, fg="#ccc", relief="flat", bd=0,
                             width=2, cursor="hand2", activebackground=TOMATO_LIGHT,
                             activeforeground=TOMATO,
                             command=lambda t=todo: self._delete_todo(t["id"]))
        del_btn.pack(side=tk.RIGHT)

        # Separator
        sep = tk.Frame(self.todo_scroll_frame, bg=BORDER, height=1)
        sep.pack(fill=tk.X, padx=6)

def main():
    root = tk.Tk()
    app = TomatoListApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
