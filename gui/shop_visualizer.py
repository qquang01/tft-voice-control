import os
import customtkinter as ctk
from typing import Optional

from core.adb_controller import ADBController
from core.screen_capture import ScreenCapture
from gui.utils.debug_logger import DebugLogger
from gui.components.shop_preview import ShopPreview
from gui.components.template_labeling import TemplateLabeling
from gui.components.screenshot_capture import ScreenshotCapture
from gui.components.batch_labeling import BatchLabeling
from gui.components.slot_config_panel import SlotConfigPanel


# Constants
class Config:
    # Slot configuration defaults
    DEFAULT_SLOT_WIDTH = 64
    DEFAULT_SLOT_HEIGHT = 64
    DEFAULT_SLOT_SPACING = 104
    DEFAULT_SLOT_START_X = 170
    DEFAULT_SLOT_START_Y = 50
    DEFAULT_SLOT_COUNT = 5
    
    # Shop state box defaults
    DEFAULT_SHOP_STATE_X = 880
    DEFAULT_SHOP_STATE_Y = 500
    DEFAULT_SHOP_STATE_WIDTH = 40
    DEFAULT_SHOP_STATE_HEIGHT = 20
    
    # Canvas dimensions
    SHOP_CANVAS_WIDTH = 960
    SHOP_CANVAS_HEIGHT = 540
    TEMPLATE_CANVAS_WIDTH = 800
    TEMPLATE_CANVAS_HEIGHT = 400
    SCREENSHOT_CANVAS_WIDTH = 960
    SCREENSHOT_CANVAS_HEIGHT = 540
    
    # UI colors
    CANVAS_BG_COLOR = "#1a1a1a"
    
    # Template grid layout
    TEMPLATE_GRID_COLS = 4
    TEMPLATE_GRID_PADDING = 10
    TEMPLATE_THUMB_SIZE = 100
    
    # Preview settings
    PREVIEW_FPS = 10
    PREVIEW_SLEEP_TIME = 0.1
    
    # Auto-labeling
    MATCH_THRESHOLD = 0.5
    
    # Retry delays (ms)
    CANVAS_RETRY_DELAY = 200
    GUI_RENDER_DELAY = 100
    BACKGROUND_DISPLAY_DELAY = 1000


