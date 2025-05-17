class ColorPalette:
    def __init__(self, colors):
        if len(colors) != 6:
            raise ValueError("A palette must have exactly 6 colors.")
        self.colors = colors

    def __getitem__(self, idx):
        return self.colors[idx]

    def __iter__(self):
        return iter(self.colors)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.colors})"


# Common palettes
class PastelPalette(ColorPalette):
    def __init__(self):
        super().__init__(
            ["#aec6cf", "#ffb347", "#b39eb5", "#77dd77", "#f49ac2", "#ffe29a"]
        )


class VibrantPalette(ColorPalette):
    def __init__(self):
        super().__init__(
            ["#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4"]
        )


class BluesPalette(ColorPalette):
    def __init__(self):
        super().__init__(
            ["#4f8ef7", "#7ec8e3", "#012169", "#89cff0", "#325288", "#0096c7"]
        )


class WarmPalette(ColorPalette):
    def __init__(self):
        super().__init__(
            ["#ff6f61", "#ffb347", "#ffd166", "#f67280", "#c06c84", "#ffb4a2"]
        )


class EarthPalette(ColorPalette):
    def __init__(self):
        super().__init__(
            ["#a0522d", "#cd853f", "#deb887", "#8b7765", "#bc987e", "#c19a6b"]
        )


def get_all_color_palettes():
    return {
        "Pastel": PastelPalette(),
        "Vibrant": VibrantPalette(),
        "Blues": BluesPalette(),
        "Warm": WarmPalette(),
        "Earth": EarthPalette(),
    }
