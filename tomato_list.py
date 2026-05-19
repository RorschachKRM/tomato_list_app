import customtkinter as ctk
import tkinter as tk
import json
import os
from datetime import datetime
from ctypes import windll

# ── Appearance ──
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

FONT = "Trebuchet MS"
MONO = "Consolas"

# ── ToolTip ──
class ToolTip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self.after_id = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)

    def _schedule(self, event=None):
        self.after_id = self.widget.after(self.delay, self._show)

    def _show(self):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self.text, font=(FONT, 9),
                 background="#ffffe0", foreground="#000000",
                 relief="solid", borderwidth=1, padx=6, pady=2).pack()

    def _hide(self, event=None):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


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
        self.root = ctk.CTk()
        self.root.title("Tomato List")
        self.root.geometry("440x680")
        self.root.minsize(380, 600)

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

        self.mode = "focus"
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
            windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    def _persist(self):
        save_data({
            "sessions_today": self.sessions_today,
            "session_date": self.session_date,
            "todos": self.todos,
        })

    # ── Color helpers ──
    CARD = ("#ffffff", "#2b2b2b")
    CARD_INNER = ("#f5f5f5", "#242424")
    TEXT = ("#1a1a1a", "#e0e0e0")
    TEXT_MUTED = ("#888888", "#909090")
    TIMER_COLORS = {"focus": "#e74c3c", "short": "#2ecc71", "long": "#3498db"}
    TAB_COLORS = {
        "focus": ("#3b8ed0", "#1f6aa5"),
        "short": ("#2fa572", "#106a43"),
        "long": ("#3a7eb0", "#1f5380"),
    }

    # ── UI ──
    def _build_ui(self):
        root = self.root
        card_pad = 16

        # ── Header ──
        header = ctk.CTkLabel(root, text="Tomato List",
                              font=ctk.CTkFont(family=FONT, size=22, weight="bold"))
        header.pack(pady=(20, 12))

        # ── Timer Card ──
        self.timer_frame = ctk.CTkFrame(root, fg_color=self.CARD, corner_radius=12)
        self.timer_frame.pack(fill=tk.X, padx=16, pady=(0, 12))

        # Mode tabs
        tab_outer = ctk.CTkFrame(self.timer_frame, fg_color="transparent")
        tab_outer.pack(fill=tk.X, padx=card_pad, pady=(16, 12))

        tab_inner = ctk.CTkFrame(tab_outer, fg_color=self.CARD_INNER, corner_radius=8)
        tab_inner.pack(fill=tk.X)

        self.tab_focus = ctk.CTkButton(tab_inner, text="Focus",
                                       font=ctk.CTkFont(family=FONT, size=12, weight="bold"),
                                       fg_color=self.TAB_COLORS["focus"],
                                       hover_color=self.TAB_COLORS["focus"],
                                       corner_radius=6,
                                       command=lambda: self._switch_mode("focus"))
        self.tab_focus.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=4)

        self.tab_short = ctk.CTkButton(tab_inner, text="Break",
                                       font=ctk.CTkFont(family=FONT, size=12, weight="bold"),
                                       fg_color="transparent",
                                       hover_color=self.CARD_INNER,
                                       corner_radius=6,
                                       command=lambda: self._switch_mode("short"))
        self.tab_short.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), pady=4)

        self.tab_long = ctk.CTkButton(tab_inner, text="Long Break",
                                      font=ctk.CTkFont(family=FONT, size=12, weight="bold"),
                                      fg_color="transparent",
                                      hover_color=self.CARD_INNER,
                                      corner_radius=6,
                                      command=lambda: self._switch_mode("long"))
        self.tab_long.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), pady=4)

        # Time display
        self.time_label = ctk.CTkLabel(self.timer_frame, text="25:00",
                                       font=ctk.CTkFont(family=MONO, size=50,
                                                         weight="bold"))
        self.time_label.pack(pady=(10, 0))

        self.status_label = ctk.CTkLabel(self.timer_frame, text="Ready",
                                         font=ctk.CTkFont(family=FONT, size=11),
                                         text_color=self.TEXT_MUTED)
        self.status_label.pack()

        # Progress bar
        self.progress = ctk.CTkProgressBar(self.timer_frame, width=320, height=6,
                                           corner_radius=3,
                                           progress_color=self.TAB_COLORS["focus"][0])
        self.progress.pack(pady=(16, 16), padx=30)
        self.progress.set(0)

        # Controls
        ctrl_frame = ctk.CTkFrame(self.timer_frame, fg_color="transparent")
        ctrl_frame.pack(pady=(0, 8))

        self.btn_reset = ctk.CTkButton(ctrl_frame, text="↺", width=40, height=36,
                                       fg_color="transparent", border_width=2,
                                       border_color=self.TEXT_MUTED,
                                       text_color=self.TEXT,
                                       hover_color=("#e0e0e0", "#3a3a3a"),
                                       command=self._reset_timer)
        ToolTip(self.btn_reset, "Reset")
        self.btn_reset.pack(side=tk.LEFT, padx=8)

        self.btn_play = ctk.CTkButton(ctrl_frame, text="Start Focus",
                                      width=140, height=40,
                                      font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
                                      corner_radius=8,
                                      command=self._toggle_timer)
        self.btn_play.pack(side=tk.LEFT, padx=8)

        # Session count
        self.session_label = ctk.CTkLabel(self.timer_frame, text="",
                                          font=ctk.CTkFont(family=FONT, size=11),
                                          text_color=self.TEXT_MUTED)
        self.session_label.pack(pady=(6, 0))
        self._update_session_label()

        # Settings
        settings_frame = ctk.CTkFrame(self.timer_frame, fg_color="transparent")
        settings_frame.pack(pady=(12, 16))

        self._make_setting(settings_frame, "Focus (min)", "focus")
        self._make_setting(settings_frame, "Break (min)", "short")
        self._make_setting(settings_frame, "Long (min)", "long")

        # ── Todo Card ──
        self.todo_frame = ctk.CTkFrame(root, fg_color=self.CARD, corner_radius=12)
        self.todo_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        # Header
        todo_header = ctk.CTkFrame(self.todo_frame, fg_color="transparent")
        todo_header.pack(fill=tk.X, padx=card_pad, pady=(16, 8))

        ctk.CTkLabel(todo_header, text="Tasks",
                     font=ctk.CTkFont(family=FONT, size=15, weight="bold"),
                     text_color=self.TEXT).pack(side=tk.LEFT)

        self.todo_count_label = ctk.CTkLabel(todo_header, text="0 items",
                                             font=ctk.CTkFont(family=FONT, size=11),
                                             text_color=self.TEXT_MUTED)
        self.todo_count_label.pack(side=tk.RIGHT)

        # Input row
        input_frame = ctk.CTkFrame(self.todo_frame, fg_color="transparent")
        input_frame.pack(fill=tk.X, padx=card_pad, pady=(0, 10))

        self.todo_entry = ctk.CTkEntry(input_frame, font=ctk.CTkFont(family=FONT, size=12),
                                       placeholder_text="Add a task...",
                                       height=34)
        self.todo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.todo_entry.bind("<Return>", lambda e: self._add_todo())

        self.btn_add = ctk.CTkButton(input_frame, text="Add", width=60, height=34,
                                     corner_radius=6,
                                     command=self._add_todo)
        self.btn_add.pack(side=tk.RIGHT)

        # Todo list area (canvas-based scrolling)
        list_container = ctk.CTkFrame(self.todo_frame, fg_color="transparent")
        list_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 8))

        canvas_bg = "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#e8e8e8"
        self.todo_canvas = tk.Canvas(list_container, highlightthickness=0, bd=0,
                                     bg=canvas_bg)
        self.todo_scroll_frame = ctk.CTkFrame(self.todo_canvas, fg_color="transparent")

        self.todo_scroll_frame.bind("<Configure>",
            lambda e: self.todo_canvas.configure(
                scrollregion=self.todo_canvas.bbox("all")))

        self.todo_canvas_window = self.todo_canvas.create_window(
            (0, 0), window=self.todo_scroll_frame, anchor="nw")

        self.todo_canvas.bind("<Configure>", self._on_canvas_resize)
        self.todo_canvas.bind("<MouseWheel>", self._on_mousewheel)

        self.todo_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.todo_scrollbar = ctk.CTkScrollbar(list_container, orientation="vertical",
                                               command=self.todo_canvas.yview)
        self.todo_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.todo_canvas.configure(yscrollcommand=self.todo_scrollbar.set)

        # Clear button
        btn_frame = ctk.CTkFrame(self.todo_frame, fg_color="transparent")
        btn_frame.pack(fill=tk.X, padx=card_pad, pady=(0, 12))
        self.clear_btn = ctk.CTkButton(btn_frame, text="Clear Done", width=100,
                                       height=30, fg_color="transparent",
                                       border_width=1,
                                       border_color=self.TEXT_MUTED,
                                       text_color=self.TEXT_MUTED,
                                       hover_color=("#e8e8e8", "#3a3a3a"),
                                       command=self._clear_done)
        self.clear_btn.pack(side=tk.RIGHT)

        self._render_todos()

        # Keyboard shortcuts
        self.root.bind("<space>", lambda e: self._on_space())
        self.root.bind("<Control-n>", lambda e: self.todo_entry.focus_set())

    def _make_setting(self, parent, label, mode):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side=tk.LEFT, padx=14)

        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(family=FONT, size=10),
                     text_color=self.TEXT_MUTED).pack()

        sv = tk.StringVar(value=str(self.minutes[mode]))
        sv.trace_add("write", lambda *a, m=mode, v=sv: self._on_setting_change(m, v))

        entry = ctk.CTkEntry(frame, textvariable=sv, font=ctk.CTkFont(family=FONT, size=13, weight="bold"),
                             width=60, height=32, justify="center", corner_radius=6)
        entry.pack(pady=(4, 0))
        setattr(self, f"setting_{mode}", entry)

    def _on_canvas_resize(self, event):
        self.todo_canvas.itemconfig(self.todo_canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.todo_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_space(self):
        if self.root.focus_get() == self.todo_entry:
            return
        self._toggle_timer()

    # ── Timer Logic ──
    def _switch_mode(self, mode):
        if self.running:
            self._stop_timer()
        self.mode = mode
        self.seconds_left = self.minutes[mode] * 60
        self.total_seconds = self.seconds_left
        self.progress.configure(progress_color=self.TAB_COLORS[mode][0])
        self._update_display()
        self._update_tabs()

    def _update_tabs(self):
        tabs = [
            (self.tab_focus, "focus"),
            (self.tab_short, "short"),
            (self.tab_long, "long"),
        ]
        for btn, mode in tabs:
            if mode == self.mode:
                btn.configure(fg_color=self.TAB_COLORS[mode],
                              hover_color=self.TAB_COLORS[mode],
                              text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent",
                              hover_color=self.CARD_INNER,
                              text_color=self.TEXT_MUTED)

    def _update_session_label(self):
        self.session_label.configure(text=f"Today: {self.sessions_today} sessions")

    def _on_setting_change(self, mode, sv):
        try:
            v = int(sv.get())
            limits = {"focus": (1, 120), "short": (1, 30), "long": (1, 60)}
            lo, hi = limits[mode]
            v = max(lo, min(hi, v))
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
        mode_verbs = {"focus": "Focusing...", "short": "Break...", "long": "Long Break..."}
        self.btn_play.configure(text="⏸  Pause", fg_color="#e69b00",
                                hover_color="#c48500")
        self.status_label.configure(text=mode_verbs[self.mode])
        self._update_tabs()
        self._tick()

    def _stop_timer(self):
        self.running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        play_labels = {"focus": "Start Focus", "short": "Start Break", "long": "Start Long Break"}
        self.btn_play.configure(text=play_labels[self.mode],
                                fg_color=self.TAB_COLORS["focus"][0],
                                hover_color=self.TAB_COLORS["focus"])
        mode_labels = {"focus": "Ready", "short": "Break Ready", "long": "Long Break Ready"}
        self.status_label.configure(text=mode_labels[self.mode])
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

    def _play_sound(self):
        try:
            import winsound
            for freq in (800, 1000, 1200):
                winsound.Beep(freq, 180)
        except Exception:
            self.root.bell()

    def _finish_timer(self):
        self._stop_timer()
        if self.mode == "focus":
            self.sessions_today += 1
            self._update_session_label()
            self._persist()
            self._switch_mode("short")
        else:
            self._switch_mode("focus")
        self._play_sound()
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

        progress_pct = (1 - self.seconds_left / self.total_seconds) \
            if self.total_seconds > 0 else 0
        self.progress.set(progress_pct)

        if self.running:
            self.time_label.configure(text_color=self.TIMER_COLORS[self.mode])
        else:
            self.time_label.configure(text_color=self.TEXT)

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
            ctk.CTkLabel(self.todo_scroll_frame,
                         text="No tasks yet\nAdd one to get started",
                         font=ctk.CTkFont(family=FONT, size=11),
                         text_color=self.TEXT_MUTED,
                         justify="center").pack(pady=24)
            self.clear_btn.pack_forget()
        else:
            for todo in all_todos:
                self._create_todo_row(todo)
            if done:
                self.clear_btn.pack(side=tk.RIGHT)
            else:
                self.clear_btn.pack_forget()

        self.todo_count_label.configure(text=f"{len(active)} items")

    def _create_todo_row(self, todo):
        row = ctk.CTkFrame(self.todo_scroll_frame, fg_color="transparent")
        row.pack(fill=tk.X, padx=4, pady=1)

        # Check button
        check_text = "✓" if todo["done"] else "○"
        check_fg = ("#2fa572", "#106a43") if todo["done"] else "transparent"
        check_border = ("#2fa572", "#106a43") if todo["done"] else self.TEXT_MUTED
        check_text_color = "#ffffff" if todo["done"] else self.TEXT

        check = ctk.CTkButton(row, text=check_text, width=28, height=28,
                              corner_radius=14,
                              fg_color=check_fg,
                              border_width=2 if not todo["done"] else 0,
                              border_color=check_border,
                              text_color=check_text_color,
                              font=ctk.CTkFont(family=FONT, size=12),
                              hover_color=("#d4d4d4", "#404040") if not todo["done"]
                              else ("#2fa572", "#106a43"),
                              command=lambda t=todo: self._toggle_todo(t["id"]))
        check.pack(side=tk.LEFT, padx=(0, 10))

        # Text
        text_color = self.TEXT_MUTED if todo["done"] else self.TEXT
        if todo["done"]:
            text_font = ctk.CTkFont(family=FONT, size=12, slant="italic")
        else:
            text_font = ctk.CTkFont(family=FONT, size=12)

        text_label = ctk.CTkLabel(row, text=todo["text"], font=text_font,
                                  text_color=text_color, anchor="w",
                                  wraplength=260)
        text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Delete
        del_btn = ctk.CTkButton(row, text="×", width=24, height=24,
                                corner_radius=12,
                                fg_color="transparent",
                                text_color=self.TEXT_MUTED,
                                hover_color=("#fce4e4", "#4a2020"),
                                font=ctk.CTkFont(family=FONT, size=14),
                                command=lambda t=todo: self._delete_todo(t["id"]))
        del_btn.pack(side=tk.RIGHT)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = TomatoListApp()
    app.run()
