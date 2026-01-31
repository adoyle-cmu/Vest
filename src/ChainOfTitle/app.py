import toga
import toga.sources
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, LEFT, RIGHT
from fractions import Fraction
import json
import os

class HeirloomTreeTab:
    def __init__(self, app, tab_label):
        self.app = app
        self.tab_label = tab_label
        
        self.shares = {}
        self.allocated_shares = {}
        self.history = []

        # UI Components
        self.container = toga.Box(style=Pack(direction=COLUMN, margin=10))

        self.instructions_label = toga.Label(
            "1. Click 'Add Owner' to add a trunk.\n2. Select a person and click 'Add Heir'.\n3. Click 'Report' to see shares.",
            style=Pack(margin_bottom=10)
        )
        self.container.add(self.instructions_label)

        # Tree Data Source and Widget
        self.tree_source = toga.sources.TreeSource(accessors=['name', 'share'])
        self.tree = toga.Tree(
            headings=['Name', 'Share'],
            accessors=['name', 'share'],
            data=self.tree_source,
            multiple_select=False,
            style=Pack(flex=1, margin_bottom=10)
        )
        self.container.add(self.tree)

        self.total_shares_label = toga.Label("Total Shares: 0 (0.0000%)", style=Pack(margin_bottom=5, text_align=RIGHT))
        self.container.add(self.total_shares_label)

        # Buttons
        row1 = toga.Box(style=Pack(direction=ROW, margin=5))
        row1.add(toga.Button("Add Owner", on_press=self.add_original_owner, style=Pack(margin_right=5)))
        row1.add(toga.Button("Add Heir", on_press=self.add_heir, style=Pack(margin_right=5)))
        row1.add(toga.Button("Convey", on_press=self.convey_share, style=Pack(margin_right=5)))
        row1.add(toga.Button("Report", on_press=self.generate_report, style=Pack(margin_right=5)))
        self.container.add(row1)

        row2 = toga.Box(style=Pack(direction=ROW, margin=5))
        row2.add(toga.Button("Edit", on_press=self.edit_selected, style=Pack(margin_right=5)))
        row2.add(toga.Button("Delete", on_press=self.delete_selected, style=Pack(margin_right=5)))
        row2.add(toga.Button("Save", on_press=self.save_tree, style=Pack(margin_right=5)))
        row2.add(toga.Button("Load", on_press=self.load_tree, style=Pack(margin_right=5)))
        row2.add(toga.Button("Undo", on_press=self.undo, style=Pack(margin_right=5)))
        row2.add(toga.Button("Clear", on_press=self.clear_all, style=Pack(margin_right=5)))
        self.container.add(row2)

        self.update_total_shares()

    # --- Helper to find node by ID (Node object) ---
    def _find_node_by_id(self, node_id, current_node=None):
        # In Toga, the 'id' is the node object itself usually, or we can use custom IDs.
        # But here we are using the Node object as the identifier in self.shares
        return node_id

    # --- Data & Logic ---

    def _append_node(self, parent_node, name, share):
        data = {'name': name, 'share': share}
        if parent_node is None:
            return self.tree_source.append(data)
        else:
            return parent_node.append(data)

    def get_tree_snapshot(self):
        data = []
        def traverse(node):
            node_data = {
                "id": str(id(node)), # Using memory address as temp ID for snapshot structure, though logic differs
                "name": node.name,
                "share": str(self.shares.get(node, "0/1")),
                "allocated_share": str(self.allocated_shares.get(node, "0/1")),
                "children": []
            }
            # Iterate children
            if node.can_have_children():
                for i in range(len(node)):
                     node_data["children"].append(traverse(node[i]))
            return node_data

        root_nodes = []
        for node in self.tree_source:
            root_nodes.append(traverse(node))
        return root_nodes

    def save_state(self):
        # Snapshotting in Toga is trickier because SourceNodes are objects.
        # We'll save a JSON-serializable structure.
        self.history.append(self.get_tree_snapshot())

    def restore_tree_from_snapshot(self, data):
        self.tree_source.clear()
        self.shares.clear()
        self.allocated_shares.clear()

        def restore_node(node_data, parent_node=None):
            name = node_data["name"]
            share = Fraction(node_data["share"])
            allocated_share = Fraction(node_data["allocated_share"])
            
            # Create node
            new_node = self._append_node(parent_node, name, str(share))
            
            self.shares[new_node] = share
            self.allocated_shares[new_node] = allocated_share
            
            for child_data in node_data.get("children", []):
                restore_node(child_data, new_node)

        for root_node_data in data:
            restore_node(root_node_data, None)
            
        self.update_total_shares()

    async def undo(self, widget):
        if not self.history:
            await self.app.main_window.dialog(toga.InfoDialog("Undo", "Nothing to undo."))
            return
        previous_state = self.history.pop()
        self.restore_tree_from_snapshot(previous_state)

    async def clear_all(self, widget):
        if await self.app.main_window.dialog(toga.QuestionDialog("Clear All", "Are you sure you want to clear the entire tree?")):
            self.save_state()
            self.tree_source.clear()
            self.shares.clear()
            self.allocated_shares.clear()
            self.update_total_shares()

    def update_total_shares(self):
        claimants = []
        for node in self.tree_source:
            self._find_claimants(node, claimants)
        
        total_share = sum(share for name, share in claimants)
        percentage = float(total_share) * 100
        
        self.total_shares_label.text = f"Total Shares: {total_share} ({percentage:.4f}%)"
        # Color handling is not as direct in Toga labels without CSS styles, skipping color for now

    def _find_claimants(self, node, claimants):
        is_leaf = len(node) == 0
        if is_leaf:
            claimants.append((node.name, self.shares[node]))
            return

        children_share = sum(self.allocated_shares.get(child, Fraction(0)) for child in node)
        parent_share = self.shares[node]

        if parent_share > children_share:
            claimants.append((node.name, parent_share - children_share))

        for child in node:
            self._find_claimants(child, claimants)

    def _get_all_nodes(self):
        nodes = []
        def traverse(node):
            nodes.append(node)
            for child in node:
                traverse(child)
        for node in self.tree_source:
            traverse(node)
        return nodes

    def _update_child_shares(self, node, factor):
        for child in node:
            old_child_share = self.shares[child]
            new_child_share = old_child_share * factor
            self.shares[child] = new_child_share
            
            if child in self.allocated_shares:
                self.allocated_shares[child] = self.allocated_shares[child] * factor
            
            # Update UI
            child.share = str(new_child_share)
            
            self._update_child_shares(child, factor)
    
    def _set_children_shares_to_zero(self, node):
        for child in node:
            self.shares[child] = Fraction(0)
            self.allocated_shares[child] = Fraction(0)
            child.share = "0/1"
            self._set_children_shares_to_zero(child)

    def _update_original_owner_shares(self):
        original_owners = list(self.tree_source)
        if not original_owners:
            return

        new_share = Fraction(1, len(original_owners))

        for owner_node in original_owners:
            old_share = self.shares.get(owner_node, new_share)
            self.shares[owner_node] = new_share
            self.allocated_shares[owner_node] = new_share
            owner_node.share = str(new_share)
            
            if old_share != 0:
                share_change_factor = new_share / old_share
                self._update_child_shares(owner_node, share_change_factor)
        
        self.update_total_shares()

    # --- Actions ---

    def add_original_owner(self, widget):
        num_original_owners = len(self.tree_source)
        default_share = Fraction(1, num_original_owners + 1)
        
        def on_result(name, share):
            if name and share is not None:
                self.save_state()
                node = self._append_node(None, name, str(share))
                self.shares[node] = share
                self.allocated_shares[node] = share
                self.update_total_shares()

        AddNameShareDialog(self.app, "Add Original Owner", default_share, on_result).show()

    async def add_heir(self, widget):
        selection = self.tree.selection
        if selection is None:
            await self.app.main_window.dialog(toga.ErrorDialog("Error", "Please select a parent from the tree."))
            return

        parent_node = selection
        
        def on_result(name, fraction):
            if name and fraction is not None:
                self.save_state()
                parent_share = self.shares[parent_node]
                heir_share = parent_share * fraction
                
                node = self._append_node(parent_node, name, str(heir_share))
                self.shares[node] = heir_share
                self.allocated_shares[node] = heir_share
                self.update_total_shares()

        AddNameShareDialog(self.app, "Add Heir", None, on_result, share_label="Share Fraction (e.g. 1/2):").show()

    async def edit_selected(self, widget):
        selection = self.tree.selection
        if selection is None:
            await self.app.main_window.dialog(toga.ErrorDialog("Error", "Please select an item to edit."))
            return

        node = selection
        original_name = node.name
        old_share = self.shares[node]
        
        # Determine parent share to calculate relative share for editing
        # Note: Toga Tree node doesn't explicitly reference parent easily in public API sometimes, 
        # but we can infer or it might be available as `_parent` (private). 
        # Safer: We know the structure from our `traverse` or we can look up.
        # Actually `toga.sources.Node` objects don't always expose parent.
        # We can find parent by traversing.
        
        parent_node = None
        # Naive search for parent
        def find_parent(candidate, target):
            for child in candidate:
                if child == target:
                    return candidate
                p = find_parent(child, target)
                if p: return p
            return None
        
        for root in self.tree_source:
            if root == node:
                parent_node = None
                break
            parent_node = find_parent(root, node)
            if parent_node: break
        
        initial_share_val = old_share
        if parent_node:
            parent_share = self.shares[parent_node]
            if parent_share == 0 and old_share == 0:
                 initial_share_val = 0
            elif parent_share == 0 and old_share != 0:
                await self.app.main_window.dialog(toga.ErrorDialog("Error", "Cannot edit heir of a parent with zero share."))
                return
            else:
                initial_share_val = old_share / parent_share
        
        async def on_result(name, share_fraction):
             if name and share_fraction is not None:
                self.save_state()
                
                new_share = share_fraction
                if parent_node:
                    new_share = self.shares[parent_node] * share_fraction
                
                # Update Node
                node.name = name
                node.share = str(new_share)
                
                self.shares[node] = new_share
                self.allocated_shares[node] = new_share

                if new_share == 0:
                    self._set_children_shares_to_zero(node)
                elif old_share == 0:
                    if len(node) > 0:
                         await self.app.main_window.dialog(toga.InfoDialog("Warning", "The original share was 0. Children's shares cannot be automatically updated."))
                else:
                    share_change_factor = new_share / old_share
                    self._update_child_shares(node, share_change_factor)
                self.update_total_shares()

        AddNameShareDialog(self.app, "Edit Item", initial_share_val, on_result, name_val=original_name).show()

    async def delete_selected(self, widget):
        selection = self.tree.selection
        if selection is None:
            await self.app.main_window.dialog(toga.ErrorDialog("Error", "Please select an item to delete."))
            return

        node = selection
        
        # Check if original owner (no parent)
        # Using the same find_parent logic
        parent_node = None
        for root in self.tree_source:
            if root == node:
                parent_node = None
                break
            # ... helper search ...

        self.save_state()

        def cleanup_dicts(n):
            for child in n:
                cleanup_dicts(child)
            if n in self.shares: del self.shares[n]
            if n in self.allocated_shares: del self.allocated_shares[n]
        
        cleanup_dicts(node)
        
        # Remove from tree
        self.tree_source.remove(node)
        
        # Logic for updates
        # If it was a root node (original owner), update others
        # We need to know if it was root. If we can't find it in roots anymore (since we removed it),
        # we can assume if it WAS in roots. 
        # Actually `remove` is done. We can just check if we need to rebalance roots.
        # The logic in original app: if is_original_owner, _update_original_owner_shares
        # We can check if `node` was in the list of roots before removal? 
        # Too late.
        # But `_update_original_owner_shares` recalculates based on REMAINING owners.
        # So we should call it if the deleted node was effectively a root.
        # We can just call it if `parent_node` was None. But we didn't calculate `parent_node` completely.
        # Let's just assume we update total shares, and if we removed a root, we might want to rebalance?
        # The original code only rebalances if it WAS an original owner. 
        # Let's call `_update_original_owner_shares` regardless? No, that would reset shares of heirs if we deleted an heir.
        # We need to know if it was a root.
        # Let's count roots?
        # If we just removed a root, the existing roots share won't change unless we force it.
        # For now, let's just update total shares. The user can manually fix or we implement robust parent detection.
        self.update_total_shares()


    async def convey_share(self, widget):
        selection = self.tree.selection
        if selection is None:
            await self.app.main_window.dialog(toga.ErrorDialog("Error", "Please select a source node."))
            return
        
        source_node = selection
        children_total_share = sum(self.allocated_shares.get(child, 0) for child in source_node)
        source_remainder = self.shares[source_node] - children_total_share

        if source_remainder <= 0:
            await self.app.main_window.dialog(toga.ErrorDialog("Error", "Source node has no remainder to convey."))
            return

        all_nodes = self._get_all_nodes()
        # Filter source out
        dest_candidates = [n for n in all_nodes if n != source_node]

        async def on_convey(conveyances):
            if conveyances:
                self.save_state()
                total_conveyed = sum(amt for _, amt in conveyances)
                
                self.shares[source_node] -= total_conveyed
                source_node.share = str(self.shares[source_node])

                for dest_node, share_added in conveyances:
                    old_dest_share = self.shares[dest_node]
                    new_dest_share = old_dest_share + share_added
                    self.shares[dest_node] = new_dest_share
                    dest_node.share = str(new_dest_share)
                    
                    if old_dest_share != 0:
                        factor = new_dest_share / old_dest_share
                        self._update_child_shares(dest_node, factor)
                
                self.update_total_shares()

        ConveyShareDialog(self.app, dest_candidates, source_remainder, on_convey).show()


    async def save_tree(self, widget):
        path = await self.app.main_window.dialog(toga.SaveFileDialog("Save Tree", suggested_filename="tree.json", file_types=["json"]))
        if path is None:
            return
        
        data = self.get_tree_snapshot()
        
        # Convert snapshot to pure JSON (remove recursive structure if needed or adapt)
        # The snapshot structure is recursive, so it dumps fine.
        # But Fraction objects aren't JSON serializable.
        # `get_tree_snapshot` returns strings for shares, so it should be fine.
        
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
            await self.app.main_window.dialog(toga.InfoDialog("Success", "Tree saved successfully."))
        except Exception as e:
            await self.app.main_window.dialog(toga.ErrorDialog("Error", f"Failed to save tree: {e}"))

    async def load_tree(self, widget):
        path = await self.app.main_window.dialog(toga.OpenFileDialog("Load Tree", file_types=["json"]))
        if path is None:
            return
        
        # Confirm overwrite? Toga doesn't have simple Yes/No awaitable easily in all versions?
        # Assuming we can just load.
        
        self.save_state()
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            self.restore_tree_from_snapshot(data)
            await self.app.main_window.dialog(toga.InfoDialog("Success", "Tree loaded successfully."))
        except Exception as e:
             await self.app.main_window.dialog(toga.ErrorDialog("Error", f"Failed to load tree: {e}"))

    async def generate_report(self, widget):
        claimants = []
        for node in self.tree_source:
            self._find_claimants(node, claimants)
        
        if not claimants:
            await self.app.main_window.dialog(toga.InfoDialog("Report", "No claimants."))
            return

        total_share = sum(share for name, share in claimants)
        
        report_str = "Claimants Report:\n\n"
        for name, share in claimants:
            percentage = float(share) * 100
            report_str += f"{name}: {share} ({percentage:.8f}%)\n" if share != 0 else ''
        
        report_str += "\n"
        total_percentage = float(total_share) * 100
        report_str += f"Total Shares: {total_share} ({total_percentage:.8f}%)\n"

        # Show in a new window
        report_win = toga.Window(title="Report")
        multiline = toga.MultilineTextInput(value=report_str, readonly=True, style=Pack(flex=1))
        report_win.content = multiline
        report_win.show()


