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


def draw_pause_button(target_screen: pygame.Surface, font: pygame.font.Font) -> pygame.Rect:
    """Draw the pause button on the given screen.

    Uses properties and colors from `config.settings.game_ui.pause_button`
    and `config.settings.colors`.

    Args:
        target_screen: The Pygame Surface to draw on.
        font: The Pygame Font object to use for the button text.

    Returns:
        pygame.Rect: The rectangle representing the bounds of the drawn button.
    """
    pause_cfg = settings.game_ui.pause_button

    bg_color = settings.colors.pause_button_bg # Or a more specific one if defined
    text_color = settings.colors.button_text_default # Assuming default button text color

    pause_btn_rect = pygame.Rect(
        pause_cfg.x, pause_cfg.y, pause_cfg.width, pause_cfg.height
    )

    # Draw button background (potentially with transparency if bg_color has alpha)
    # If color has alpha (e.g. from config [r,g,b,a]), create a separate surface for transparency
    if len(bg_color) == 4 and bg_color[3] < 255:
        button_surface = pygame.Surface(pause_btn_rect.size, pygame.SRCALPHA)
        button_surface.fill(bg_color)
        target_screen.blit(button_surface, pause_btn_rect.topleft)
    else:
        pygame.draw.rect(target_screen, bg_color, pause_btn_rect)

    pygame.draw.rect(target_screen, settings.colors.black, pause_btn_rect, 1)  # Border (thinner)

    text_surf = font.render(pause_cfg.text, True, text_color)
    text_rect = text_surf.get_rect(center=pause_btn_rect.center)
    target_screen.blit(text_surf, text_rect)

    return pause_btn_rect


def draw_pause_menu_overlay(target_screen: pygame.Surface):
    """Draw a semi-transparent overlay for the pause menu.

    Args:
        target_screen: The Pygame Surface to draw on (main screen).
    """
    overlay_color = settings.colors.pause_overlay_bg
    overlay_surface = pygame.Surface(target_screen.get_size(), pygame.SRCALPHA)
    overlay_surface.fill(overlay_color)
    target_screen.blit(overlay_surface, (0, 0))


