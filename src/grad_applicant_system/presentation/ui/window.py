from __future__ import annotations

from typing import Callable

import imgui as im
import imgui.glfw as glfw


class Window:
    """Owns GLFW + ImGui context lifecycle and the main frame loop."""

    def __init__(
        self,
        title: str = "Grad Applicant System",
        width: int = 1280,
        height: int = 720,
        glsl_version: str = "#version 130",
    ) -> None:
        self._title = title
        self._width = width
        self._height = height
        self._glsl_version = glsl_version

        self._window = None
        self._clear_color = im.Vec4(0.05, 0.06, 0.08, 1.0)
        self._initialized = False

    @property
    def native_window(self):
        return self._window

    def _error_callback(self, err: int, msg: str) -> None:
        print(f"GLFW Error Code: {err}, Msg: {msg}")

    def initialize(self) -> None:
        if self._initialized:
            return

        glfw.SetErrorCallback(self._error_callback)

        if not glfw.Init():
            raise RuntimeError("Could not initialize GLFW.")

        glfw.WindowHint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.WindowHint(glfw.CONTEXT_VERSION_MINOR, 6)

        self._window = glfw.CreateWindow(self._width, self._height, self._title)
        if self._window is None:
            glfw.Terminate()
            raise RuntimeError("Could not create GLFW window.")

        glfw.MakeContextCurrent(self._window)
        glfw.SwapInterval(1)

        im.CreateContext()
        im.InitContextForGLFW(self._window, self._glsl_version)
        im.StyleColorsDark()

        self._initialized = True

    def shutdown(self) -> None:
        if not self._initialized:
            return

        if self._window is not None:
            glfw.DestroyWindow(self._window)
            self._window = None

        im.Shutdown()
        im.DestroyContext()
        glfw.Terminate()

        self._initialized = False

    def run(self, draw_frame: Callable[[], bool]) -> None:
        self.initialize()

        try:
            while True:
                glfw.PollEvents()
                im.NewFrame()

                should_exit = draw_frame()

                im.Render(self._window, self._clear_color)
                glfw.SwapBuffers(self._window)

                if should_exit or glfw.WindowShouldClose(self._window):
                    break
        finally:
            self.shutdown()