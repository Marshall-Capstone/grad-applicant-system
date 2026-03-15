from __future__ import annotations

import imgui

from .base_pane import BasePane
from grad_applicant_system.presentation.ui.viewmodels.search_pane_viewmodel import (
    SearchPaneViewModel,
)


class TopMenuPane(BasePane):
    """Top application menu strip."""

    def __init__(self, viewmodel: SearchPaneViewModel) -> None:
        super().__init__()
        self._viewmodel = viewmodel

    def render(self) -> None:
        if not imgui.BeginMainMenuBar():
            return

        try:
            if imgui.BeginMenu("File"):
                try:
                    imgui.BeginDisabled(not self._viewmodel.can_clear)
                    try:
                        if self._menu_item_clicked("Clear conversation"):
                            self._viewmodel.clear_conversation()
                    finally:
                        imgui.EndDisabled()
                finally:
                    imgui.EndMenu()

            if imgui.BeginMenu("View"):
                try:
                    imgui.BeginDisabled(True)
                    try:
                        self._menu_item_clicked("Shell styling coming soon")
                    finally:
                        imgui.EndDisabled()
                finally:
                    imgui.EndMenu()
        finally:
            imgui.EndMainMenuBar()

    @staticmethod
    def _menu_item_clicked(label: str) -> bool:
        result = imgui.MenuItem(label)
        if isinstance(result, tuple):
            return bool(result[0])
        return bool(result)