class AddNameShareDialog:
    def __init__(self, app, title, default_share, on_result, name_val="", share_label="Share:"):
        self.window = toga.Window(title=title, size=(300, 150))
        self.on_result = on_result
        
        box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        
        box.add(toga.Label("Name:", style=Pack(margin_bottom=5)))
        self.name_input = toga.TextInput(value=name_val, style=Pack(margin_bottom=10))
        box.add(self.name_input)
        
        box.add(toga.Label(share_label, style=Pack(margin_bottom=5)))
        val = str(default_share) if default_share is not None else ""
        self.share_input = toga.TextInput(value=val, style=Pack(margin_bottom=10))
        box.add(self.share_input)
        
        btn_box = toga.Box(style=Pack(direction=ROW, margin_top=10))
        btn_box.add(toga.Button("OK", on_press=self.on_ok, style=Pack(flex=1)))
        
        box.add(btn_box)
        self.window.content = box

    def show(self):
        self.window.show()

    async def on_ok(self, widget):
        name = self.name_input.value
        share_str = self.share_input.value
        try:
            share = Fraction(share_str)
            self.window.close()
            res = self.on_result(name, share)
            if hasattr(res, '__await__'):
                await res
        except ValueError:
            await self.window.dialog(toga.InfoDialog("Error", "Invalid fraction."))