def draw_pause_menu_elements(target_screen: pygame.Surface, title_font: pygame.font.Font, button_font: pygame.font.Font) -> dict[str, pygame.Rect]:
    """Draw the pause menu title and buttons.

    Calculates positions based on screen center and configured spacings.

    Args:
        target_screen: The Pygame Surface to draw on.
        title_font: Font for the "Paused" title.
        button_font: Font for the menu buttons.

    Returns:
        A dictionary mapping button IDs (e.g., 'resume', 'reset_level')
        to their pygame.Rect objects.
    """
    button_rects = {}
    screen_width = target_screen.get_width()
    screen_height = target_screen.get_height()

    menu_cfg = settings.game_ui.pause_menu

    # Draw Title
    title_surf = title_font.render(
        menu_cfg.title_text, True, settings.colors.black # Assuming black for title
    )
    # Calculate total height of menu for centering (approximate)
    num_buttons = len(menu_cfg.buttons)
    total_button_height = num_buttons * menu_cfg.button_height + max(0, num_buttons - 1) * menu_cfg.button_spacing
    title_height = title_surf.get_height()
    total_menu_height = title_height + menu_cfg.title_y_offset_before_buttons + total_button_height

    start_y = screen_height // 2 - total_menu_height // 2

    title_rect = title_surf.get_rect(center=(screen_width // 2, start_y + title_height // 2))
    target_screen.blit(title_surf, title_rect)

    current_y = start_y + title_height + menu_cfg.title_y_offset_before_buttons

    # Draw Buttons
    for btn_def in menu_cfg.buttons:
        btn_id = btn_def.id
        btn_text = btn_def.text

        btn_rect = pygame.Rect(
            screen_width // 2 - menu_cfg.button_width // 2,
            current_y,
            menu_cfg.button_width,
            menu_cfg.button_height
        )
        button_rects[btn_id] = btn_rect

        # Draw button background and border
        pygame.draw.rect(target_screen, settings.colors.pause_menu_button_bg, btn_rect)
        pygame.draw.rect(target_screen, settings.colors.black, btn_rect, 2)

        # Render and blit text
        text_surf = button_font.render(btn_text, True, settings.colors.button_text_default)
        text_rect = text_surf.get_rect(center=btn_rect.center)
        target_screen.blit(text_surf, text_rect)

        current_y += menu_cfg.button_height + menu_cfg.button_spacing

    return button_rects


def draw_win_screen_elements(
    target_screen: pygame.Surface,
    title_font: pygame.font.Font,
    stats_font: pygame.font.Font, # Font for stats like V, E, Time
    button_font: pygame.font.Font, # Font for button text
    game_session_data: dict # Contains num_vertices, num_edges, elapsed_time
) -> dict[str, pygame.Rect]:
    """Draw the win screen title, game statistics, and action buttons.

    Calculates positions based on screen center and configured spacings.

    Args:
        target_screen: The Pygame Surface to draw on.
        title_font: Font for the "You Win!" title.
        stats_font: Font for the game statistics.
        button_font: Font for the menu buttons.
        game_session_data: A dictionary with keys 'num_vertices', 'num_edges',
                           and 'elapsed_time'.

    Returns:
        A dictionary mapping button IDs (e.g., 'new_game', 'retry_same')
        to their pygame.Rect objects.
    """
    button_rects = {}
    screen_width = target_screen.get_width()
    screen_height = target_screen.get_height()

    win_cfg = settings.game_ui.win_screen
    colors = settings.colors

    # --- Calculate total height for vertical centering ---
    title_surf_temp = title_font.render("You Win!", True, colors.win_message)
    title_height = title_surf_temp.get_height()

    stats_texts = [
        f"Vertices: {game_session_data['num_vertices']}",
        f"Edges: {game_session_data['num_edges']}",
        f"Time: {game_session_data['elapsed_time']:.1f}s",
    ]
    stats_surfaces = [stats_font.render(text, True, colors.win_message) for text in stats_texts]
    stats_total_height = sum(s.get_height() for s in stats_surfaces) + max(0, len(stats_surfaces) - 1) * win_cfg.stats_spacing_after

    num_buttons = len(win_cfg.buttons)
    buttons_total_height = num_buttons * win_cfg.button_height + max(0, num_buttons - 1) * win_cfg.button_spacing

    total_content_height = (
        title_height + win_cfg.title_spacing_after +
        stats_total_height + win_cfg.buttons_block_spacing_before +
        buttons_total_height
    )
    current_y = screen_height // 2 - total_content_height // 2

    # 1. Draw Title
    title_rect = title_surf_temp.get_rect(center=(screen_width // 2, current_y + title_height // 2))
    target_screen.blit(title_surf_temp, title_rect)
    current_y += title_height + win_cfg.title_spacing_after

    # 2. Draw Stats
    for stat_surf in stats_surfaces:
        stat_rect = stat_surf.get_rect(center=(screen_width // 2, current_y + stat_surf.get_height() // 2))
        target_screen.blit(stat_surf, stat_rect)
        current_y += stat_surf.get_height() + win_cfg.stats_spacing_after

    current_y += win_cfg.buttons_block_spacing_before - win_cfg.stats_spacing_after # Adjust spacing before buttons

    # 3. Draw Buttons
    for btn_def in win_cfg.buttons:
        btn_id = btn_def.id
        btn_text = btn_def.text

        btn_rect = pygame.Rect(
            screen_width // 2 - win_cfg.button_width // 2, # Assuming all win buttons share same width from config
            current_y,
            win_cfg.button_width,
            win_cfg.button_height
        )
        button_rects[btn_id] = btn_rect

        # Determine button background color from config based on id
        bg_color_key = f"win_screen_button_{btn_id}_bg" # e.g., win_screen_button_new_game_bg
        btn_bg_color = getattr(colors, bg_color_key, colors.button_text_default) # Fallback color

        pygame.draw.rect(target_screen, btn_bg_color, btn_rect)
        pygame.draw.rect(target_screen, colors.black, btn_rect, 2) # Border

        text_surf = button_font.render(btn_text, True, colors.button_text_default)
        text_rect = text_surf.get_rect(center=btn_rect.center)
        target_screen.blit(text_surf, text_rect)

        current_y += win_cfg.button_height + win_cfg.button_spacing

    return button_rects


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
        settings.colors.input_box_active_bg # Corrected path
        if text_box_is_active
        else settings.colors.input_box_inactive_bg # Corrected path
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
    pygame.draw.rect(screen, settings.colors.input_start_button_bg, start_button_rect) # Corrected path
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
