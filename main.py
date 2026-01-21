import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
from fractions import Fraction
import json

class HeirloomApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Heirloom Head Right Calculator")
        self.root.geometry("800x600")

        self.instructions_label = tk.Label(self.root, text="1. Click 'Add Original Owner' to add a trunk to the tree.\n2. Select a person in the tree and click 'Add Heir' to add a successor.\n3. Click 'Generate Report' to see the final claimants and their shares.", justify=tk.LEFT)
        self.instructions_label.pack(anchor="w", padx=10, pady=5)

        self.tree = ttk.Treeview(self.root, columns=("Name", "Share"), show="tree headings")
        self.tree.heading("#0", text="Heirloom Tree")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Share", text="Share")
        self.tree.pack(expand=True, fill="both")

        self.shares = {}
        self.allocated_shares = {}

        self.total_shares_label = tk.Label(self.root, text="", anchor="e", padx=10)
        self.total_shares_label.pack(side="bottom", fill="x")

        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(fill="x", pady=10)

        self.add_owner_button = tk.Button(self.button_frame, text="Add Original Owner", command=self.add_original_owner)
        self.add_owner_button.pack(side="left", padx=10)

        self.add_heir_button = tk.Button(self.button_frame, text="Add Heir", command=self.add_heir)
        self.add_heir_button.pack(side="left", padx=10)

        self.convey_share_button = tk.Button(self.button_frame, text="Convey Share", command=self.convey_share)
        self.convey_share_button.pack(side="left", padx=10)

        self.generate_report_button = tk.Button(self.button_frame, text="Generate Report", command=self.generate_report)
        self.generate_report_button.pack(side="left", padx=10)

        self.save_button = tk.Button(self.button_frame, text="Save", command=self.save_tree)
        self.save_button.pack(side="right", padx=10)

        self.load_button = tk.Button(self.button_frame, text="Load", command=self.load_tree)
        self.load_button.pack(side="right", padx=10)

        self.clear_all_button = tk.Button(self.button_frame, text="Clear All", command=self.clear_all)
        self.clear_all_button.pack(side="right", padx=10)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.edit_selected)
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cancel")

        self.tree.bind("<Button-3>", self.show_context_menu)
        
        self.update_total_shares()

    def show_context_menu(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region not in ("cell", "tree"):
            return

        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def clear_all(self):
        if messagebox.askokcancel("Clear All", "Are you sure you want to clear the entire tree?"):
            self.tree.delete(*self.tree.get_children())
            self.shares.clear()
            self.update_total_shares()

    def update_total_shares(self):
        claimants = []
        for item in self.tree.get_children():
            self._find_claimants(item, claimants)
        
        total_share = sum(share for name, share in claimants)
        percentage = float(total_share) * 100
        
        color = "black"
        if claimants:
            if total_share < 1:
                color = "dark goldenrod"
            elif total_share > 1:
                color = "salmon"
            elif total_share == 1:
                color = "forest green"

        self.total_shares_label.config(text=f"Total Shares: {total_share} ({percentage:.4f}%)", fg=color)

    def save_tree(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not filename:
            return

        data = []
        def traverse(item):
            node = {
                "id": item,
                "parent": self.tree.parent(item),
                "name": self.tree.item(item, "text"),
                "share": str(self.shares.get(item, "0/1")),
                "allocated_share": str(self.allocated_shares.get(item, "0/1"))
            }
            data.append(node)
            for child in self.tree.get_children(item):
                traverse(child)

        for item in self.tree.get_children():
             traverse(item)

        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Success", "Tree saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save tree: {e}")

    def load_tree(self):
        filename = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not filename:
            return

        if not messagebox.askokcancel("Load Tree", "Loading a tree will clear the current one. Continue?"):
            return

        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            self.tree.delete(*self.tree.get_children())
            self.shares.clear()
            self.allocated_shares.clear()
            
            for node in data:
                item_id = node["id"]
                parent_id = node["parent"]
                name = node["name"]
                share = Fraction(node["share"])
                allocated_share = Fraction(node["allocated_share"])

                # If parent is empty string, it's root level
                if parent_id == "":
                     parent_id = ""

                # Insert with same ID
                self.tree.insert(parent_id, "end", iid=item_id, text=name, values=(name, str(share)))
                self.shares[item_id] = share
                self.allocated_shares[item_id] = allocated_share

            self.update_total_shares()
            messagebox.showinfo("Success", "Tree loaded successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tree: {e}")

    def add_original_owner(self):
        num_original_owners = len(self.tree.get_children())
        default_share = Fraction(1, num_original_owners + 1)
        
        dialog = AddOriginalOwnerDialog(self.root, default_share)
        self.root.wait_window(dialog.top)

        if dialog.name and dialog.share_fraction is not None:
            item_id = self.tree.insert("", "end", text=dialog.name, values=(dialog.name, str(dialog.share_fraction)))
            self.shares[item_id] = dialog.share_fraction
            self.allocated_shares[item_id] = dialog.share_fraction
            self.update_total_shares()

    def convey_share(self):
        source_id = self.tree.selection()
        if not source_id:
            messagebox.showerror("Error", "Please select a source node.")
            return
        source_id = source_id[0]

        source_children = self.tree.get_children(source_id)
        children_total_share = sum(self.allocated_shares.get(child, 0) for child in source_children)
        source_remainder = self.shares[source_id] - children_total_share

        if source_remainder <= 0:
            messagebox.showerror("Error", "Source node has no remainder to convey.")
            return

        all_nodes = self._get_all_nodes()
        nodes = [node for node in all_nodes if node[1] != source_id] # Exclude source from destinations

        dialog = ConveyShareDialog(self.root, nodes, source_remainder)
        self.root.wait_window(dialog.top)

        if dialog.conveyances:
            total_conveyed_share = sum(share for _, share in dialog.conveyances)

            # Update source
            self.shares[source_id] -= total_conveyed_share
            self.tree.item(source_id, values=(self.tree.item(source_id, 'text'), str(self.shares[source_id])))

            # Update destinations
            for dest_id, share_to_convey in dialog.conveyances:
                old_dest_share = self.shares[dest_id]
                new_dest_share = old_dest_share + share_to_convey
                self.shares[dest_id] = new_dest_share
                self.tree.item(dest_id, values=(self.tree.item(dest_id, 'text'), str(new_dest_share)))
                if old_dest_share != 0:
                    share_change_factor = new_dest_share / old_dest_share
                    self._update_child_shares(dest_id, share_change_factor)

            self.update_total_shares()

    def add_heir(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a parent from the tree.")
            return

        selected_item = selected_item[0]
        dialog = AddHeirDialog(self.root)
        self.root.wait_window(dialog.top)
        
        if dialog.name and dialog.share_fraction:
            parent_share = self.shares[selected_item]
            heir_share = parent_share * dialog.share_fraction
            
            item_id = self.tree.insert(selected_item, "end", text=dialog.name, values=(dialog.name, str(heir_share)))
            self.shares[item_id] = heir_share
            self.allocated_shares[item_id] = heir_share
            self.update_total_shares()

    def edit_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select an item to edit.")
            return

        selected_item = selected_item[0]
        original_name = self.tree.item(selected_item, "text")
        old_share = self.shares[selected_item]

        parent_item = self.tree.parent(selected_item)
        if parent_item:
            parent_share = self.shares[parent_item]
            if parent_share == 0 and old_share == 0:
                 original_relative_share = 0
            elif parent_share == 0 and old_share !=0:
                messagebox.showerror("Error", "Cannot edit heir of a parent with zero share.")
                return
            else:
                original_relative_share = old_share / parent_share
            
            dialog = EditDialog(self.root, original_name, original_relative_share)
            self.root.wait_window(dialog.top)

            if dialog.name and dialog.share_fraction is not None:
                new_share = parent_share * dialog.share_fraction
                self.tree.item(selected_item, text=dialog.name, values=(dialog.name, str(new_share)))
                self.shares[selected_item] = new_share
                self.allocated_shares[selected_item] = new_share

                if new_share == 0:
                    self._set_children_shares_to_zero(selected_item)
                elif old_share == 0:
                    if self.tree.get_children(selected_item):
                        messagebox.showwarning("Warning", "The original share was 0. Children's shares cannot be automatically updated and are now likely incorrect. Please edit them manually.")
                else:
                    share_change_factor = new_share / old_share
                    self._update_child_shares(selected_item, share_change_factor)
                self.update_total_shares()

        else: # Original Owner
            dialog = EditDialog(self.root, original_name, old_share)
            self.root.wait_window(dialog.top)

            if dialog.name and dialog.share_fraction is not None:
                new_share = dialog.share_fraction
                self.tree.item(selected_item, text=dialog.name, values=(dialog.name, str(new_share)))
                self.shares[selected_item] = new_share
                self.allocated_shares[selected_item] = new_share

                if new_share == 0:
                    self._set_children_shares_to_zero(selected_item)
                elif old_share == 0:
                    if self.tree.get_children(selected_item):
                        messagebox.showwarning("Warning", "The original share was 0. Children's shares cannot be automatically updated and are now likely incorrect. Please edit them manually.")
                else:
                    share_change_factor = new_share / old_share
                    self._update_child_shares(selected_item, share_change_factor)
                self.update_total_shares()

    def _update_child_shares(self, item, factor):
        for child in self.tree.get_children(item):
            old_child_share = self.shares[child]
            new_child_share = old_child_share * factor
            self.shares[child] = new_child_share
            
            if child in self.allocated_shares:
                self.allocated_shares[child] = self.allocated_shares[child] * factor
            
            self.tree.item(child, values=(self.tree.item(child, "text"), str(new_child_share)))
            self._update_child_shares(child, factor)

    def _set_children_shares_to_zero(self, item):
        for child in self.tree.get_children(item):
            self.shares[child] = Fraction(0)
            self.allocated_shares[child] = Fraction(0)
            self.tree.item(child, values=(self.tree.item(child, "text"), "0/1"))
            self._set_children_shares_to_zero(child)

    def delete_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select an item to delete.")
            return

        selected_item = selected_item[0]
        is_original_owner = not self.tree.parent(selected_item)

        def delete_children(item):
            for child in self.tree.get_children(item):
                delete_children(child)
                if child in self.shares:
                    del self.shares[child]
                if child in self.allocated_shares:
                    del self.allocated_shares[child]
                self.tree.delete(child)

        delete_children(selected_item)
        
        if selected_item in self.shares:
            del self.shares[selected_item]
        if selected_item in self.allocated_shares:
            del self.allocated_shares[selected_item]
        self.tree.delete(selected_item)

        if is_original_owner:
            self._update_original_owner_shares()
        else:
            self.update_total_shares()

    def _find_claimants(self, item, claimants):
        children = self.tree.get_children(item)
        if not children:
            claimants.append((self.tree.item(item, "text"), self.shares[item]))
            return

        children_share = sum(self.allocated_shares.get(child, Fraction(0)) for child in children)
        parent_share = self.shares[item]

        if parent_share > children_share:
            claimants.append((self.tree.item(item, "text"), parent_share - children_share))

        for child in children:
            self._find_claimants(child, claimants)

    def _get_all_nodes(self):
        nodes = []
        def traverse(item):
            nodes.append((self.tree.item(item, "text"), item))
            for child in self.tree.get_children(item):
                traverse(child)
        
        for item in self.tree.get_children():
            traverse(item)
        return nodes

    def _update_original_owner_shares(self):
        original_owners = self.tree.get_children()
        if not original_owners:
            return

        new_share = Fraction(1, len(original_owners))

        for owner_id in original_owners:
            old_share = self.shares.get(owner_id, new_share) # Use new_share as default for new owners
            self.shares[owner_id] = new_share
            self.allocated_shares[owner_id] = new_share
            self.tree.item(owner_id, values=(self.tree.item(owner_id, 'text'), str(new_share)))
            
            if old_share != 0:
                share_change_factor = new_share / old_share
                self._update_child_shares(owner_id, share_change_factor)
        
        self.update_total_shares()

    def generate_report(self):
        claimants = []
        for item in self.tree.get_children():
            self._find_claimants(item, claimants)

        if not claimants:
            messagebox.showinfo("Report", "No claimants to report.")
            return

        total_share = sum(share for name, share in claimants)
        ReportWindow(self.root, claimants, total_share)

class AddHeirDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Add Heir")
        
        self.name_label = tk.Label(self.top, text="Heir's Name:")
        self.name_label.grid(row=0, column=0, padx=10, pady=5)
        self.name_entry = tk.Entry(self.top)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        self.share_label = tk.Label(self.top, text="Share (e.g., 1/2):")
        self.share_label.grid(row=1, column=0, padx=10, pady=5)
        self.share_entry = tk.Entry(self.top)
        self.share_entry.grid(row=1, column=1, padx=10, pady=5)
        
        self.ok_button = tk.Button(self.top, text="OK", command=self.ok)
        self.ok_button.grid(row=2, columnspan=2, pady=10)
        
        self.name = ""
        self.share_fraction = None

    def ok(self):
        self.name = self.name_entry.get()
        share_str = self.share_entry.get()
        if not self.name:
            messagebox.showerror("Error", "Please enter a name.", parent=self.top)
            return
        try:
            self.share_fraction = Fraction(share_str)
            self.top.destroy()
        except (ValueError, ZeroDivisionError):
            messagebox.showerror("Error", "Invalid fraction format. Please use 'numerator/denominator'.", parent=self.top)
            return

class EditDialog:
    def __init__(self, parent, original_name, original_share):
        self.top = tk.Toplevel(parent)
        self.top.title("Edit Item")
        
        self.name_label = tk.Label(self.top, text="Name:")
        self.name_label.grid(row=0, column=0, padx=10, pady=5)
        self.name_entry = tk.Entry(self.top)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)
        self.name_entry.insert(0, original_name)
        
        self.share_label = tk.Label(self.top, text="Share (e.g., 1/2):")
        self.share_label.grid(row=1, column=0, padx=10, pady=5)
        self.share_entry = tk.Entry(self.top)
        self.share_entry.grid(row=1, column=1, padx=10, pady=5)
        self.share_entry.insert(0, str(original_share))
        
        self.ok_button = tk.Button(self.top, text="OK", command=self.ok)
        self.ok_button.grid(row=2, columnspan=2, pady=10)
        
        self.name = ""
        self.share_fraction = None

    def ok(self):
        self.name = self.name_entry.get()
        share_str = self.share_entry.get()
        if not self.name:
            messagebox.showerror("Error", "Please enter a name.", parent=self.top)
            return
        try:
            self.share_fraction = Fraction(share_str)
            self.top.destroy()
        except (ValueError, ZeroDivisionError):
            messagebox.showerror("Error", "Invalid fraction format. Please use 'numerator/denominator'.", parent=self.top)
            return

class AddOriginalOwnerDialog:
    def __init__(self, parent, default_share):
        self.top = tk.Toplevel(parent)
        self.top.title("Add Original Owner")
        
        self.name_label = tk.Label(self.top, text="Name:")
        self.name_label.grid(row=0, column=0, padx=10, pady=5)
        self.name_entry = tk.Entry(self.top)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        self.share_label = tk.Label(self.top, text="Share (e.g., 1/2):")
        self.share_label.grid(row=1, column=0, padx=10, pady=5)
        self.share_entry = tk.Entry(self.top)
        self.share_entry.grid(row=1, column=1, padx=10, pady=5)
        self.share_entry.insert(0, str(default_share))
        
        self.ok_button = tk.Button(self.top, text="OK", command=self.ok)
        self.ok_button.grid(row=2, columnspan=2, pady=10)
        
        self.name = ""
        self.share_fraction = None

    def ok(self):
        self.name = self.name_entry.get()
        share_str = self.share_entry.get()
        if not self.name:
            messagebox.showerror("Error", "Please enter a name.", parent=self.top)
            return
        try:
            self.share_fraction = Fraction(share_str)
            self.top.destroy()
        except (ValueError, ZeroDivisionError):
            messagebox.showerror("Error", "Invalid fraction format. Please use 'numerator/denominator'.", parent=self.top)
            return

class SelectNodeDialog:
    def __init__(self, parent, nodes):
        self.top = tk.Toplevel(parent)
        self.top.title("Select Node")
        
        self.label = tk.Label(self.top, text="Select a destination node:")
        self.label.pack(padx=10, pady=5)

        self.listbox = tk.Listbox(self.top)
        self.listbox.pack(padx=10, pady=5)

        self.node_map = {}
        for name, item_id in nodes:
            display_text = f"{name} ({item_id})"
            self.listbox.insert(tk.END, display_text)
            self.node_map[display_text] = item_id

        self.ok_button = tk.Button(self.top, text="OK", command=self.ok)
        self.ok_button.pack(pady=10)

        self.selected_node_id = None

    def ok(self):
        selection = self.listbox.curselection()
        if selection:
            selected_text = self.listbox.get(selection[0])
            self.selected_node_id = self.node_map[selected_text]
            self.top.destroy()
        else:
            messagebox.showerror("Error", "Please select a node.", parent=self.top)

class ConveyShareDialog:
    def __init__(self, parent, nodes, remainder):
        self.top = tk.Toplevel(parent)
        self.top.title("Convey Share")

        self.nodes = nodes
        self.node_map = {f"{name} ({item_id})": item_id for name, item_id in nodes}
        self.remainder = remainder
        self.recipient_entries = []

        self.info_label = tk.Label(self.top, text=f"Remainder to convey: {self.remainder}")
        self.info_label.pack(padx=10, pady=5)

        self.recipients_frame = tk.Frame(self.top)
        self.recipients_frame.pack(padx=10, pady=5)

        self.add_recipient_button = tk.Button(self.top, text="Add Recipient", command=self.add_recipient_entry)
        self.add_recipient_button.pack(pady=5)

        self.button_frame = tk.Frame(self.top)
        self.button_frame.pack(pady=10)

        self.ok_button = tk.Button(self.button_frame, text="OK", command=self.ok)
        self.ok_button.pack(side="left", padx=5)

        self.cancel_button = tk.Button(self.button_frame, text="Cancel", command=self.top.destroy)
        self.cancel_button.pack(side="left", padx=5)

        self.conveyances = []

    def add_recipient_entry(self):
        entry_frame = tk.Frame(self.recipients_frame)
        entry_frame.pack(fill="x", pady=2)

        node_label = tk.Label(entry_frame, text="To:")
        node_label.pack(side="left", padx=5)

        node_var = tk.StringVar()
        node_combobox = ttk.Combobox(entry_frame, textvariable=node_var)
        node_combobox['values'] = list(self.node_map.keys())
        node_combobox.pack(side="left", padx=5)

        share_label = tk.Label(entry_frame, text="Share (portion of remainder):")
        share_label.pack(side="left", padx=5)

        share_entry = tk.Entry(entry_frame, width=10)
        share_entry.pack(side="left", padx=5)

        self.recipient_entries.append((node_var, share_entry))

    def ok(self):
        conveyances = []
        
        try:
            total_portion = sum(Fraction(share_entry.get()) for _, share_entry in self.recipient_entries)
            if total_portion > 1:
                messagebox.showerror("Error", "Total portion of remainder cannot exceed 1.", parent=self.top)
                return
        except (ValueError, ZeroDivisionError):
            messagebox.showerror("Error", "Invalid fraction format in one of the share entries.", parent=self.top)
            return

        for node_var, share_entry in self.recipient_entries:
            dest_name = node_var.get()
            share_str = share_entry.get()

            if not dest_name or not share_str:
                messagebox.showerror("Error", "Please fill all fields for each recipient.", parent=self.top)
                return
            
            dest_id = self.node_map.get(dest_name)
            if not dest_id:
                messagebox.showerror("Error", f"Invalid destination node: {dest_name}", parent=self.top)
                return

            try:
                portion = Fraction(share_str)
                if portion < 0:
                    messagebox.showerror("Error", "Share cannot be negative.", parent=self.top)
                    return
                
                share_to_convey = self.remainder * portion
                conveyances.append((dest_id, share_to_convey))

            except (ValueError, ZeroDivisionError):
                messagebox.showerror("Error", f"Invalid fraction format for {dest_name}.", parent=self.top)
                return

        self.conveyances = conveyances
        self.top.destroy()

class ReportWindow:
    def __init__(self, parent, data, total_share):
        self.top = tk.Toplevel(parent)
        self.top.title("Claimants Report")
        self.top.geometry("500x400")
        
        self.text = tk.Text(self.top, wrap="word")
        self.text.pack(expand=True, fill="both")
        
        report_str = "Claimants Report:\n\n"
        for name, share in data:
            percentage = float(share) * 100
            report_str += f"{name}: {share} ({percentage:.4f}%)\n" if share != 0 else ''
        
        report_str += "\n"
        total_percentage = float(total_share) * 100
        report_str += f"Total Shares: {total_share} ({total_percentage:.4f}%)\n"
            
        self.text.insert("1.0", report_str)
        self.text.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = HeirloomApp(root)
    root.mainloop()
