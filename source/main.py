from utils import CURRENTDATE
from widget import ChecklistBox, RadioBox

import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
from PIL import Image, ImageTk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler

import numpy as np
import webbrowser
from gather_data import PriceBook
from visualize import Visualizer


class BetterButton(tk.Button):
    def __init__(self, *args, width=20, height=2, **kwargs):
        super().__init__(*args, width=width, height=height, **kwargs)

class BetterEntry(tk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind("<<Paste>>", self.custom_paste)
        self.bind('<Control-a>', self.select_all)

    def custom_paste(self, event=None):
        try:
            event.widget.delete("sel.first", "sel.last")
        except:
            pass
        event.widget.insert("insert", event.widget.clipboard_get())
        return "break"

    def select_all(self, event=None):
        self.select_range(0, 'end')
        return 'break'


class DetailWindow(tk.Toplevel):
    def __init__(self, parent, prod_id, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.geometry("900x600")
        self.prod = price_book[prod_id]
        self.wm_title(self.prod["name"])

        self.small_visualizer = Visualizer(self, None)
        self.info_frame = tk.Frame(self)

        date = []
        for d in self.prod["price"].keys():
            d = d.split('-')[0:2]
            date.append('-'.join(d))
        price = [k["price"] for k in self.prod["price"].values()]
        self.small_visualizer.plot_data(date, price)

        thumbnail = ImageTk.PhotoImage(Image.open(self.prod["thumbnail"]).resize((150, 150)))
        self.thumbnail_label = tk.Label(self.info_frame, image=thumbnail, anchor="w")
        self.thumbnail_label.image = thumbnail
        self.name_label = tk.Label(self.info_frame, text=self.prod["name"], anchor="w")
        self.producer_label = tk.Label(self.info_frame, text=self.prod["author"]["name"], anchor="w")
        self.view_button = BetterButton(self.info_frame, text="View this on browser", command=self.view_on_browser)

        self.thumbnail_label.grid(row=0, rowspan=2, column=0)
        self.name_label.grid(row=0, column=1)
        self.producer_label.grid(row=1, column=1, sticky="w")
        self.view_button.grid(row=1, column=2)

        self.info_frame.pack(fill="x", expand=False)
        self.small_visualizer.pack(fill="both", expand=True)

    def view_on_browser(self):
        webbrowser.open("https://tiki.vn/{}".format(self.prod["url_path"]))


class EditFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent

        self.check_box = ChecklistBox(self, background="white")
        self.init_checkbox()
        self.delete_button = BetterButton(self, text="Delete", command=self.delete_selected)
        self.save_button = BetterButton(self, text="Save", command=lambda: [price_book.dump_to_json(), self.update_status_label("Dumping to json done")])
        self.update_button = BetterButton(self, text="Update data", command=self.update_price_book)
        self.view_selected_button = BetterButton(self, text="View selected", command=self.view_selected)
        self.insert_entry = BetterEntry(self, width=10, highlightbackground="black", borderwidth=10, relief="flat", selectbackground="#DFDFDF")
        self.insert_button = BetterButton(self, text="Add", command=self.insert)
        self.status_label = tk.Label(self, text="Waiting", anchor='w', background="#EEEEEE")

        self.status_label.configure(width=12, height=1)

        for i in range(3):
            tk.Grid.rowconfigure(self, i, weight=1)
            tk.Grid.columnconfigure(self, i, weight=1)

        self.check_box.grid(row=0, column=0, rowspan=4, columnspan=3, sticky="nswe")
        self.delete_button.grid(row=0, column=3, padx=10, sticky="w")
        self.save_button.grid(row=1, column=3, padx=10, sticky="w")
        self.update_button.grid(row=2, column=3, padx=10, sticky="w")
        self.view_selected_button.grid(row=3, column=3, padx=10, sticky="w")
        self.insert_entry.grid(row=4, column=0, columnspan=3, pady=10, sticky="we")
        self.insert_button.grid(row=4, column=3, padx=10, sticky="w")
        self.status_label.grid(row=5, column=0, columnspan=4, padx=10, pady=(0, 5), ipady=5, sticky='we')

    def init_checkbox(self):
        for prod_id, prod in price_book.data.items():
            p_producer = ""
            if "author" in prod:
                p_producer = prod["author"]["name"]
            elif "brand" in prod:
                p_producer = prod["brand"]["name"]

            text = " {} - {} | {}".format(prod["name"], p_producer, "Not update yet")
            if CURRENTDATE in prod["price"]:
                text = " {} - {} | {}".format(prod["name"], p_producer, format(prod["price"][CURRENTDATE]["price"], ','))
            self.check_box.insert(text=text, cb_id=prod_id, onvalue=prod_id, offvalue="")

    def update_status_label(self, text=""):
        self.status_label.configure(text=text)

    def update_price_book(self):
        self.update_status_label("Updating price book")
        self.status_label.update()
        price_book.update()
        for cb_id, (_, cb) in self.check_box.boxes.items():
            prod = self.price_book[cb_id]
            text = " {} - {} | {}".format(prod["name"], prod["author"], "Not update yet")
            if CURRENTDATE in prod["price"]:
                text = " {} - {} | {}".format(prod["name"], prod["author"], format(prod["price"][CURRENTDATE]["price"], ','))
            self.check_box.update_text_cb(cb_id=cb_id, text=text)
        self.parent.graph_frame.visualizer_frame.update_graph()
        self.update_status_label("Update price book done")

    def insert(self):
        url = self.insert_entry.get().strip().split('?')[0]
        success, prod_id = price_book.insert_product(url, "INSERT from main")
        if success:
            prod = price_book[prod_id]
            text = " {} - {} | {}".format(prod["name"], prod["author"]["name"], "Not update yet")
            if CURRENTDATE in prod["price"]:
                text = " {} - {} | {}".format(prod["name"], prod["author"]["name"], format(prod["price"][CURRENTDATE]["price"], ','))
            self.check_box.insert(text=text, cb_id=prod_id, onvalue=prod_id, offvalue="")

            self.update_status_label("Insert done")
            self.parent.graph_frame.visualizer_frame.update_graph()
        else:
            self.update_status_label("Already inserted")

        self.insert_entry.delete(0, 'end')

    def view_selected(self):
        for prod_id, _, _ in self.check_box.get_checked_items():
            webbrowser.open("https://tiki.vn/{}".format(price_book.data[prod_id]["url_path"]))

    def delete_selected(self):
        count = 0
        for val, cb, cb_id in self.check_box.get_checked_items():
            price_book.delete_product(val, "DELETE from main")
            cb.destroy()
            del self.check_box.boxes[cb_id]
            count += 1

        if count != 0:
            self.update_status_label("Delete {} items".format(count))
            self.parent.graph_frame.visualizer_frame.update_graph()

    def view_prod_detail(self, prod_id):
        win = DetailWindow(self, prod_id)


class GraphFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        
        self.visualizer_frame = Visualizer(parent=self, price_book=price_book)
        choices = (["Price", "price"], ["Original Price", "list_price"], ["Discount", "discount"], ["Discount Rate", "discount_rate"])
        self.ok_button = BetterButton(self, text="Ok", command=self.filter)
        self.radio_box = RadioBox(self, choices, 2)
        self.upper_bound_label = tk.Label(self, text="Upper")
        self.lower_bound_label = tk.Label(self, text="Lower")
        self.upper_bound_entry = BetterEntry(self)
        self.lower_bound_entry = BetterEntry(self)

        self.upper_bound_entry.bind("<Return>", self.filter)
        self.lower_bound_entry.bind("<Return>", self.filter)

        for i in range(4):
            tk.Grid.columnconfigure(self, i, weight=1)
        tk.Grid.rowconfigure(self, 0, weight=1)

        self.visualizer_frame.grid(row=0, column=0, columnspan=4, sticky="nswe")
        self.lower_bound_label.grid(row=1, column=0, padx=10, pady=10)
        self.upper_bound_label.grid(row=1, column=1, padx=10, pady=10)
        self.lower_bound_entry.grid(row=2, column=0, padx=10, pady=10)
        self.upper_bound_entry.grid(row=2, column=1, padx=10, pady=10)
        self.radio_box.grid(row=1, column=2, rowspan=2, padx=10, pady=10)
        self.ok_button.grid(row=1, column=3, rowspan=2, padx=10, pady=10)

        self.ok_button.invoke()

    def filter(self, event=None):
        lower = self.lower_bound_entry.get()
        upper = self.upper_bound_entry.get()
        key = self.radio_box.get_checked_items()
        if lower and upper:
            constrain = lambda prod: int(upper) >= prod["price"][CURRENTDATE][key] >= int(lower)
        elif lower:
            constrain = lambda prod: prod["price"][CURRENTDATE][key] >= int(lower)
        elif upper:
            constrain = lambda prod: int(upper) >= prod["price"][CURRENTDATE][key]
        else:
            constrain = lambda prod: True
        self.visualizer_frame.plot_data_with_constrain(constrain, key)


class MainApplication(ttk.Notebook):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.parent = parent
        self.parent.title("Tiki Visualizer")

        s = ttk.Style()
        s.theme_create("MyStyle", parent="alt", settings={
                "TNotebook": {"configure": {"tabmargins": [0, 0, 0, 0]},
                              },
                "TNotebook.Tab": {
                    "configure": {"padding": [10, 10], "background": "#CCCCCC", "font" : ('Liberation', '11', 'bold')},
                    "map":       {"background": [("selected", "#EEEEEE"), ("active", "#DDDDDD")],
                                  "expand": [("selected", [1, 1, 1, 0])]}
                }})

        s.theme_use("MyStyle")
        bg = "#EEEEEE"

        self.edit_frame = EditFrame(self, background=bg)
        self.graph_frame = GraphFrame(self, background=bg)
        self.add(self.graph_frame, text="Graph")
        self.pack(padx=20, pady=20, expand=True, fill="both")
        self.add(self.edit_frame, text="Edit")
        self.pack(padx=20, pady=20, expand=True, fill="both")


if __name__ == "__main__":
    price_book = PriceBook()
    root = tk.Tk()
    default_font = tkFont.nametofont("TkDefaultFont")
    default_font.configure(family="Roboto Regular", size=12, weight="normal")
    root.option_add("*Font", default_font)
    root.geometry("1300x750")

    main = MainApplication(root)
    main.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
