"""Functions for drawing game elements using Pygame.

This module provides functions to render the visual components of the
Planarity game, such as the graph (vertices and edges), input screens,
and UI elements. It relies on Pygame for drawing operations and uses
configuration settings for styling (colors, sizes, etc.).
"""
import pygame
import io
from PIL import Image
import win32clipboard  # For clipboard functionality in capture_game_view

from typing import Optional, Set, List # Added type hints

# Project modules
from config import settings
from game_logic import Graph, Vertex, Edge # Import classes from game_logic


# Global 'screen' variable, similar to planarity.py. This is generally not
# ideal and is a candidate for refactoring (e.g., passing screen as a parameter
# to drawing functions or using a display manager class).
screen = None


def set_screen(pygame_screen: pygame.Surface, width: int, height: int):
    """Set the global screen variable and dimensions for drawing functions.

    Note: This global screen is a temporary measure and planned for refactoring.
    The width and height parameters are for the Pygame screen object and might
    not directly correspond to all internal drawing dimension calculations if
    those are based on dynamic window resizing.

    Args:
        pygame_screen: The Pygame Surface object representing the main display.
        width: The current width of the screen.
        height: The current height of the screen.
    """
    global screen
    screen = pygame_screen
    # current_screen_width and current_screen_height are typically passed to
    # specific drawing functions or sourced from settings for dynamic UI.


def capture_game_view(
    screen_w_param: int,
    screen_h_param: int,
    graph: Graph, # Changed to Graph object
    crossing_edges: Set[Edge], # Changed to Set of Edge objects
    elapsed_t_stat: float,
    filename: Optional[str] = None,
) -> Optional[str]:
    """Create an image of the current graph view and copy to clipboard or save.

    Renders the graph (vertices, edges with crossing highlights) and game statistics
    (number of vertices, edges, elapsed time) onto a new Pygame surface.
    Attempts to copy this image to the system clipboard. If clipboard access fails
    or is not available, it falls back to saving the image to a file.

    The appearance (colors, radii, line thickness, font sizes) is determined
    by values from the `config.settings`.

    Args:
        screen_w_param: The width for the capture surface.
        screen_h_param: The height for the capture surface.
        graph: The Graph object containing vertices and edges.
        crossing_edges: A set of Edge objects that are currently crossing.
        elapsed_t_stat: The current elapsed game time (for stats display).
        filename: Optional. The filename to use if saving to a file.
                  If None, uses `settings.screenshot_default_filename`.

    Returns:
        A string indicating the result: "clipboard" if copied successfully,
        the `filename` if saved successfully, or None if both operations failed.
    """
    if filename is None:
        filename = settings.screenshot_default_filename

    capture_surface = pygame.Surface((screen_w_param, screen_h_param))
    capture_surface.fill(settings.screen.background_color)

    # Draw edges
    edge_thickness = settings.edge.line_thickness
    crossing_color = settings.colors.edge_crossing
    non_crossing_color = settings.colors.edge_non_crossing
    for edge in graph.edges:
        start_pos = (edge.v1.x, edge.v1.y)
        end_pos = (edge.v2.x, edge.v2.y)
        edge_is_crossing = edge in crossing_edges
        edge_color = crossing_color if edge_is_crossing else non_crossing_color
        pygame.draw.line(
            capture_surface, edge_color, start_pos, end_pos, edge_thickness
        )

    # Draw vertices
    vertex_radius = settings.vertex.radius
    vertex_color = settings.colors.vertex_default
    for vertex in graph.vertices:
        pygame.draw.circle(capture_surface, vertex_color, (vertex.x, vertex.y), vertex_radius)

    # Draw stats text
    num_v_stat = len(graph.vertices)
    num_e_stat = len(graph.edges)
    stats_font = None
    try:
        stats_font = pygame.font.Font(None, settings.font_sizes.small_ui)
    except Exception as e:
        print(
            f"Failed to load font (size {settings.font_sizes.small_ui}) "
            f"for screenshot stats: {e}"
        )

    if stats_font:
        texts_to_render = [
            f"Vertices: {num_v_stat}",
            f"Edges: {num_e_stat}",
            f"Time: {elapsed_t_stat:.1f}s",
        ]
        line_height = (
            stats_font.get_height() + settings.game_ui.screenshot_stats_line_spacing
        )
        current_y_text = settings.game_ui.screenshot_stats_y_padding
        text_x_pos = settings.game_ui.screenshot_stats_x_padding
        for text_str in texts_to_render:
            text_surface = stats_font.render(
                text_str, True, settings.colors.black
            )
            capture_surface.blit(text_surface, (text_x_pos, current_y_text))
            current_y_text += line_height
    try:
        image_str = pygame.image.tostring(capture_surface, "RGB")
        image_size = capture_surface.get_size()
        image_pil = Image.frombytes("RGB", image_size, image_str)
        output = io.BytesIO()
        image_pil.save(output, "BMP")
        data = output.getvalue()[14:]  # Strip BMP header
        output.close()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        print("Screenshot copied to clipboard.")
        return "clipboard"
    except Exception as e:
        print(f"Error copying screenshot to clipboard: {e}. Trying to save to file.")
        try:
            pygame.image.save(capture_surface, filename)
            print(f"Screenshot saved to {filename}")
            return filename
        except Exception as e_save:
            print(f"Error saving screenshot to file '{filename}': {e_save}")
            return None


