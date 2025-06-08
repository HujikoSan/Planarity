"""Functions for handling user input for the Planarity game.

This module is responsible for processing Pygame events related to
user input during different game states, such as the initial input screen
for selecting vertex count, and the main game session for interacting
with the graph and UI elements (e.g., pause button, win screen options).
"""

import pygame
import sys
import webbrowser  # For opening URLs (e.g., Post to X)
import urllib.parse  # For encoding URL parameters
from typing import Optional, Union # Added for type hints

# Project module
from config import settings

# Placeholder for game_logic classes if needed later
# from game_logic import GameSession, Vertex
# import drawing # Might be needed if input handling directly triggers drawing updates


def handle_input_screen_logic(
    events: list[pygame.event.Event],
    current_input_text: str,
    text_box_is_active: bool,
    error_message: str,
    current_screen_width: int,
    current_screen_height: int,
) -> tuple[str, bool, str, Optional[Union[int, str]]]:
    """Handle events and logic for the vertex number input screen.

    Processes Pygame events to manage text input for the number of vertices,
    button clicks ("Start"), and Enter key presses. Validates the input
    based on configured min/max vertex counts.

    Args:
        events: A list of Pygame events to process.
        current_input_text: The current text string in the input box.
        text_box_is_active: True if the input box currently has focus.
        error_message: The current error message string to be displayed.
        current_screen_width: Current width of the game window.
        current_screen_height: Current height of the game window.

    Returns:
        A tuple containing:
            - new_input_text (str): The updated input text.
            - new_text_box_active (bool): The updated active state of the input box.
            - new_error_message (str): The updated error message.
            - action (Optional[Union[int, str]]):
                - An integer (number of vertices) if "Start" is clicked or Enter
                  is pressed with valid input.
                - "QUIT_APP" (str) if a quit event is detected.
                - None otherwise, indicating no state-changing action.
    """
    action_taken: Optional[Union[int, str]] = None
    new_error_message = error_message  # Persist error unless cleared

    box_cfg = settings.text_input_ui

    local_text_box_rect = pygame.Rect(
        current_screen_width // 2 - box_cfg.box_width // 2,
        current_screen_height // 2 - box_cfg.box_height // 2,
        box_cfg.box_width,
        box_cfg.box_height,
    )
    local_start_button_rect = pygame.Rect(
        current_screen_width // 2 - box_cfg.start_button_width // 2,
        local_text_box_rect.centery
        + box_cfg.start_button_y_offset
        - box_cfg.start_button_height // 2,
        box_cfg.start_button_width,
        box_cfg.start_button_height,
    )

    for event in events:
        if event.type == pygame.QUIT:
            return current_input_text, text_box_is_active, new_error_message, "QUIT_APP"

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if local_text_box_rect.collidepoint(event.pos):
                    text_box_is_active = True
                    new_error_message = ""
                else:
                    text_box_is_active = False

                if local_start_button_rect.collidepoint(event.pos):
                    text_box_is_active = False
                    try:
                        if not current_input_text:
                            new_error_message = "Input is empty!"
                        else:
                            num_v = int(current_input_text)
                            if (
                                settings.vertex.min_count
                                <= num_v
                                <= settings.vertex.max_count
                            ):
                                action_taken = num_v
                                new_error_message = ""
                            else:
                                new_error_message = (
                                    f"Range: {settings.vertex.min_count}-"
                                    f"{settings.vertex.max_count}"
                                )
                    except ValueError:
                        new_error_message = "Invalid number!"

        if event.type == pygame.KEYDOWN:
            if text_box_is_active:
                new_error_message = ""
                if event.key == pygame.K_RETURN:
                    try:
                        if not current_input_text:
                            new_error_message = "Input is empty!"
                        else:
                            num_v = int(current_input_text)
                            if (
                                settings.vertex.min_count
                                <= num_v
                                <= settings.vertex.max_count
                            ):
                                action_taken = num_v
                                new_error_message = ""
                            else:
                                new_error_message = (
                                    f"Range: {settings.vertex.min_count}-"
                                    f"{settings.vertex.max_count}"
                                )
                    except ValueError:
                        new_error_message = "Invalid number!"
                elif event.key == pygame.K_BACKSPACE:
                    current_input_text = current_input_text[:-1]
                else:
                    max_len_input = len(str(settings.vertex.max_count))
                    if (
                        event.unicode.isdigit()
                        and len(current_input_text) < max_len_input
                    ):
                        current_input_text += event.unicode
                    elif not event.unicode.isdigit() and event.key != pygame.K_BACKSPACE:
                        new_error_message = "Only digits allowed."

    return current_input_text, text_box_is_active, new_error_message, action_taken


