"""Modified TkinterMapView for use with the paldea map"""

import os.path
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk
from .corrected_marker import CorrectedMarker

class PaldeaMapView(TkinterMapView):
    """Modified TkinterMapView for use with the paldea map"""
    def __init__(
        self,
        *args,
        width: int = 512,
        height: int = 512,
        corner_radius: int = 0,
        bg_color: str = None,
        database_path: str = None,
        use_database_only: bool = False,
        max_zoom: int = 5,
        **kwargs
    ):
        super().__init__(
            *args,
            width=width,
            height=height,
            corner_radius=corner_radius,
            bg_color=bg_color,
            database_path=database_path,
            use_database_only=use_database_only,
            max_zoom=max_zoom,
            **kwargs
        )

    def pre_cache(self):
        # disable precaching
        pass

    def check_map_border_crossing(self):
        diff_x, diff_y = 0, 0
        if self.upper_left_tile_pos[0] < 0:
            diff_x += 0 - self.upper_left_tile_pos[0]

        if self.upper_left_tile_pos[1] < 0:
            diff_y += 0 - self.upper_left_tile_pos[1]
        if self.lower_right_tile_pos[0] > 2 ** round(self.zoom):
            diff_x -= self.lower_right_tile_pos[0] - (2 ** round(self.zoom))
        if self.lower_right_tile_pos[1] > 2 ** round(self.zoom):
            diff_y -= self.lower_right_tile_pos[1] - (2 ** round(self.zoom))

        self.upper_left_tile_pos = \
            self.upper_left_tile_pos[0] + diff_x, self.upper_left_tile_pos[1] + diff_y
        self.lower_right_tile_pos = \
            self.lower_right_tile_pos[0] + diff_x, self.lower_right_tile_pos[1] + diff_y

    def update_dimensions(self, event):
        if self.width != event.width or self.height != event.height:
            self.width = event.width
            self.height = event.height

    def request_image(self, zoom: int, x: int, y: int, db_cursor=None):
        # bounds checking
        if not (
            0 < zoom <= self.max_zoom # ensure zoom is a valid value
            and 2 ** zoom > max(x, y) # ensure x and y are within zoom scale
            and min(x, y) >= 0 # ensure x and y are non negative
        ):
            return self.empty_tile_image
        # files are stored with zoom inverted
        zoom = 5 - zoom
        # TODO: dynamic path?
        path = f"resources/map/{zoom}_{x}_{y}.png"
        if os.path.exists(path):
            img = ImageTk.PhotoImage(Image.open(path))
            self.tile_image_cache[f'z{zoom}x{x}y{y}'] = img
            return img
        return self.empty_tile_image

    def set_marker(self, deg_x: float, deg_y: float, text: str = None, **kwargs) -> CorrectedMarker:
        marker = CorrectedMarker(self, (deg_x, deg_y), text=text, **kwargs)
        marker.draw()
        self.canvas_marker_list.append(marker)
        return marker
