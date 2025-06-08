"""Main application file for the Planarity game.

This module initializes Pygame, loads configurations and fonts, and runs the
main game loop. It manages game states (e.g., input screen, in-game) and
delegates event handling and drawing operations to respective modules
(`input_handling.py`, `drawing.py`). It also includes placeholder logic
for graph generation and game session management, which are intended to be
further refactored into the `game_logic` module.
"""

import pygame
import sys
import time
import enum  # For GameState
import random  # For HACK graph generation
import webbrowser  # For "Post to X" functionality
import urllib.parse  # For "Post to X" functionality

# Project modules
from game_logic import GameSession, Graph
import drawing
import input_handling
from config import settings  # Import the settings object


class GameState(enum.Enum):
    """Enumerates the possible states of the game application."""

    INPUT_SCREEN = 1  # State where the user inputs the number of vertices.
    IN_GAME = 2  # State where the main game is being played.


# --- Pygame Initialization and Font Setup ---
pygame.init()
pygame.font.init()

# Load fonts using sizes from config settings
try:
    TITLE_FONT = pygame.font.Font(None, settings.font_sizes.title)
    STATS_FONT = pygame.font.Font(None, settings.font_sizes.stats)
    UI_FONT = pygame.font.Font(None, settings.font_sizes.small_ui)
except Exception as e:
    print(f"Font loading failed: {e}. Using default Pygame font for all.")
    default_font_name = pygame.font.get_default_font()
    TITLE_FONT = pygame.font.Font(default_font_name, settings.font_sizes.title)
    STATS_FONT = pygame.font.Font(default_font_name, settings.font_sizes.stats)
    UI_FONT = pygame.font.Font(default_font_name, settings.font_sizes.small_ui)

# Fallback if any font is still None
if not TITLE_FONT:
    TITLE_FONT = pygame.font.Font(pygame.font.get_default_font(), 74)
if not STATS_FONT:
    STATS_FONT = pygame.font.Font(pygame.font.get_default_font(), 36)
if not UI_FONT:
    UI_FONT = pygame.font.Font(pygame.font.get_default_font(), 24)