class ShopVisualizer:
    """Main coordinator for shop visualization components"""

    def __init__(self, logger: DebugLogger, tabview, root):
        self.logger = logger
        self.tabview = tabview
        self.root = root

        # Initialize ADB and capture
        self.adb = ADBController()
        self.capture = None

        # Initialize components
        self.shop_preview = ShopPreview(logger, tabview, root)
        self.template_labeling = TemplateLabeling(logger, tabview, root)
        self.screenshot_capture = ScreenshotCapture(logger, tabview, root, None)
        self.batch_labeling = BatchLabeling(logger, tabview, root)

        # Slot configuration panel (will be created in create_tab)
        self.slot_config_panel = None

        # Sync slot configuration between components
        self._sync_slot_config()

    def _sync_slot_config(self):
        """Sync slot configuration between components"""
        # Get config from shop_preview (source of truth)
        self.shop_preview.update_slot_config(
            Config.DEFAULT_SLOT_WIDTH,
            Config.DEFAULT_SLOT_HEIGHT,
            Config.DEFAULT_SLOT_SPACING,
            Config.DEFAULT_SLOT_START_X,
            Config.DEFAULT_SLOT_START_Y,
            Config.DEFAULT_SLOT_COUNT
        )
        self.shop_preview.update_shop_state_config(
            Config.DEFAULT_SHOP_STATE_X,
            Config.DEFAULT_SHOP_STATE_Y,
            Config.DEFAULT_SHOP_STATE_WIDTH,
            Config.DEFAULT_SHOP_STATE_HEIGHT
        )
        
        # Sync to batch_labeling
        self.batch_labeling.set_slot_config(
            Config.DEFAULT_SLOT_WIDTH,
            Config.DEFAULT_SLOT_HEIGHT,
            Config.DEFAULT_SLOT_SPACING,
            Config.DEFAULT_SLOT_START_X,
            Config.DEFAULT_SLOT_START_Y,
            Config.DEFAULT_SLOT_COUNT
        )
        self.batch_labeling.set_shop_state_config(
            Config.DEFAULT_SHOP_STATE_X,
            Config.DEFAULT_SHOP_STATE_Y,
            Config.DEFAULT_SHOP_STATE_WIDTH,
            Config.DEFAULT_SHOP_STATE_HEIGHT
        )

    def create_tab(self):
        """Create all tabs and coordinate components"""
        # Create shop preview tab
        self.shop_preview.create_tab()
        
        # Add slot configuration button to shop preview controls
        shop_tab = self.tabview.tab("Shop Visualizer")
        shop_controls = shop_tab.winfo_children()[1]  # Get controls frame
        
        # Slot configuration button
        config_btn = ctk.CTkButton(
            shop_controls,
            text="Config Slots",
            command=self.toggle_slot_config_panel,
            width=120
        )
        config_btn.pack(side="left", padx=(0, 10))

        # Create slot configuration panel
        self.slot_config_panel = SlotConfigPanel(
            shop_tab,
            self._apply_slot_config,
            self._reset_slot_config,
            self._apply_shop_state_config,
            self._reset_shop_state_config,
            self.toggle_slot_config_panel
        )
        self.slot_config_panel.create_panel()

        # Create template labeling tab
        self.template_labeling.create_tab()
        
        # Add batch labeling button to template labeling
        template_tab = self.tabview.tab("Template Labeling")
        label_frame = template_tab.winfo_children()[1]  # Get label frame
        
        # Batch labeling button
        batch_btn = ctk.CTkButton(
            label_frame,
            text="Batch Label",
            command=self.start_batch_labeling,
            width=100
        )
        batch_btn.pack(side="left", padx=(0, 10))

        # Create screenshot capture tab
        self.screenshot_capture.create_tab()
        
        # Set capture instance after initialization
        if self.adb.connect():
            self.capture = ScreenCapture(self.adb)
            self.screenshot_capture.set_capture(self.capture)

    def toggle_slot_config_panel(self):
        """Toggle slot configuration panel visibility"""
        if self.slot_config_panel:
            self.slot_config_panel.toggle_visibility()

    def _apply_slot_config(self, width, height, spacing, start_x, start_y, count):
        """Apply slot configuration to all components"""
        self.logger.log("INFO", f"Slot config updated: {width}x{height}, start=({start_x}, {start_y}), spacing={spacing}, count={count}")
        
        # Update shop preview
        self.shop_preview.update_slot_config(width, height, spacing, start_x, start_y, count)
        
        # Update batch labeling
        self.batch_labeling.set_slot_config(width, height, spacing, start_x, start_y, count)
        
        # Refresh shop preview if background exists
        self.shop_preview.display_shop_background()

    def _reset_slot_config(self):
        """Reset slot configuration to defaults"""
        self.logger.log("INFO", "Slot configuration reset to defaults")
        
        # Reset to defaults
        self._apply_slot_config(
            Config.DEFAULT_SLOT_WIDTH,
            Config.DEFAULT_SLOT_HEIGHT,
            Config.DEFAULT_SLOT_SPACING,
            Config.DEFAULT_SLOT_START_X,
            Config.DEFAULT_SLOT_START_Y,
            Config.DEFAULT_SLOT_COUNT
        )
        
        # Update panel inputs
        if self.slot_config_panel:
            self.slot_config_panel.update_values(
                Config.DEFAULT_SLOT_WIDTH,
                Config.DEFAULT_SLOT_HEIGHT,
                Config.DEFAULT_SLOT_SPACING,
                Config.DEFAULT_SLOT_START_X,
                Config.DEFAULT_SLOT_START_Y,
                Config.DEFAULT_SLOT_COUNT,
                Config.DEFAULT_SHOP_STATE_X,
                Config.DEFAULT_SHOP_STATE_Y,
                Config.DEFAULT_SHOP_STATE_WIDTH,
                Config.DEFAULT_SHOP_STATE_HEIGHT
            )

    def _apply_shop_state_config(self, x, y, width, height):
        """Apply shop state box configuration to all components"""
        self.logger.log("INFO", f"Shop state box config updated: ({x}, {y}), size={width}x{height}")
        
        # Update shop preview
        self.shop_preview.update_shop_state_config(x, y, width, height)
        
        # Update batch labeling
        self.batch_labeling.set_shop_state_config(x, y, width, height)
        
        # Refresh shop preview if background exists
        self.shop_preview.display_shop_background()

    def _reset_shop_state_config(self):
        """Reset shop state box configuration to defaults"""
        self.logger.log("INFO", "Shop state box configuration reset to defaults")
        
        # Reset to defaults
        self._apply_shop_state_config(
            Config.DEFAULT_SHOP_STATE_X,
            Config.DEFAULT_SHOP_STATE_Y,
            Config.DEFAULT_SHOP_STATE_WIDTH,
            Config.DEFAULT_SHOP_STATE_HEIGHT
        )
        
        # Update panel inputs
        if self.slot_config_panel:
            self.slot_config_panel.update_values(
                Config.DEFAULT_SLOT_WIDTH,
                Config.DEFAULT_SLOT_HEIGHT,
                Config.DEFAULT_SLOT_SPACING,
                Config.DEFAULT_SLOT_START_X,
                Config.DEFAULT_SLOT_START_Y,
                Config.DEFAULT_SLOT_COUNT,
                Config.DEFAULT_SHOP_STATE_X,
                Config.DEFAULT_SHOP_STATE_Y,
                Config.DEFAULT_SHOP_STATE_WIDTH,
                Config.DEFAULT_SHOP_STATE_HEIGHT
            )

    def start_batch_labeling(self):
        """Start batch labeling workflow"""
        self.batch_labeling.start_batch_labeling()

    def handle_batch_labeling_complete(self, recreate_tab=False):
        """Handle batch labeling completion"""
        if recreate_tab:
            # Recreate template labeling tab
            self.template_labeling.create_tab()
            
            # Re-add batch labeling button
            template_tab = self.tabview.tab("Template Labeling")
            label_frame = template_tab.winfo_children()[1]  # Get label frame
            
            batch_btn = ctk.CTkButton(
                label_frame,
                text="Batch Label",
                command=self.start_batch_labeling,
                width=100
            )
            batch_btn.pack(side="left", padx=(0, 10))
