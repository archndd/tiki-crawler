import tkinter as tk

class ChecklistBox(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent

        self.canvas = tk.Canvas(self, **kwargs)
        self.vscroll_bar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.hscroll_bar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.checkbox_frame = tk.Frame(self.canvas, **kwargs)
        self.canvas.configure(yscrollcommand=self.vscroll_bar.set)
        self.canvas.configure(xscrollcommand=self.hscroll_bar.set)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.hscroll_bar.grid(row=1, column=0, sticky="ew")
        self.vscroll_bar.grid(row=0, column=1, sticky="ns")
        self.canvas.grid(row=0, column=0, sticky="nswe")

        self.window = self.canvas.create_window((0,0), window=self.checkbox_frame, anchor="nw", tags="self.checkbox_frame")

        self.checkbox_frame.bind("<Configure>", self.onFrameConfigure)
        self.canvas.bind("<Configure>", self.onCanvasConfigure)

        self.boxes = {}

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def onCanvasConfigure(self, event):
        minWidth = self.checkbox_frame.winfo_reqwidth()
        minHeight = self.checkbox_frame.winfo_reqheight()

        if self.winfo_width() >= minWidth:
            newWidth = self.winfo_width()
            self.hscroll_bar.grid_remove()
        else:
            newWidth = minWidth
            self.hscroll_bar.grid()

        if self.winfo_height() >= minHeight:
            newHeight = self.winfo_height()
            self.vscroll_bar.grid_remove()
        else:
            newHeight = minHeight
            self.vscroll_bar.grid()

        self.canvas.itemconfig(self.window, width=newWidth, height=newHeight)

    def get_checked_items(self):
        values = []
        for cb_id, (var, cb) in self.boxes.items():
            value = var.get()
            if value:
                values.append([value, cb, cb_id])
                cb.deselect()
        return values

    def insert(self, text="", cb_id="", onvalue="", offvalue="", **kwargs):
        bg = self.cget("background")
        var = tk.StringVar(value="")
        cb = tk.Checkbutton(self.checkbox_frame, variable=var, text=text,
                            onvalue=onvalue, offvalue=offvalue,
                            anchor="w", background=bg,
                            relief="flat", highlightthickness=0, **kwargs)
        cb.bind("<Double-Button-1>", lambda event: self.parent.view_prod_detail(onvalue))
        # cb.configure(font=font)
        if not self.boxes:
            cb.pack(side="top", fill="x", ipady=5, ipadx=10, pady=(10,0))
        else:
            cb.pack(side="top", fill="x", ipady=5, ipadx=10)
        self.boxes[onvalue] = (var, cb)

    def update_text_cb(self, cb_id, text):
        cb = self.boxes[cb_id][1]
        cb.configure(text=text)

    def deleted_selected_cb(self):
        count = 0
        for val, cb, cb_id in self.get_checked_items():
            cb.destroy()
            del self.boxes[cb_id]
            count += 1
        return count

    def delete_cb(self, cb_id):
        cb = self.boxes[cb_id][1]
        cb.destroy()
        del self.boxes[cb_id]

class RadioBox(tk.Frame):
    def __init__(self, parent, choices, choice_per_col=1, **kwargs):
        bg = parent.cget("background")
        super().__init__(parent, background=bg, **kwargs)

        self.choice_per_col = choice_per_col
        self.size = 0
        self.var = tk.StringVar(value="price")
        if choices:
            self.insert(choices)

    def get_checked_items(self):
        return self.var.get()

    def insert(self, choices, **kwargs):
        bg = self.cget("background")
        for text, val in choices:
            rb = tk.Radiobutton(self, variable=self.var, text=text,
                                value=val,
                                anchor="w", background=bg,
                                relief="flat", highlightthickness=0, **kwargs)
            row = self.size // self.choice_per_col
            col = self.size % self.choice_per_col
            rb.grid(row=row, column=col, ipady=5, ipadx=10, sticky='nswe')
            self.size += 1
            # rb.pack(side="top", fill="both", expand=True , ipady=5, ipadx=10)
