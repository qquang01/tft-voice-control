"""Slot configuration panel component for UI configuration"""

import customtkinter as ctk


class SlotConfigPanel:
    """Handles slot configuration UI"""

    def __init__(self, parent_tab, on_apply_slots, on_reset_slots, 
                 on_apply_shop_state, on_reset_shop_state, on_toggle):
        self.parent_tab = parent_tab
        self.on_apply_slots = on_apply_slots
        self.on_reset_slots = on_reset_slots
        self.on_apply_shop_state = on_apply_shop_state
        self.on_reset_shop_state = on_reset_shop_state
        self.on_toggle = on_toggle

        # Slot configuration inputs
        self.slot_config_inputs = {}
        self.shop_state_config_inputs = {}

        # Default values
        self.slot_width = 64
        self.slot_height = 64
        self.slot_spacing = 104
        self.slot_start_x = 170
        self.slot_start_y = 50
        self.slot_count = 5
        self.shop_state_x = 880
        self.shop_state_y = 500
        self.shop_state_width = 40
        self.shop_state_height = 20

    def create_panel(self):
        """Create slot configuration panel"""
        # Slot configuration panel (hidden by default)
        self.slot_config_panel = ctk.CTkFrame(self.parent_tab)
        self.slot_config_panel.pack(fill="x", padx=5, pady=5)
        self.slot_config_panel.pack_forget()  # Hide initially

        # Create slot configuration inputs
        self._create_slot_config_inputs()

        return self.slot_config_panel

    def _create_slot_config_inputs(self):
        """Create input controls for slot configuration"""
        # Row 1: Width, Height
        row1 = ctk.CTkFrame(self.slot_config_panel)
        row1.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(row1, text="Width:", width=60).pack(side="left", padx=2)
        self.slot_config_inputs['width'] = ctk.CTkEntry(row1, width=80)
        self.slot_config_inputs['width'].insert(0, str(self.slot_width))
        self.slot_config_inputs['width'].pack(side="left", padx=2)
        
        ctk.CTkLabel(row1, text="Height:", width=60).pack(side="left", padx=2)
        self.slot_config_inputs['height'] = ctk.CTkEntry(row1, width=80)
        self.slot_config_inputs['height'].insert(0, str(self.slot_height))
        self.slot_config_inputs['height'].pack(side="left", padx=2)
        
        ctk.CTkLabel(row1, text="Spacing:", width=60).pack(side="left", padx=2)
        self.slot_config_inputs['spacing'] = ctk.CTkEntry(row1, width=80)
        self.slot_config_inputs['spacing'].insert(0, str(self.slot_spacing))
        self.slot_config_inputs['spacing'].pack(side="left", padx=2)
        
        # Row 2: Start X, Start Y, Count
        row2 = ctk.CTkFrame(self.slot_config_panel)
        row2.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(row2, text="Start X:", width=60).pack(side="left", padx=2)
        self.slot_config_inputs['start_x'] = ctk.CTkEntry(row2, width=80)
        self.slot_config_inputs['start_x'].insert(0, str(self.slot_start_x))
        self.slot_config_inputs['start_x'].pack(side="left", padx=2)
        
        ctk.CTkLabel(row2, text="Start Y:", width=60).pack(side="left", padx=2)
        self.slot_config_inputs['start_y'] = ctk.CTkEntry(row2, width=80)
        self.slot_config_inputs['start_y'].insert(0, str(self.slot_start_y))
        self.slot_config_inputs['start_y'].pack(side="left", padx=2)
        
        ctk.CTkLabel(row2, text="Count:", width=60).pack(side="left", padx=2)
        self.slot_config_inputs['count'] = ctk.CTkEntry(row2, width=80)
        self.slot_config_inputs['count'].insert(0, str(self.slot_count))
        self.slot_config_inputs['count'].pack(side="left", padx=2)
        
        # Row 3: Buttons
        row3 = ctk.CTkFrame(self.slot_config_panel)
        row3.pack(fill="x", padx=5, pady=5)
        
        apply_btn = ctk.CTkButton(
            row3,
            text="Apply Slots",
            command=self._apply_slot_config,
            width=100
        )
        apply_btn.pack(side="left", padx=5)
        
        reset_btn = ctk.CTkButton(
            row3,
            text="Reset Slots",
            command=self._reset_slot_config,
            width=100
        )
        reset_btn.pack(side="left", padx=5)
        
        close_btn = ctk.CTkButton(
            row3,
            text="Close",
            command=self.on_toggle,
            width=100
        )
        close_btn.pack(side="left", padx=5)
        
        # Row 4: Shop State Box (6th box) - separate configuration
        row4 = ctk.CTkFrame(self.slot_config_panel)
        row4.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(row4, text="Shop State Box (6th box):", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        ctk.CTkLabel(row4, text="X:", width=30).pack(side="left", padx=2)
        self.shop_state_config_inputs['x'] = ctk.CTkEntry(row4, width=60)
        self.shop_state_config_inputs['x'].insert(0, str(self.shop_state_x))
        self.shop_state_config_inputs['x'].pack(side="left", padx=2)
        
        ctk.CTkLabel(row4, text="Y:", width=30).pack(side="left", padx=2)
        self.shop_state_config_inputs['y'] = ctk.CTkEntry(row4, width=60)
        self.shop_state_config_inputs['y'].insert(0, str(self.shop_state_y))
        self.shop_state_config_inputs['y'].pack(side="left", padx=2)
        
        ctk.CTkLabel(row4, text="Width:", width=45).pack(side="left", padx=2)
        self.shop_state_config_inputs['width'] = ctk.CTkEntry(row4, width=60)
        self.shop_state_config_inputs['width'].insert(0, str(self.shop_state_width))
        self.shop_state_config_inputs['width'].pack(side="left", padx=2)
        
        ctk.CTkLabel(row4, text="Height:", width=50).pack(side="left", padx=2)
        self.shop_state_config_inputs['height'] = ctk.CTkEntry(row4, width=60)
        self.shop_state_config_inputs['height'].insert(0, str(self.shop_state_height))
        self.shop_state_config_inputs['height'].pack(side="left", padx=2)
        
        # Row 5: Shop State Buttons
        row5 = ctk.CTkFrame(self.slot_config_panel)
        row5.pack(fill="x", padx=5, pady=5)
        
        apply_shop_state_btn = ctk.CTkButton(
            row5,
            text="Apply Shop State",
            command=self._apply_shop_state_config,
            width=120
        )
        apply_shop_state_btn.pack(side="left", padx=5)
        
        reset_shop_state_btn = ctk.CTkButton(
            row5,
            text="Reset Shop State",
            command=self._reset_shop_state_config,
            width=120
        )
        reset_shop_state_btn.pack(side="left", padx=5)

    def _apply_slot_config(self):
        """Apply slot configuration from inputs"""
        try:
            width = int(self.slot_config_inputs['width'].get())
            height = int(self.slot_config_inputs['height'].get())
            spacing = int(self.slot_config_inputs['spacing'].get())
            start_x = int(self.slot_config_inputs['start_x'].get())
            start_y = int(self.slot_config_inputs['start_y'].get())
            count = int(self.slot_config_inputs['count'].get())
            
            if self.on_apply_slots:
                self.on_apply_slots(width, height, spacing, start_x, start_y, count)
            
        except ValueError:
            pass  # Error handling should be done by caller

    def _reset_slot_config(self):
        """Reset slot configuration to defaults"""
        self.slot_width = 64
        self.slot_height = 64
        self.slot_spacing = 104
        self.slot_start_x = 170
        self.slot_start_y = 50
        self.slot_count = 5
        
        # Update inputs
        self.slot_config_inputs['width'].delete(0, "end")
        self.slot_config_inputs['width'].insert(0, str(self.slot_width))
        self.slot_config_inputs['height'].delete(0, "end")
        self.slot_config_inputs['height'].insert(0, str(self.slot_height))
        self.slot_config_inputs['spacing'].delete(0, "end")
        self.slot_config_inputs['spacing'].insert(0, str(self.slot_spacing))
        self.slot_config_inputs['start_x'].delete(0, "end")
        self.slot_config_inputs['start_x'].insert(0, str(self.slot_start_x))
        self.slot_config_inputs['start_y'].delete(0, "end")
        self.slot_config_inputs['start_y'].insert(0, str(self.slot_start_y))
        self.slot_config_inputs['count'].delete(0, "end")
        self.slot_config_inputs['count'].insert(0, str(self.slot_count))
        
        if self.on_reset_slots:
            self.on_reset_slots()

    def _apply_shop_state_config(self):
        """Apply shop state box configuration from inputs"""
        try:
            x = int(self.shop_state_config_inputs['x'].get())
            y = int(self.shop_state_config_inputs['y'].get())
            width = int(self.shop_state_config_inputs['width'].get())
            height = int(self.shop_state_config_inputs['height'].get())
            
            if self.on_apply_shop_state:
                self.on_apply_shop_state(x, y, width, height)
            
        except ValueError:
            pass  # Error handling should be done by caller

    def _reset_shop_state_config(self):
        """Reset shop state box configuration to defaults"""
        self.shop_state_x = 880
        self.shop_state_y = 500
        self.shop_state_width = 40
        self.shop_state_height = 20
        
        # Update inputs
        self.shop_state_config_inputs['x'].delete(0, "end")
        self.shop_state_config_inputs['x'].insert(0, str(self.shop_state_x))
        self.shop_state_config_inputs['y'].delete(0, "end")
        self.shop_state_config_inputs['y'].insert(0, str(self.shop_state_y))
        self.shop_state_config_inputs['width'].delete(0, "end")
        self.shop_state_config_inputs['width'].insert(0, str(self.shop_state_width))
        self.shop_state_config_inputs['height'].delete(0, "end")
        self.shop_state_config_inputs['height'].insert(0, str(self.shop_state_height))
        
        if self.on_reset_shop_state:
            self.on_reset_shop_state()

    def toggle_visibility(self):
        """Toggle panel visibility"""
        if self.slot_config_panel.winfo_ismapped():
            self.slot_config_panel.pack_forget()
        else:
            self.slot_config_panel.pack(fill="x", padx=5, pady=5)

    def update_values(self, slot_width, slot_height, slot_spacing, slot_start_x, slot_start_y, slot_count,
                      shop_state_x, shop_state_y, shop_state_width, shop_state_height):
        """Update input values"""
        self.slot_width = slot_width
        self.slot_height = slot_height
        self.slot_spacing = slot_spacing
        self.slot_start_x = slot_start_x
        self.slot_start_y = slot_start_y
        self.slot_count = slot_count
        self.shop_state_x = shop_state_x
        self.shop_state_y = shop_state_y
        self.shop_state_width = shop_state_width
        self.shop_state_height = shop_state_height

        # Update slot inputs
        self.slot_config_inputs['width'].delete(0, "end")
        self.slot_config_inputs['width'].insert(0, str(self.slot_width))
        self.slot_config_inputs['height'].delete(0, "end")
        self.slot_config_inputs['height'].insert(0, str(self.slot_height))
        self.slot_config_inputs['spacing'].delete(0, "end")
        self.slot_config_inputs['spacing'].insert(0, str(self.slot_spacing))
        self.slot_config_inputs['start_x'].delete(0, "end")
        self.slot_config_inputs['start_x'].insert(0, str(self.slot_start_x))
        self.slot_config_inputs['start_y'].delete(0, "end")
        self.slot_config_inputs['start_y'].insert(0, str(self.slot_start_y))
        self.slot_config_inputs['count'].delete(0, "end")
        self.slot_config_inputs['count'].insert(0, str(self.slot_count))

        # Update shop state inputs
        self.shop_state_config_inputs['x'].delete(0, "end")
        self.shop_state_config_inputs['x'].insert(0, str(self.shop_state_x))
        self.shop_state_config_inputs['y'].delete(0, "end")
        self.shop_state_config_inputs['y'].insert(0, str(self.shop_state_y))
        self.shop_state_config_inputs['width'].delete(0, "end")
        self.shop_state_config_inputs['width'].insert(0, str(self.shop_state_width))
        self.shop_state_config_inputs['height'].delete(0, "end")
        self.shop_state_config_inputs['height'].insert(0, str(self.shop_state_height))
