from __future__ import annotations

import imgui
import os

from .base_pane import BasePane
from grad_applicant_system.presentation.ui.viewmodels.message_composer_viewmodel import (
    MessageComposerViewModel,
    TranscriptEntry,
)


class TopMenuPane(BasePane):
    """Top application menu strip."""

    def __init__(self, viewmodel: MessageComposerViewModel) -> None:
        super().__init__()
        self._viewmodel = viewmodel

    def render(self) -> None:
        if not imgui.BeginMainMenuBar():
            return

        try:
            if imgui.BeginMenu("File"):
                try:
                    # Upload PDF
                    try:
                        if self._menu_item_clicked("Upload PDF..."):
                            # open native file dialog (tkinter) to pick a PDF
                            try:
                                import tkinter as _tk
                                from tkinter import filedialog as _fd

                                _tk_root = _tk.Tk()
                                _tk_root.withdraw()
                                paths = _fd.askopenfilenames(
                                    filetypes=[("PDF files", "*.pdf")]
                                )
                                _tk_root.destroy()
                            except Exception:
                                paths = ()

                            # `askopenfilenames` returns a tuple of paths
                            if paths:
                                # normalize single-selection to list for downstream
                                selected = list(paths)
                            else:
                                selected = []

                            # Validate and ingest selected files
                            if not selected:
                                selected = []

                            valid_paths = []
                            for p in selected:
                                valid = False
                                try:
                                    if p.lower().endswith(".pdf"):
                                        with open(p, "rb") as _f:
                                            valid = _f.read(4) == b"%PDF"
                                except Exception:
                                    valid = False

                                if not valid:
                                    self._viewmodel._transcript.append(
                                        TranscriptEntry(role="system", text=f"Selected file is not a valid PDF: {p}")
                                    )
                                else:
                                    valid_paths.append(p)

                            if valid_paths:
                                # Use batch ingest when multiple files provided
                                if len(valid_paths) == 1:
                                    self._viewmodel.ingest_pdf(valid_paths[0])
                                else:
                                    self._viewmodel.ingest_pdfs(valid_paths)
                    except Exception:
                        # swallow UI-level errors to avoid crashing menu
                        pass

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