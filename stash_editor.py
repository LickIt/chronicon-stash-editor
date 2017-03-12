import tkinter as tk
import tkinter.filedialog
import os
from decoder import Stash


class Application(tk.Frame):

    def __init__(self, master=None, title=None):
        super().__init__(master)

        self.stash_file_name = tk.StringVar()
        self.stash_size = tk.StringVar()
        self.stash_version = tk.StringVar()
        self.item_editor_frame = None
        self.stash = None
        self.items_list = tk.Variable()
        self.stat_variables = dict()

        master.title(title)
        master.minsize(width=1064, height=600)
        self.pack(expand=True, fill=tk.BOTH)
        self.create_widgets()

    def create_widgets(self):
        self.create_file_widgets()
        self.create_content_widgets()

    def create_file_widgets(self):
        frame = tk.Frame(self, padx=5, pady=10)
        frame.pack(fill=tk.X)

        label = tk.Label(frame, text="Stash File", justify=tk.LEFT, width=7)
        label.pack(side=tk.LEFT, padx=5)

        entry = tk.Entry(frame, textvariable=self.stash_file_name)
        entry.pack(expand=True, fill=tk.X, side=tk.LEFT, padx=5)

        select_button = tk.Button(
            frame, text="...", padx=5, command=self.choose_file)
        select_button.pack(side=tk.LEFT, padx=5)

        load_button = tk.Button(
            frame, text="Load", padx=5, command=self.load_file)
        load_button.pack(side=tk.LEFT, padx=5)

        save_button = tk.Button(
            frame, text="Save", padx=5, command=self.save_file)
        save_button.pack(side=tk.LEFT, padx=5)

    def create_content_widgets(self):
        item_list_frame = self.create_item_list_frame()
        item_list_frame.pack(fill=tk.BOTH, side=tk.LEFT)
        item_editor_frame = self.create_item_editor_frame()
        item_editor_frame.pack(expand=1, fill=tk.BOTH,
                               side=tk.LEFT, pady=(25, 5))

    def create_item_list_frame(self):

        frame = tk.Frame(self, pady=5, padx=5)

        top_frame = tk.Frame(frame)
        top_frame.pack(fill=tk.X)

        size_label = tk.Label(top_frame, text="Stash Size",
                              justify=tk.LEFT, width=7)
        size_label.pack(side=tk.LEFT, padx=5)

        stash_size_entry = tk.Entry(
            top_frame, width=5, textvariable=self.stash_size)
        stash_size_entry.pack(side=tk.LEFT, padx=5)

        version_value_label = tk.Label(
            top_frame, width=5, textvariable=self.stash_version)
        version_value_label.pack(side=tk.RIGHT)

        version_label = tk.Label(top_frame, text="Version")
        version_label.pack(side=tk.RIGHT)

        items_list = tk.Listbox(frame, width=40, listvariable=self.items_list)
        items_list.bind("<<ListboxSelect>>", self.item_selected)
        items_list.pack(expand=1, fill=tk.Y, pady=5, padx=5)

        return frame

    def create_item_editor_frame(self):
        frame = tk.Frame(self, padx=5, pady=5)
        self.item_editor_frame = frame
        return frame

    def choose_file(self):
        fname = tkinter.filedialog.askopenfilename(
            initialdir=os.path.join(
                os.getenv("LOCALAPPDATA", ""), "Chronicon", "save"),
            filetypes=(("Stash files", "*.stash"),))

        if fname:
            self.stash_file_name.set(fname)

    def load_file(self):
        fname = self.stash_file_name.get()
        if not fname:
            return

        stash = Stash(fname)
        self.stash = stash
        self.load_stash()

    def save_file(self):
        fname = self.stash_file_name.get()
        os.replace(fname, os.path.join(os.path.dirname(
            fname), "_" + os.path.basename(fname)))
        with open(fname, "w") as f:
            f.write(self.stash.write())

    def load_stash(self):
        self.stash_version.set(self.stash.version)
        self.stash_size.set(self.stash.size)

        items = self.stash.items[:self.stash.size]
        self.items_list.set(["{:4d}: {}".format(idx + 1, i.get_name())
                             for idx, i in enumerate(items)])

    def item_selected(self, event):
        listbox = event.widget
        index = listbox.curselection()
        if index:
            self.load_item(index[0])

    def load_item(self, index):
        item = self.stash.items[index]
        stats = item.stats
        stats.sort(key=lambda x: x.name)

        self.stat_variables.clear()

        frame = self.item_editor_frame
        for widget in frame.winfo_children():
            widget.destroy()

        for idx, stat in enumerate(stats):
            per_row = 3
            row = idx // per_row
            col = per_row * (idx % per_row)
            is_last_col = (idx % per_row) == (per_row - 1)

            label = tk.Label(frame, text=stat.name, width=15, anchor=tk.E)
            label.grid(row=row, column=col, padx=5, pady=3)

            variable_name = "{}_{}".format(index, stat.name)
            variable = tk.StringVar(value=stat.value, name=variable_name)
            variable.trace_add("write", lambda name, *
                               args: self.item_stat_changed(name, index))
            self.stat_variables[variable_name] = variable

            entry = tk.Entry(frame, textvariable=variable, width=20)
            entry.grid(row=row, column=col + 1,
                       padx=(5, 10 if is_last_col else 15), pady=3)

    def item_stat_changed(self, name, idx):
        variable = self.stat_variables[name]
        value = variable.get()
        stat_name = name.split("_", 1)[1]
        stat = [s for s in self.stash.items[
            idx].stats if s.name == stat_name][0]

        try:
            stat.set_value(value)
        except ValueError:
            variable.set(stat.value)

if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root, "Chronicon Stash Editor")
    root.iconbitmap("icon.ico")
    app.mainloop()