def draw_graph(
    graph: Graph, # Changed to Graph object
    crossing_edges: Optional[Set[Edge]] = None, # Changed to Set of Edge objects
):
    """Draw the graph (vertices and edges) on the global screen.

    Uses styling (colors, radius, thickness) from `config.settings`.
    Vertices are drawn as circles, and edges as lines. Crossing edges
    are highlighted with a different color.

    Args:
        graph: The Graph object containing vertices and edges.
        crossing_edges: An optional set of Edge objects that are currently crossing.
                        If None, no edges are highlighted as crossing.
    """
    global screen
    if screen is None:
        print("Error: Screen not set for draw_graph. Cannot draw.")
        return
    if crossing_edges is None:
        crossing_edges = set()

    edge_thickness = settings.edge.line_thickness
    vertex_radius = settings.vertex.radius
    vertex_color = settings.colors.vertex_default
    crossing_color = settings.colors.edge_crossing
    non_crossing_color = settings.colors.edge_non_crossing

    for edge in graph.edges:
        start_pos = (edge.v1.x, edge.v1.y)
        end_pos = (edge.v2.x, edge.v2.y)
        edge_is_crossing = edge in crossing_edges
        edge_color = crossing_color if edge_is_crossing else non_crossing_color
        pygame.draw.line(screen, edge_color, start_pos, end_pos, edge_thickness)

    for vertex in graph.vertices:
        pygame.draw.circle(screen, vertex_color, (vertex.x, vertex.y), vertex_radius)


def draw_input_screen(
    text_input_font: pygame.font.Font,
    title_font: pygame.font.Font,
    current_input_text: str,
    error_msg_text: str,
    text_box_is_active: bool,
    current_screen_width: int,
    current_screen_height: int,
):
    """Draw the screen for user to input the number of vertices.

    This screen includes a title/prompt, a text input box for the number
    of vertices, a "Start" button, and an area for displaying error messages.
    Layout and styling are determined by `config.settings`.

    Args:
        text_input_font: Pygame Font object for the input field and button text.
        title_font: Pygame Font object for the main title/prompt.
        current_input_text: The string currently entered by the user.
        error_msg_text: Any error message to be displayed.
        text_box_is_active: Boolean indicating if the text input box has focus.
        current_screen_width: Current width of the game window.
        current_screen_height: Current height of the game window.
    """
    global screen
    if screen is None:
        print("Error: Screen not set for draw_input_screen. Cannot draw.")
        return

    screen.fill(settings.screen.background_color)

    box_cfg = settings.text_input_ui

    # Calculate positions for UI elements based on current screen dimensions and config
    text_box_rect = pygame.Rect(
        current_screen_width // 2 - box_cfg.box_width // 2,
        current_screen_height // 2 - box_cfg.box_height // 2,
        box_cfg.box_width,
        box_cfg.box_height,
    )
    start_button_rect = pygame.Rect(
        current_screen_width // 2 - box_cfg.start_button_width // 2,
        text_box_rect.bottom + (box_cfg.start_button_y_offset - box_cfg.box_height / 2 - box_cfg.start_button_height / 2), # Adjusted offset logic
        box_cfg.start_button_width,
        box_cfg.start_button_height,
    )
    start_button_rect.centerx = text_box_rect.centerx # Ensure alignment

    # Draw title/prompt
    prompt_text_str = (
        f"Enter Vertices ({settings.vertex.min_count}-{settings.vertex.max_count}):"
    )
    prompt_surface = title_font.render(
        prompt_text_str, True, settings.colors.prompt_text
    )
    prompt_rect = prompt_surface.get_rect(
        center=(current_screen_width // 2, text_box_rect.y - box_cfg.prompt_y_offset)
    )
    screen.blit(prompt_surface, prompt_rect)

    # Draw text input box
    box_bg_color = (
        settings.ui.input_box.active_color
        if text_box_is_active
        else settings.ui.input_box.inactive_color
    )
    pygame.draw.rect(screen, box_bg_color, text_box_rect)
    pygame.draw.rect(screen, settings.colors.black, text_box_rect, 2)  # Border

    input_text_surface = text_input_font.render(
        current_input_text, True, settings.colors.black
    )
    screen.blit(
        input_text_surface,
        (
            text_box_rect.x + box_cfg.text_x_padding,
            text_box_rect.y + (text_box_rect.height - input_text_surface.get_height()) // 2,
        ),
    )

    # Draw Start button
    pygame.draw.rect(screen, settings.ui.input_start_button_bg, start_button_rect)
    pygame.draw.rect(screen, settings.colors.black, start_button_rect, 2)  # Border

    start_text_surface = text_input_font.render(
        "Start", True, settings.colors.button_text_default
    )
    start_text_rect = start_text_surface.get_rect(center=start_button_rect.center)
    screen.blit(start_text_surface, start_text_rect)

    # Draw error message, if any
    if error_msg_text:
        error_surface = text_input_font.render(
            error_msg_text, True, settings.colors.error_text
        )
        error_rect = error_surface.get_rect(
            center=(
                current_screen_width // 2,
                start_button_rect.bottom + box_cfg.error_message_y_offset,
            )
        )
        screen.blit(error_surface, error_rect)

    pygame.display.flip()  # Update the full display
