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

    pause_btn_cfg = settings.game_ui.pause_button
    pause_btn_r = pygame.Rect(
        pause_btn_cfg.x, pause_btn_cfg.y, pause_btn_cfg.width, pause_btn_cfg.height
    )

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
            mx, my = event.pos
            if event.button == 1:  # LEFT CLICK
                if not game_session.is_won and not game_session.paused:
                    m_down_local = True # Mouse button is now pressed for this event batch
                    found_vertex = game_session.graph.find_vertex_at_pos((mx, my), vertex_radius_val)
                    game_session.select_vertex(found_vertex) # Selects None if not found, deselecting
                    # No need to manage temp_m_down_hack or temp_sel_v_idx_hack on game_session

            elif event.button == 3:  # RIGHT CLICK
                is_paused = game_session.paused # Directly use GameSession attribute

                if not is_paused and not game_session.is_won:
                    if pause_btn_r.collidepoint(mx, my):
                        game_session.toggle_pause() # Use the new method
                        return "GAME_PAUSED" if game_session.paused else "GAME_RESUMED" # Status reflects actual state
                elif is_paused: # game_session.paused is True
                    if pause_screen_buttons.get(
                        "resume_button_rect", pygame.Rect(0, 0, 0, 0)
                    ).collidepoint(mx, my):
                        game_session.toggle_pause() # Use the new method
                        return "GAME_RESUMED"
                    elif pause_screen_buttons.get(
                        "reset_button_rect", pygame.Rect(0, 0, 0, 0) # Rects are passed in config_params
                    ).collidepoint(mx, my):
                        return "RESTART_SAME"
                    elif pause_screen_buttons.get(
                        "quit_button_rect", pygame.Rect(0, 0, 0, 0)
                    ).collidepoint(mx, my):
                        return "MAIN_MENU"
                elif game_session.is_won:
                    if win_screen_buttons.get(
                        "new_game_button_rect", pygame.Rect(0, 0, 0, 0)
                    ).collidepoint(mx, my):
                        return "MAIN_MENU"
                    elif win_screen_buttons.get(
                        "retry_same_button_rect", pygame.Rect(0, 0, 0, 0)
                    ).collidepoint(mx, my):
                        return "RESTART_SAME"
                    elif win_screen_buttons.get(
                        "capture_button_rect", pygame.Rect(0, 0, 0, 0)
                    ).collidepoint(mx, my):
                        return "CAPTURE_VIEW_REQUESTED"
                    elif win_screen_buttons.get(
                        "post_to_x_button_rect", pygame.Rect(0, 0, 0, 0)
                    ).collidepoint(mx, my):
                        return "POST_TO_X_REQUESTED"

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
