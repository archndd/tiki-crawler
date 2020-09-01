from utils import CURRENTDATE

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")

import tkinter as tk
import numpy as np
import logging
import webbrowser
import datetime
from gather_data import PriceBook


def reformat_large_tick_values(tick_val, pos=None):
    """
    Turns large tick values (in the billions, millions and thousands) such as 4500 into 4.5K and also appropriately turns 4000 into 4K (no zero after the decimal).
    """
    if tick_val >= 1000:
        val = round(tick_val/1000, 1)
        new_tick_format = '{:}K'.format(val)
    elif tick_val < 1000:
        new_tick_format = round(tick_val, 1)
    else:
        new_tick_format = tick_val

    # make new_tick_format into a string value
    new_tick_format = str(new_tick_format)
    
    # code below will keep 4.5M as is but change values such as 4.0M to 4M since that zero after the decimal isn't needed
    index_of_decimal = new_tick_format.find(".")
    
    if index_of_decimal != -1:
        value_after_decimal = new_tick_format[index_of_decimal+1]
        if value_after_decimal == "0":
            # remove the 0 after the decimal point since it's not needed
            new_tick_format = new_tick_format[0:index_of_decimal] + new_tick_format[index_of_decimal+2:]
            
    return new_tick_format


class Visualizer(tk.Frame):
    color = ["blue", "orange", "green", "red", "purple", "brown", "pink", "gray", "olive", "cyan"]
    def __init__(self, parent, price_book, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.price_book = price_book

        self.figure = Figure(figsize=(4,4), dpi=100)
        self.sub_graph = self.figure.add_subplot(111)
        box = self.sub_graph.get_position()
        self.figure.subplots_adjust(left=0.05, right=0.84, bottom=0.05, top=0.96)

        self.book_url = {}
        self.force_update = False

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side='top', fill='both', expand=True)

        self.canvas.mpl_connect("key_press_event", lambda event: key_press_handler(event, self.canvas, self.toolbar))

    def init_chart(self, constrain, key):
        if key is not None:
            self.key = key
        if constrain is not None:
            self.constrain = constrain

        self.book_url = {}
        self.sub_graph.clear()

        self.sub_graph.set_ylabel(self.key)

        tmp = next(iter(self.price_book.data.values()))
        if CURRENTDATE not in tmp["price"]:
            self.price_book.update()

    def on_click(self, event):
        url = self.book_url[event.artist.get_label()]
        webbrowser.open("https://tiki.vn/{}".format(url))

    def update_graph(self):
        self.plot_data_with_constrain(None, None)


class LineVisualizer(Visualizer):
    def __init__(self, parent, price_book, *args, **kwargs):
        super().__init__(parent, price_book, *args, **kwargs)

    def plot_data_with_constrain(self, constrain, key):
        super().init_chart(constrain, key)

        # Plot sorted data by key so that line and legend have the same order
        for prod_id, prod in sorted(self.price_book.data.items(), key=lambda prod: prod[1]["price"][CURRENTDATE][self.key], reverse=True):
            try:
                if self.constrain(prod):
                    date = matplotlib.dates.date2num([datetime.datetime.strptime(d, '%d-%m-%Y') for d in prod["price"].keys()])
                    yval = [k[self.key] for k in prod["price"].values()]

                    self.sub_graph.plot_date(date, yval, '-', marker="o", label=prod["name"])
                    self.book_url[prod["name"]] = self.price_book.data[prod_id]["url_path"]
                    for x,y in zip(date, yval):
                        self.sub_graph.annotate(reformat_large_tick_values(y), (x, y), textcoords="offset points", xytext=(0, 5), ha='center')
            except:
                pass

        self.sub_graph.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d-%m"))
        self.sub_graph.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(reformat_large_tick_values))

        legend = self.sub_graph.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        for line in legend.get_lines():
            line.set_picker(True)
            line.set_pickradius(5)

        self.canvas.draw()
        self.canvas.mpl_connect('pick_event', self.on_click)

    def plot_data(self, xa, ya, xname="Date", yname="Price"):
        self.figure.subplots_adjust(left=0.075, right=0.975, bottom=0.05, top=0.95)
        self.sub_graph.clear()
        box = self.sub_graph.get_position()

        self.sub_graph.set_xlabel(xname)
        self.sub_graph.set_ylabel(yname)

        self.sub_graph.plot(xa, ya, marker="o", c=np.random.choice(self.color))
        for x,y in zip(xa, ya):
            self.sub_graph.annotate(reformat_large_tick_values(y), (x, y), textcoords="offset points", xytext=(0, 5), ha='center')

        self.sub_graph.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(reformat_large_tick_values))
        self.canvas.draw()