def main_application():
    """Run the main application loop for the Planarity game.

    Initializes the game window, handles game state transitions,
    manages the main event loop, and calls appropriate functions for
    event processing, game logic updates, and drawing based on the
    current game state.
    """
    current_screen_width = settings.screen.default_width
    current_screen_height = settings.screen.default_height

    screen = pygame.display.set_mode(
        (current_screen_width, current_screen_height), pygame.RESIZABLE
    )
    pygame.display.set_caption(settings.game_title)
    drawing.set_screen(
        screen, current_screen_width, current_screen_height
    )  # Initialize global screen in drawing module

    clock = pygame.time.Clock()
    current_state = GameState.INPUT_SCREEN

    num_vertices_for_game = settings.vertex.default_count
    input_text = ""
    text_box_active = True
    error_message = ""

    game_session: Optional[GameSession] = None
    # current_button_rects = {} # This was planned but not yet fully utilized.
                              # Button rects are mostly handled within drawing/input functions.

    running = True
    while running:
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                current_screen_width = event.w
                current_screen_height = event.h
                screen = pygame.display.set_mode(
                    (current_screen_width, current_screen_height), pygame.RESIZABLE
                )
                drawing.set_screen(screen, current_screen_width, current_screen_height)

        if current_state == GameState.INPUT_SCREEN:
            (
                input_text,
                text_box_active,
                error_message,
                action,
            ) = input_handling.handle_input_screen_logic(
                events,
                input_text,
                text_box_active,
                error_message,
                current_screen_width,
                current_screen_height,
            )

            if isinstance(action, int):  # Number of vertices chosen
                num_vertices_for_game = action
                # temp_graph = Graph() # This is no longer needed as GameSession creates its own graph.

                # Create a new GameSession, which also creates and populates its own Graph
                game_session = GameSession(
                    num_vertices=num_vertices_for_game,
                    screen_width=current_screen_width,
                    screen_height=current_screen_height,
                )
                # No more HACK graph generation or attribute setting needed here.
                # GameSession constructor calls its reset_game, which calls graph.populate_random_planar.
                # temp_graph is no longer needed here as GameSession creates its own graph.

                current_state = GameState.IN_GAME
                input_text = ""
                error_message = ""
                text_box_active = False
            elif action == "QUIT_APP":
                running = False

            drawing.draw_input_screen(
                STATS_FONT,
                TITLE_FONT,
                input_text,
                error_message,
                text_box_active,
                current_screen_width,
                current_screen_height,
            )

        elif current_state == GameState.IN_GAME:
            if not game_session:  # Should ideally not happen
                current_state = GameState.INPUT_SCREEN
                continue

            # Prepare dynamic parameters for event handling (e.g., button rects)
            # TODO: Populate these from drawing module or game session state if UI is dynamic
            game_event_config = {
                "current_screen_width": current_screen_width,
                "current_screen_height": current_screen_height,
                # "win_screen_buttons": getattr(  # No longer used by input_handling for dynamic buttons
                #     game_session, "win_button_rects_hack", {}
                # ),
                # "pause_screen_buttons": getattr( # No longer used by input_handling for dynamic buttons
                #     game_session, "pause_button_rects_hack", {}
                # ),
            }
            game_status = input_handling.handle_game_events(
                events, game_session, game_event_config
            )

            if game_status == "QUIT_APP":
                running = False
            elif game_status == "MAIN_MENU":
                current_state = GameState.INPUT_SCREEN
                game_session = None
                text_box_active = True
            elif game_status == "RESTART_SAME":
                if game_session: # Should always be true here
                    game_session.reset_game() # num_vertices is stored in game_session
                # current_state remains IN_GAME
            elif game_status == "VIDEO_RESIZE":
                if game_session:
                    game_session.update_screen_dimensions(current_screen_width, current_screen_height)

            elif game_status == "CAPTURE_VIEW_REQUESTED":
                if game_session:
                    # capture_game_view now takes the Graph object
                    crossing_edges_for_capture = game_session.graph.find_crossing_edges()
                    drawing.capture_game_view(
                        current_screen_width, current_screen_height,
                        game_session.graph,
                        crossing_edges_for_capture,
                        game_session.elapsed_time
                    )
            elif game_status == "POST_TO_X_REQUESTED":
                if game_session:
                    tweet_text = (
                        f"Solved Planarity: {game_session.num_vertices}V, "
                        f"{len(game_session.graph.edges)}E, "
                        f"{game_session.elapsed_time:.1f}s! #PlanarityGame #{settings.game_title}"
                    )
                    webbrowser.open_new_tab(
                        f"https://x.com/intent/post?text={urllib.parse.quote(tweet_text)}"
                    )

            # Game Logic Updates & Win Condition Check
            if game_session and not game_session.paused:
                if not game_session.is_won: # Only update time and check win if not already won
                    game_session.update_elapsed_time()
                    # Win condition check is now more explicit after potential moves in handle_game_events
                    # or if a "check win" button were added.
                    # A simple check after every event batch if not paused/won:
                    game_session.check_win_condition()


            # Drawing game content
            screen.fill(settings.screen.background_color)
            if game_session:
                # draw_graph now takes the Graph object directly
                crossing_edges = game_session.graph.find_crossing_edges()
                drawing.draw_graph(
                    game_session.graph,
                    crossing_edges
                )

                # Draw UI elements (timer, messages, etc.)
                if not game_session.is_won and not game_session.paused:
                    time_surf = STATS_FONT.render(
                        f"Time: {game_session.elapsed_time:.1f}",
                        True,
                        settings.colors.black,
                    )
                    screen.blit(
                        time_surf, (settings.game_ui.timer.x, settings.game_ui.timer.y)
                    )
                    # Draw the pause button and store its rect for input handling
                    drawn_pause_button_rect = drawing.draw_pause_button(screen, STATS_FONT)
                    if game_session: # Should always be true here
                        game_session.ui_rects['pause_button'] = drawn_pause_button_rect


                if game_session.is_won:
                    win_surf = TITLE_FONT.render(
                        "You Win!", True, settings.colors.win_message
                    )
                    # TODO: Centralize UI layout logic, perhaps in drawing.py or a UI manager
                    win_rect_center_y = current_screen_height / 2 - 50 # Placeholder
                    if settings.game_ui.win_screen and settings.game_ui.win_screen.get("title_y_offset"):
                        win_rect_center_y = current_screen_height / 2 + settings.game_ui.win_screen.title_y_offset

                    win_rect = win_surf.get_rect(
                        center=(current_screen_width / 2, win_rect_center_y)
                    )
                    screen.blit(win_surf, win_rect)

                    # Prepare data for win screen elements
                    win_game_data = {
                        'num_vertices': game_session.graph.get_vertex_count(),
                        'num_edges': game_session.graph.get_edge_count(),
                        'elapsed_time': game_session.elapsed_time
                    }
                    # Draw win screen buttons and store their rects
                    # Assuming STATS_FONT for stats text and button text on win screen
                    drawn_win_button_rects = drawing.draw_win_screen_elements(
                        screen, TITLE_FONT, STATS_FONT, STATS_FONT, win_game_data
                    )
                    if game_session: # Should always be true
                        for btn_id, rect in drawn_win_button_rects.items():
                            game_session.ui_rects[f'win_screen_{btn_id}'] = rect

                if game_session.paused: # Use game_session.paused directly
                    drawing.draw_pause_menu_overlay(screen) # Use global screen from drawing module
                    # Assuming STATS_FONT is suitable for button text, TITLE_FONT for "Paused" title
                    # These fonts are loaded globally in main.py
                    drawn_pause_menu_button_rects = drawing.draw_pause_menu_elements(
                        screen, TITLE_FONT, STATS_FONT
                    )
                    if game_session: # Should always be true here
                        for btn_id, rect in drawn_pause_menu_button_rects.items():
                            game_session.ui_rects[f'pause_menu_{btn_id}'] = rect

            pygame.display.flip()

        clock.tick(settings.get("game_fps", 60)) # Use FPS from config or default to 60

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main_application()
