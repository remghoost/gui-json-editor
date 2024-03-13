import os
import re
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog


class JSONEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON Editor")
        self.json_data = {}
        self.last_file_path = ""
        if os.path.exists("last_file_path.json"):
            with open("last_file_path.json", "r") as file:
                self.last_file_path = json.load(file)

        self.tree = ttk.Treeview(self.root, columns=("Value"), selectmode="browse")
        self.tree.heading("#0", text="Key")
        self.tree.heading("Value", text="Value")
        self.tree.column("#0", width=200, stretch=True)
        self.tree.column("Value", width=200, stretch=True)
        self.tree.bind("<Double-1>", self.edit_item)  # Bind double-click event

        vsb = ttk.Scrollbar(orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(expand=True, fill="both")

        button_frame = tk.Frame(self.root)
        button_frame.pack(side="bottom", fill="x", padx=5, pady=5)

        self.load_button = tk.Button(button_frame, text="Load", command=self.load_json)
        self.load_button.pack(side="left", padx=5)

        self.save_button = tk.Button(
            button_frame,
            text="Save",
            command=lambda: self.save_json(self.ask_overwrite()),
        )
        self.save_button.pack(side="left", padx=5)

        self.root.bind(
            "<Control-s>",
            lambda event: self.save_json(self.ask_overwrite()),
        )

        self.sort_button = tk.Button(button_frame, text="Sort", command=self.sort_json)
        self.sort_button.pack(side="left", padx=5)

        self.search_frame = ttk.Frame(button_frame)
        self.search_frame.pack(side="left", fill="x", expand=True)

        self.search_type = tk.StringVar(value="Key")
        self.search_option = ttk.OptionMenu(
            self.search_frame, self.search_type, "Key", "Key", "Value"
        )
        self.search_option.pack(side="left", padx=5)

        self.search_entry = tk.Entry(self.search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", self.search_json)
        self.search_entry.bind("<BackSpace>", self.search_json)

        if self.last_file_path:
            self.load_json(
                self.last_file_path
            )  # Load the last loaded file automatically

        # Bind the <Return> key to the root window
        self.root.bind("<Return>", self.close_edit_entry)

        root.geometry("700x500")

        self.root.mainloop()

    def close_edit_entry(self, event):
        if hasattr(self.tree, "entry") and self.tree.entry:
            self.tree.entry.destroy()
            self.tree.entry = None

    def ask_overwrite(self):
        answer = messagebox.askyesnocancel(
            "Overwrite Existing File",
            "Do you want to overwrite the existing file?",
            parent=self.root,
        )
        if answer is None:  # User clicked Cancel
            return -1
        elif answer:  # User clicked Yes
            return self.last_file_path
        else:  # User clicked No
            return None

    def edit_item(self, event):
        item = self.tree.identify("item", event.x, event.y)
        if item:
            column = self.tree.identify_column(event.x)
            if column == "#0":  # If clicked on the key column
                self.edit_key(item)
            else:  # If clicked on the value column
                self.edit_value(item, event)  # Pass the event argument to edit_value

    def edit_key(self, item, event):
        if hasattr(self.tree, "entry") and self.tree.entry:
            self.tree.entry.destroy()

        self.tree.entry = tk.Entry(self.tree)
        current_key = self.tree.item(item, "text")
        self.tree.entry.insert(0, current_key)
        self.tree.entry.bind("<Return>", self.update_key)

        column = self.tree.identify_column(event.x)
        x, y, width, height = self.tree.bbox(item, column)
        self.tree.entry.place(x=x, y=y, width=width, height=height)

    def update_key(self, event):
        new_key = self.tree.entry.get()
        item = self.tree.focus()
        current_key = self.tree.item(item, "text")
        if new_key and new_key != current_key:
            self.json_data[new_key] = self.json_data.pop(current_key)
            self.tree.item(item, text=new_key)
        self.tree.entry.destroy()

    def edit_value(self, item, event):
        if hasattr(self.tree, "entry") and self.tree.entry:
            self.tree.entry.destroy()

        self.tree.entry = tk.Entry(self.tree)
        current_value = self.tree.item(item, "values")[0]
        self.tree.entry.insert(0, current_value)
        self.tree.entry.bind("<Return>", self.update_value)

        column = self.tree.identify_column(event.x)
        x, y, width, height = self.tree.bbox(item, column)
        self.tree.entry.place(x=x, y=y, width=width, height=height)

    def get_quoted_string(tacos, new_value):
        # Remove any leading or trailing double quotes
        print(f"value of new_value before stripping is: {new_value}")
        # print(f"value of tacos is: {tacos}")
        new_value = new_value.strip("")

        # Split the string into two parts: the quoted portion and the rest
        # quote_end = new_value.index("")
        # quoted_part = new_value[:quote_end]
        # unquoted_part = new_value[quote_end + 1 :]

        print(f"new_value after stripping is: {new_value}")

        # Return the quoted portion
        return new_value

    def update_value(self, event):
        new_value = self.tree.entry.get()
        item = self.tree.focus()
        current_value = self.tree.item(item, "values")[0]
        key = self.tree.item(item, "text")

        # Handle integers
        if new_value.isdigit():
            new_value = int(new_value)
        else:
            # Handle floats
            try:
                new_value = float(new_value)
            except ValueError:
                # Handle strings
                new_value = str(new_value)

        if new_value != current_value:
            self.json_data[key] = new_value
            self.tree.item(item, values=(new_value,))
        self.tree.entry.destroy()

    def undo_value_change(self, event):
        if self.undo_stack:
            key, value = self.undo_stack.pop()
            self.json_data[key] = value
            item = self.tree.selection()[0]  # Get the currently selected item
            self.tree.item(item, values=(value,))

    def load_json(self, file_path=None):
        if not file_path:
            file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])

        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                self.json_data = json.load(file)
                self.populate_tree()
                self.save_last_file_path(file_path)  # Save the last loaded file path

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        for key, value in self.json_data.items():
            self.tree.insert("", "end", text=key, values=(value,))

    def save_json(self, choice):
        if choice == -1:
            return
        if choice is None:
            choice = filedialog.asksaveasfilename(
                defaultextension=".json", filetypes=[("JSON files", "*.json")]
            )
        if choice:
            with open(choice, "w", encoding="utf-8") as file:
                json.dump(self.json_data, file, indent=4, ensure_ascii=False)
                file.write("\n")
            messagebox.showinfo("Save successful", "JSON file saved successfully!")

    def sort_json(self):
        self.json_data = dict(
            sorted(self.json_data.items(), key=lambda x: x[0].lower())
        )
        self.populate_tree()

    def search_json(self, event=None):
        search_term = self.search_entry.get().lower()
        search_type = self.search_type.get()

        if event and event.keysym == "BackSpace":
            # Handle backspace event
            self.populate_tree()
            self.search_entry.focus_set()  # Keep the focus on the search_entry
            self.search_entry.icursor(
                len(self.search_entry.get())
            )  # Move the cursor to the end of the text

        matching_items = []
        for item in self.tree.get_children():
            item_data = self.tree.item(item)
            key = item_data["text"].lower()
            value = item_data["values"][0]
            if search_type == "Value" and isinstance(value, str):
                value = value.lower()
            else:
                value = ""
            if search_term:
                if (search_type == "Key" and search_term in key) or (
                    search_type == "Value"
                    and isinstance(value, str)
                    and search_term in value
                ):
                    matching_items.append(item_data)

        # Clear the treeview
        self.tree.delete(*self.tree.get_children())

        # Repopulate the treeview with matching items
        for item_data in matching_items:
            self.tree.insert(
                "", "end", text=item_data["text"], values=item_data["values"]
            )

        if not search_term:
            # If search term is empty, repopulate the treeview with all items
            self.populate_tree()

    def load_last_file_path(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(script_dir, "last_file_path.json")

        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as file:
                last_file_path = json.load(file)
            return last_file_path
        else:
            return ""

    def save_last_file_path(self, file_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(script_dir, "last_file_path.json")

        with open(config_file, "w", encoding="utf-8") as file:
            json.dump(file_path, file)


if __name__ == "__main__":
    root = tk.Tk()
    app = JSONEditorApp(root)
    root.mainloop()