def handle_game_events(
    events: list[pygame.event.Event], game_session, config_params: dict
) -> str:
    """Handle Pygame events during the main game session.

    Processes user interactions such as mouse clicks for selecting and dragging
    vertices, interacting with UI buttons (pause, win screen options), and
    window events like resizing or quitting. Modifies `game_session` state
    accordingly (e.g., selected vertex, pause state) and uses `config_params`
    for dynamic UI element information.

    Note: This function currently uses several 'HACK' attributes on `game_session`
    (e.g., `temp_vertices_coords_hack`) which are placeholders for proper
    integration with the `GameSession` and `Graph` classes.

    Args:
        events: A list of Pygame events to process.
        game_session: The current `GameSession` object, which holds game state.
                      This object will be modified by this function.
        config_params: A dictionary containing dynamic configuration or state
                       parameters needed for event handling, such as:
                       - "current_screen_width" (int)
                       - "current_screen_height" (int)
                       - "win_screen_buttons" (dict): Rects for win screen buttons.
                       - "pause_screen_buttons" (dict): Rects for pause menu buttons.

    Returns:
        A string indicating the outcome or requested action:
            - "QUIT_APP": If a quit event is detected.
            - "VIDEO_RESIZE": If a window resize event occurs.
            - "GAME_PAUSED": If the pause button is clicked.
            - "GAME_RESUMED": If the resume button (in pause menu) is clicked.
            - "RESTART_SAME": If a "retry same level" button is clicked.
            - "MAIN_MENU": If a "quit to menu" or "new game" button is clicked.
            - "CAPTURE_VIEW_REQUESTED": If capture button is clicked.
            - "POST_TO_X_REQUESTED": If "Post to X" button is clicked.
            - "CONTINUE": If no state-changing action is taken by this event batch.
    """
    current_screen_width = config_params.get(
        "current_screen_width", settings.screen.default_width
    )
    current_screen_height = config_params.get(
        "current_screen_height", settings.screen.default_height
    )

    # Retrieve the dynamically drawn pause button rect from game_session
    # Fallback to config if not found, though it should always be there if drawn by main.py
    pause_button_rect = game_session.ui_rects.get('pause_button')
    if not pause_button_rect:
        # Fallback to static config if not available dynamically
        # This is a safety measure; ideally, it's always passed from where it's drawn.
        pause_cfg = settings.game_ui.pause_button
        pause_button_rect = pygame.Rect(pause_cfg.x, pause_cfg.y, pause_cfg.width, pause_cfg.height)


    win_screen_buttons = config_params.get("win_screen_buttons", {})
    pause_screen_buttons = config_params.get("pause_screen_buttons", {})

    # m_down state should be managed locally within this function's scope or passed if needed across calls.
    # For now, let's assume it's managed per call or this function is called frequently enough.
    # If drag state needs to persist across calls not containing MOUSEMOTION, it should be in GameSession.
    # For simplicity here, m_down will be local to this function's call frame.
    # This might mean drag operations must initiate with MOUSEBUTTONDOWN and continue with MOUSEMOTION in the same `events` batch.
    # A more robust solution would store m_down and selected_vertex_for_drag in GameSession.
    # For now, we use game_session.selected_vertex to infer selection state.

    # Local state for dragging, if not moved to GameSession
    # This implies that `handle_game_events` is called once per frame with all events for that frame.
    # If `m_down` needs to persist across frames where no MOUSEBUTTONDOWN/UP occurs, it must be in GameSession.
    # For this refactoring, let's assume game_session.selected_vertex existing means a drag *could* happen.
    # `m_down` will be a local variable that's set by MOUSEBUTTONDOWN and cleared by MOUSEBUTTONUP within this event batch.

    m_down_local = False # Local to this specific call of handle_game_events
    # If game_session.selected_vertex is already set from a previous call,
    # and a MOUSEBUTTONDOWN event occurs, it might be a new click, not start of drag.
    # True drag state (m_down) will be determined by MOUSEBUTTONDOWN events.

    vertex_radius_val = settings.vertex.radius

    for event in events:
        if event.type == pygame.QUIT:
            return "QUIT_APP"

        if event.type == pygame.VIDEORESIZE:
            # This part is now handled by main.py calling game_session.update_screen_dimensions
            # We still need to return "VIDEO_RESIZE" so main.py can update its screen object etc.
            # The actual resizing of graph elements is now encapsulated in GameSession.
            # config_params["current_screen_width"] = event.w # main.py will update this
            # config_params["current_screen_height"] = event.h
            if game_session and game_session.graph:
                 # game_session.update_screen_dimensions(event.w, event.h) # Called by main.py
                 pass # Graph update is handled by GameSession method called from main
            return "VIDEO_RESIZE"

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # LEFT CLICK for all primary interactions
                mx, my = event.pos

                if game_session.paused:
                    resume_rect = game_session.ui_rects.get('pause_menu_resume')
                    reset_rect = game_session.ui_rects.get('pause_menu_reset_level')
                    quit_rect = game_session.ui_rects.get('pause_menu_quit_to_menu')

                    if resume_rect and resume_rect.collidepoint(mx, my):
                        game_session.toggle_pause()
                        return "GAME_RESUMED"
                    elif reset_rect and reset_rect.collidepoint(mx, my):
                        return "RESTART_SAME"
                    elif quit_rect and quit_rect.collidepoint(mx, my):
                        return "MAIN_MENU"
                    # If no pause menu button is clicked, do nothing more for this event.

                elif game_session.is_won:
                    new_game_rect = game_session.ui_rects.get('win_screen_new_game')
                    retry_rect = game_session.ui_rects.get('win_screen_retry_same_level')
                    capture_rect = game_session.ui_rects.get('win_screen_capture_view')
                    post_x_rect = game_session.ui_rects.get('win_screen_post_to_x')

                    if new_game_rect and new_game_rect.collidepoint(mx, my):
                        return "MAIN_MENU"
                    elif retry_rect and retry_rect.collidepoint(mx, my):
                        return "RESTART_SAME"
                    elif capture_rect and capture_rect.collidepoint(mx, my):
                        return "CAPTURE_VIEW_REQUESTED"
                    elif post_x_rect and post_x_rect.collidepoint(mx, my):
                        return "POST_TO_X_REQUESTED"
                    # If no win screen button is clicked, do nothing more for this event.

                else:  # Active game state (not paused, not won)
                    # 1. Check Pause Button first
                    if pause_button_rect and pause_button_rect.collidepoint(mx, my):
                        game_session.toggle_pause()
                        return "GAME_PAUSED" # The new state is paused
                    else:
                        # 2. If Pause button not clicked, then handle vertex selection
                        m_down_local = True
                        found_vertex = game_session.graph.find_vertex_at_pos((mx, my), vertex_radius_val)
                        game_session.select_vertex(found_vertex)

            # elif event.button == 3: # RIGHT CLICK - currently no actions assigned for right click in this new scheme

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                m_down_local = False # Mouse button is now up for this event batch
                # Deselection on mouse up is implicit if no vertex is clicked on MOUSEBUTTONDOWN.
                # If a vertex was selected and dragged, it remains selected until a new click.
                # The old logic of deselecting on any mouse up might not be desired.
                # For now, if a vertex was selected, let it remain selected.
                # The win condition check is usually done in main loop after updates.
                # game_session.deselect_vertex() # Reconsider if this should always happen on mouse up

        elif event.type == pygame.MOUSEMOTION:
            if m_down_local and game_session.selected_vertex and \
               not game_session.paused and not game_session.is_won:
                mx, my = event.pos
                # Clamp motion to screen bounds (minus radius for aesthetics or to keep center on screen)
                # The clamping logic might be better inside GameSession.move_selected_vertex
                clamped_mx = max(
                    vertex_radius_val, min(mx, current_screen_width - vertex_radius_val)
                )
                clamped_my = max(
                    vertex_radius_val, min(my, current_screen_height - vertex_radius_val)
                )
                game_session.move_selected_vertex(clamped_mx, clamped_my)
                # After moving, the main loop should call game_session.check_win_condition()
    return "CONTINUE"