class BarVisualizer(Visualizer):
    def __init__(self, parent, price_book, *args, **kwargs):
        super().__init__(parent, price_book, *args, **kwargs)
        self.width = 0.6

    def navigation_format(self, x, y):
        m = x % 1
        if not (m <= self.width / 2  or (1 - self.width / 2) <= m):
            return ""
        index = int(x + self.width / 2)
        try:
            name = self.sub_graph.containers[index].get_label()
            p = self.sub_graph.containers[index].patches[0].get_height()

            return "{} | {}".format(name, reformat_large_tick_values(p))
        except:
            return ""

    def plot_data_with_constrain(self, constrain, key, date=None):
        super().init_chart(constrain, key)
        if date is None:
            date = CURRENTDATE
        prev_date = datetime.datetime.strptime(date, "%d-%m-%Y") - datetime.timedelta(days=1)
        prev_date = prev_date.strftime("%d-%m-%Y")

        self.sub_graph.set_title(date)
        # Plot sorted data by key so that line and legend have the same order
        for prod_id, prod in sorted(self.price_book.data.items(), key=lambda prod: prod[1]["price"][CURRENTDATE][self.key], reverse=True):
            try:
                if self.constrain(prod):
                    name = prod["name"]
                    yval = prod["price"][date][self.key]
                    try:
                        prev_yval = prod["price"][prev_date][self.key]
                        delta_yval = yval - prev_yval
                    except:
                        delta_yval = 0
                    # Valu increase
                    if delta_yval > 0:
                        self.sub_graph.bar(name, prev_yval, width=self.width, label=name)
                        self.sub_graph.bar(name, delta_yval, color='r', width=self.width, bottom=prev_yval)
                        self.sub_graph.annotate(reformat_large_tick_values(yval), (name, yval), textcoords="offset points", xytext=(0, 10), ha='center')
                    # Value decrease
                    elif delta_yval < 0:
                        self.sub_graph.bar(name, yval, width=self.width, label=name)
                        self.sub_graph.bar(name, -1*delta_yval, color='g', width=self.width, bottom=yval)
                        self.sub_graph.annotate(reformat_large_tick_values(yval), (name, prev_yval), textcoords="offset points", xytext=(0, 10), ha='center')
                    # Value unchange
                    else:
                        self.sub_graph.bar(name, yval, width=self.width, label=name)
                        self.sub_graph.annotate(reformat_large_tick_values(yval), (name, yval), textcoords="offset points", xytext=(0, 10), ha='center')

                    self.book_url[name] = self.price_book.data[prod_id]["url_path"]
            except:
                pass

        self.sub_graph.format_coord = self.navigation_format
        self.sub_graph.xaxis.set_visible(False)
        self.sub_graph.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(reformat_large_tick_values))

        legend = self.sub_graph.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        # TODO: fix legend
        # for line in legend.get_patches():
        #     line.set_picker(True)

        self.canvas.draw()
        self.canvas.mpl_connect('pick_event', self.on_click)


if __name__ == "__main__": 
    logger = logging.getLogger('visualizer')
    logger.setLevel(logging.DEBUG)
    # create a file handler
    handler = logging.FileHandler('app.log')
    handler.setLevel(logging.DEBUG)
    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(handler)

    price_book = PriceBook()
    visualizer = Visualizer(price_book)
    visualizer.all()
    # visualizer.discount_40()


