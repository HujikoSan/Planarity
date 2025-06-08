"""Configuration loader for the Planarity game.

This module loads settings from a YAML file (typically 'config.yaml'),
converts the settings into an accessible object structure, and makes them
available for other modules in the application. It handles potential
errors during file loading or parsing by providing default or empty settings.
"""
import yaml
import os


class DictToObject:
    """Convert a dictionary to an object with attributes.

    This class recursively transforms a dictionary and its nested dictionaries
    into objects, allowing attribute-style access (e.g., `obj.key.subkey`)
    instead of dictionary-style access (e.g., `obj['key']['subkey']`).
    Lists within the dictionary are also processed: if they contain dictionaries,
    those are converted to DictToObject instances as well.

    Attributes:
        All keys from the input dictionary become attributes of the instance.
    """

    def __init__(self, **entries):
        """Initialize DictToObject from dictionary entries.

        Args:
            **entries: Keyword arguments representing the dictionary to convert.
        """
        for key, value in entries.items():
            if isinstance(value, dict):
                self.__dict__[key] = DictToObject(**value)
            elif isinstance(value, list):
                self.__dict__[key] = [
                    DictToObject(**item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                self.__dict__[key] = value

    def __repr__(self) -> str:
        """Return a string representation of the object's attributes.

        Returns:
            A string showing the dictionary representation of the object.
        """
        return f"{self.__dict__}"

    def get(self, key: str, default=None):
        """Provide a dictionary-like 'get' method for attribute access.

        Args:
            key: The attribute name to retrieve.
            default: The value to return if the attribute is not found.

        Returns:
            The value of the attribute, or the default value if not found.
        """
        return self.__dict__.get(key, default)


def _to_tuple_if_list(value):
    """Recursively convert lists of numbers (likely colors) into tuples.

    Pygame generally prefers tuples for color definitions. This function
    traverses the configuration structure (which might be nested DictToObjects
    and lists) and converts lists where all elements are numbers into tuples.

    Args:
        value: The value to process (can be a list, DictToObject, or other type).

    Returns:
        The processed value, with relevant lists converted to tuples.
    """
    if isinstance(value, list):
        if all(isinstance(x, (int, float)) for x in value):
            return tuple(value)
        return [_to_tuple_if_list(item) for item in value]
    elif isinstance(value, DictToObject):
        for key, attr_value in value.__dict__.items():
            value.__dict__[key] = _to_tuple_if_list(attr_value)
        return value
    return value


def load_config(filepath: str = "config.yaml") -> DictToObject:
    """Load configuration settings from a YAML file.

    This function reads a specified YAML file, parses its content,
    and transforms it into a DictToObject for easy access. It also attempts
    to convert color-related lists to tuples for Pygame compatibility.
    If the file is not found or if there's an error during parsing,
    it prints a warning and returns an empty configuration object.

    Args:
        filepath: The path to the YAML configuration file.
                  Defaults to 'config.yaml'.

    Returns:
        A DictToObject instance containing the configuration settings.
        Returns an empty DictToObject if the file is not found or parsing fails.
    """
    if not os.path.exists(filepath):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filepath)

    config_dict = {}
    try:
        with open(filepath, "r") as f:
            config_dict = yaml.safe_load(f)
        if not config_dict:
            config_dict = {}
    except FileNotFoundError:
        print(f"Warning: Configuration file '{filepath}' not found. Using empty config.")
        config_dict = {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file '{filepath}': {e}. Using empty config.")
        config_dict = {}

    config_object = DictToObject(**config_dict)

    # Convert color lists to tuples after loading the main structure
    # This ensures that color definitions like [255, 255, 255] become (255, 255, 255)
    # which is preferred by Pygame.
    if hasattr(config_object, "colors"):
        config_object.colors = _to_tuple_if_list(config_object.colors)
    if hasattr(config_object, "screen") and hasattr(
        config_object.screen, "background_color"
    ):
        config_object.screen.background_color = _to_tuple_if_list(
            config_object.screen.background_color
        )
    if hasattr(config_object, "ui"):
        if hasattr(config_object.ui, "input_box"):
            if hasattr(config_object.ui.input_box, "inactive_color"):
                config_object.ui.input_box.inactive_color = _to_tuple_if_list(
                    config_object.ui.input_box.inactive_color
                )
            if hasattr(config_object.ui.input_box, "active_color"):
                config_object.ui.input_box.active_color = _to_tuple_if_list(
                    config_object.ui.input_box.active_color
                )
        if hasattr(config_object.ui, "button"):
            if hasattr(config_object.ui.button, "color"):
                config_object.ui.button.color = _to_tuple_if_list(
                    config_object.ui.button.color
                )
            if hasattr(config_object.ui.button, "text_color"):
                config_object.ui.button.text_color = _to_tuple_if_list(
                    config_object.ui.button.text_color
                )
        # Add more specific UI color conversions if necessary, following the pattern.

    return config_object


# Load configuration when the module is imported.
# The 'settings' object will be used by other modules to access configuration values.
settings: DictToObject = load_config()

if __name__ == "__main__":
    # This block is for testing the configuration loading.
    # It prints some sample values to verify that the config was loaded correctly.
    print("Config loaded. Accessing some values:")
    if settings and settings.screen:
        print(f"Screen Width: {settings.screen.default_width}")
        print(f"Screen Height: {settings.screen.default_height}")
        print(
            f"Background Color: {settings.screen.background_color} "
            f"(type: {type(settings.screen.background_color)})"
        )
    if settings and settings.colors:
        print(
            f"White Color: {settings.colors.white} "
            f"(type: {type(settings.colors.white)})"
        )
        print(
            f"Vertex Default Color: {settings.colors.vertex_default} "
            f"(type: {type(settings.colors.vertex_default)})"
        )
    if settings and settings.vertex:
        print(f"Vertex Radius: {settings.vertex.radius}")
    if settings and settings.font_sizes:
        print(f"Title Font Size: {settings.font_sizes.title}")
    if settings and settings.ui and settings.ui.input_box:
        print(f"Input Box Active BG: {settings.ui.input_box.active_color}")

    print(f"Game Title: {settings.get('game_title', 'Default Title')}")
    non_existent = settings.get("non_existent_key")
    print(f"Non Existent Key: {non_existent} (type: {type(non_existent)})")

    if (
        settings
        and settings.ui
        and settings.ui.win_screen
        and settings.ui.win_screen.buttons
    ):
        print("Win screen buttons:")
        for button_cfg in settings.ui.win_screen.buttons:
            print(f"  ID: {button_cfg.id}, Text: {button_cfg.text}")

    # Check if specific color values were converted to tuples
    if settings.colors and isinstance(settings.colors.white, tuple):
        print("settings.colors.white is a tuple.")
    else:
        print("settings.colors.white is NOT a tuple.")

    if settings.screen and isinstance(settings.screen.background_color, tuple):
        print("settings.screen.background_color is a tuple.")
    else:
        print("settings.screen.background_color is NOT a tuple.")

    # Test if Pygame can use a loaded color
    import pygame  # Local import for testing

    try:
        s = pygame.Surface((10, 10))
        if settings.colors and settings.colors.white:
            s.fill(settings.colors.white)
            print("Pygame fill with settings.colors.white successful.")
        if settings.screen and settings.screen.background_color:
            s.fill(settings.screen.background_color)
            print("Pygame fill with settings.screen.background_color successful.")
        if settings.ui.input_box.active_color:
            s.fill(settings.ui.input_box.active_color)
            print(
                f"Pygame fill with input_box.active_color "
                f"{settings.ui.input_box.active_color} successful."
            )

    except Exception as e:
        print(f"Error testing Pygame color: {e}")