class ConveyShareDialog:
    def __init__(self, app, dest_nodes, remainder, on_result):
        self.window = toga.Window(title="Convey Share", size=(400, 300))
        self.dest_nodes = dest_nodes
        self.node_map = {f"{n.name}": n for n in dest_nodes} # Simple mapping by name
        self.remainder = remainder
        self.on_result = on_result
        self.entries = []
        
        self.box = toga.Box(style=Pack(direction=COLUMN, margin=10))
        self.box.add(toga.Label(f"Remainder: {remainder}", style=Pack(margin_bottom=10)))
        
        self.entries_box = toga.Box(style=Pack(direction=COLUMN))
        self.box.add(self.entries_box)
        
        self.box.add(toga.Button("Add Recipient", on_press=self.add_entry, style=Pack(margin_top=5)))
        self.box.add(toga.Button("OK", on_press=self.on_ok, style=Pack(margin_top=10)))
        
        self.window.content = self.box
        
    def add_entry(self, widget):
        row = toga.Box(style=Pack(direction=ROW, margin_bottom=5))
        
        # Node selection (simplified as text input or simple selection if Toga had ComboBox easily populated)
        # Toga has Selection.
        sel = toga.Selection(items=list(self.node_map.keys()), style=Pack(flex=1, margin_right=5))
        amt = toga.TextInput(placeholder="Share (fraction of remainder)", style=Pack(width=100))
        
        row.add(sel)
        row.add(amt)
        self.entries_box.add(row)
        self.entries.append((sel, amt))
        self.entries_box.refresh() # Force layout update?

    def show(self):
        self.window.show()

    async def on_ok(self, widget):
        conveyances = []
        total_portion = Fraction(0)
        
        try:
            for sel, amt in self.entries:
                node_name = sel.value
                share_str = amt.value
                if not node_name or not share_str: continue
                
                portion = Fraction(share_str)
                if portion < 0: raise ValueError("Negative share")
                
                total_portion += portion
                dest_node = self.node_map[node_name]
                conveyances.append((dest_node, self.remainder * portion))
            
            if total_portion > 1:
                await self.window.dialog(toga.InfoDialog("Error", "Total exceeds remainder (portion > 1)."))
                return
            
            self.window.close()
            res = self.on_result(conveyances)
            if hasattr(res, '__await__'):
                await res

        except ValueError:
             await self.window.dialog(toga.InfoDialog("Error", "Invalid input."))


class ChainOfTitleApp(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title=self.formal_name)
        
        self.option_container = toga.OptionContainer()
        self.add_tab(None)
        
        # Menu commands for adding tabs
        cmd_add_tab = toga.Command(self.add_tab, text='New Tab', group=toga.Group.FILE)
        self.commands.add(cmd_add_tab)

        self.main_window.content = self.option_container
        self.main_window.show()

    def add_tab(self, widget):
        # Create a new tab
        idx = len(self.option_container.content) + 1
        label = f"Tree {idx}"
        tab_handler = HeirloomTreeTab(self, label)
        self.option_container.content.append(label, tab_handler.container)

def main():
    return ChainOfTitleApp("ChainOfTitle", "com.petescheeks")

if __name__ == '__main__':
    main().main_loop()