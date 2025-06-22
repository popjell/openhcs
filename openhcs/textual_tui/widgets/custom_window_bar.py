"""
Custom WindowBar for OpenHCS that removes left button bar and adds separators.

Extends textual-window WindowBar to customize button layout and appearance.
"""

import logging
from typing import Any

from textual import work
from textual.app import ComposeResult
from textual.widgets import Static
from textual_window import WindowBar
from textual_window.windowbar import WindowBarAllButton, WindowBarButton
from textual_window.window import Window

logger = logging.getLogger(__name__)


# ButtonSeparator removed - not using separators anymore


class CustomWindowBar(WindowBar):
    """
    Custom WindowBar that removes the left button bar and adds separators between buttons.

    Layout: [Window1] | [Window2] | [Window3] [Right All Button]
    """

    def __init__(self, **kwargs):
        """Initialize with logging."""
        logger.info("🔘 WINDOWBAR INIT: CustomWindowBar created")
        super().__init__(**kwargs)
        logger.info(f"🔘 WINDOWBAR INIT: CustomWindowBar initialized")
        logger.info(f"🔘 WINDOWBAR INIT: Manager = {self.manager}")
        logger.info(f"🔘 WINDOWBAR INIT: Manager windowbar = {getattr(self.manager, 'windowbar', 'None')}")

        # Verify our methods are being used
        logger.info(f"🔘 WINDOWBAR INIT: add_window_button method = {self.add_window_button}")
        logger.info(f"🔘 WINDOWBAR INIT: update_window_button_state method = {self.update_window_button_state}")
    
    DEFAULT_CSS = """
    CustomWindowBar {
        align: center bottom;
        background: $panel;
    }
    WindowBarButton {
        height: 1; width: auto;
        padding: 0 1;
        &:hover { background: $panel-lighten-1; }
        &.pressed { background: $primary; color: $text; }
        &.right_pressed { background: $accent-darken-3; color: $text; }
    }
    WindowBarAllButton {
        height: 1; width: 1fr;  /* Keep 1fr to fill remaining space */
        padding: 0 1;
        &:hover { background: $boost; }
        &.pressed { background: $panel-lighten-1; }
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the window bar with only the right button (no left button)."""
        logger.info("🔘 WINDOWBAR COMPOSE: Creating CustomWindowBar")
        # Only yield the right button - no left button
        yield WindowBarAllButton(window_bar=self, id="windowbar_button_right")
        logger.info("🔘 WINDOWBAR COMPOSE: Right button created")

    def on_mount(self) -> None:
        """Log children after mounting to see what actually exists."""
        logger.info("🔘 WINDOWBAR MOUNT: CustomWindowBar mounted")
        all_children = [f"{child.__class__.__name__}(id={getattr(child, 'id', 'no-id')})" for child in self.children]
        logger.info(f"🔘 WINDOWBAR MOUNT: Children after mount: {all_children}")

        # Check if both buttons exist
        try:
            left_button = self.query_one("#windowbar_button_left")
            logger.info(f"🔘 WINDOWBAR MOUNT: Left button found: {left_button}")
        except Exception as e:
            logger.error(f"🔘 WINDOWBAR MOUNT: Left button missing: {e}")

        try:
            right_button = self.query_one("#windowbar_button_right")
            logger.info(f"🔘 WINDOWBAR MOUNT: Right button found: {right_button}")
        except Exception as e:
            logger.error(f"🔘 WINDOWBAR MOUNT: Right button missing: {e}")



    @work(group="windowbar")
    async def add_window_button(self, window: Window) -> None:
        """
        Add a window button with separator.

        Override the parent method to add separators between buttons.
        """
        try:
            logger.info(f"🔘 BUTTON CREATE START: {window.id} (name: {window.name})")

            # Check if button already exists
            try:
                existing_button = self.query_one(f"#{window.id}_button")
                logger.warning(f"🔘 BUTTON ALREADY EXISTS: {window.id} - skipping creation")
                return
            except Exception:
                pass  # Button doesn't exist, continue with creation

            display_name = (window.icon + " " + window.name) if window.icon else window.name
            logger.debug(f"🔘 BUTTON CREATE: Display name = '{display_name}'")

            # Check if right button exists
            try:
                right_button = self.query_one("#windowbar_button_right")
                logger.debug(f"🔘 BUTTON CREATE: Right button found: {right_button}")
            except Exception as e:
                logger.error(f"🔘 BUTTON CREATE: Right button missing! {e}")
                raise

            # Add the window button directly (no separators)
            logger.debug(f"🔘 BUTTON CREATE: Creating WindowBarButton for {window.id}")
            try:
                button = WindowBarButton(
                    content=display_name,
                    window=window,
                    window_bar=self,
                    id=f"{window.id}_button",
                )
                logger.debug(f"🔘 BUTTON CREATE: WindowBarButton created: {button}")

                await self.mount(
                    button,
                    before=self.query_one("#windowbar_button_right"),
                )
                logger.debug(f"🔘 BUTTON CREATE: Button mounted for {window.id}")

                # Verify button was actually added
                try:
                    verify_button = self.query_one(f"#{window.id}_button")
                    logger.info(f"🔘 BUTTON CREATE SUCCESS: {window.id} - verified in DOM")
                except Exception as e:
                    logger.error(f"🔘 BUTTON CREATE: Button not found after mount! {window.id} - {e}")
                    raise

            except Exception as e:
                logger.error(f"🔘 BUTTON CREATE: Button mount failed for {window.id} - {e}")
                raise

        except Exception as e:
            logger.error(f"🔘 BUTTON CREATE FAILED: {window.id} - {type(e).__name__}: {e}")
            import traceback
            logger.error(f"🔘 BUTTON CREATE TRACEBACK: {traceback.format_exc()}")
            raise  # Re-raise to expose the actual error

    @work(group="windowbar")
    async def remove_window_button(self, window: Window) -> None:
        """
        Remove a window button.

        Simplified version without separators.
        """
        # Remove the window button
        try:
            self.query_one(f"#{window.id}_button").remove()
            logger.info(f"🔘 BUTTON REMOVE SUCCESS: {window.id}")
        except Exception as e:
            logger.warning(f"🔘 BUTTON REMOVE FAILED: {window.id} - {e}")





    def update_window_button_state(self, window: Window, state: bool) -> None:
        """
        Override to add comprehensive logging for button state updates.

        This is called by the WindowManager when a window is minimized or opened.
        """
        logger.info(f"🔘 BUTTON UPDATE START: {window.id} -> state={state}")

        try:
            # Log current WindowBar state
            all_children = [child.id for child in self.children if hasattr(child, 'id')]
            button_children = [
                child.id for child in self.children
                if isinstance(child, WindowBarButton)
            ]
            logger.debug(f"🔘 BUTTON UPDATE: All children: {all_children}")
            logger.debug(f"🔘 BUTTON UPDATE: Button children: {button_children}")

            # Try to find the button
            button_id = f"#{window.id}_button"
            logger.debug(f"🔘 BUTTON UPDATE: Looking for button: {button_id}")

            button = self.query_one(button_id, WindowBarButton)
            logger.debug(f"🔘 BUTTON UPDATE: Found button: {button}")

            # Update the button state
            if state:
                button.window_state = True
                logger.info(f"🔘 BUTTON UPDATE SUCCESS: {window.id} -> opened")
            else:
                button.window_state = False
                logger.info(f"🔘 BUTTON UPDATE SUCCESS: {window.id} -> minimized")

        except Exception as e:
            # Button doesn't exist yet - this might be normal during window creation
            # But let's log it to see what's happening
            logger.warning(f"🔘 BUTTON UPDATE FAILED: {window.id} - {type(e).__name__}: {e}")
            logger.debug(f"🔘 BUTTON UPDATE: Current children: {[child.id for child in self.children if hasattr(child, 'id')]}")
            # The button should be added later via add_window_button

    def __getattribute__(self, name):
        """Override to log when manager accesses our methods."""
        if name == 'add_window_button':
            logger.info(f"🔘 METHOD ACCESS: Manager accessing add_window_button")
        elif name == 'update_window_button_state':
            logger.info(f"🔘 METHOD ACCESS: Manager accessing update_window_button_state")
        return super().__getattribute__(name)
