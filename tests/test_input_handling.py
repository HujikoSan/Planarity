"""Unit tests for input handling functions in input_handling.py."""

import pygame
import pytest
from unittest import mock

# Module to test
from input_handling import handle_input_screen_logic, handle_game_events
from config import settings
from game_logic import GameSession  # For type hinting mock


# --- Fixtures ---
@pytest.fixture
def pygame_event_factory():
    """A factory fixture to create mock Pygame events."""
    def _create_mock_event(
        event_type, key=None, button=None, pos=None, unicode_char=None, w=None, h=None
    ):
        event = mock.Mock()
        event.type = event_type
        event.key = key
        event.button = button
        event.pos = pos
        event.unicode = unicode_char
        event.w = w
        event.h = h
        return event
    return _create_mock_event


@pytest.fixture
def default_input_screen_params():
    """Default parameters for handle_input_screen_logic."""
    return {
        "current_input_text": "",
        "text_box_is_active": False,
        "error_message": "",
        "current_screen_width": settings.screen.default_width,
        "current_screen_height": settings.screen.default_height,
    }


@pytest.fixture
def mock_game_session_obj():
    """Create a mock GameSession object."""
    session = mock.Mock(spec=GameSession)
    session.is_won = False
    session.paused = False
    session.temp_vertices_coords_hack = []
    session.temp_g_v_original_scaled_hack = []
    session.temp_sel_v_idx_hack = None
    session.temp_m_down_hack = False
    session.toggle_pause = mock.Mock()
    session.reset_game = mock.Mock()
    session.select_vertex = mock.Mock()
    session.deselect_vertex = mock.Mock()
    session.move_selected_vertex = mock.Mock()
    session.check_win_condition = mock.Mock(return_value=False)
    return session


@pytest.fixture
def default_game_config_params():
    """Default config_params for handle_game_events."""
    return {
        "current_screen_width": settings.screen.default_width,
        "current_screen_height": settings.screen.default_height,
        "win_screen_buttons": {},
        "pause_screen_buttons": {},
    }


# --- Tests for handle_input_screen_logic ---
def test_input_valid_number_start_button(pygame_event_factory, default_input_screen_params):
    params = default_input_screen_params.copy()
    params["current_input_text"] = str(settings.vertex.default_count)
    params["text_box_is_active"] = True

    mock_start_button_rect = mock.Mock(spec=pygame.Rect)
    mock_start_button_rect.collidepoint.return_value = True
    mock_text_box_rect = mock.Mock(spec=pygame.Rect)
    mock_text_box_rect.collidepoint.return_value = False
    mock_text_box_rect.centery = 300 # Default value for calculation

    with mock.patch('pygame.Rect', side_effect=[mock_text_box_rect, mock_start_button_rect]):
        event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=1, pos=(0,0))
        _, text_box_active, _, action = handle_input_screen_logic([event], **params)

    assert action == settings.vertex.default_count
    assert text_box_active is False

def test_input_valid_number_enter_key(pygame_event_factory, default_input_screen_params):
    params = default_input_screen_params.copy()
    params["current_input_text"] = str(settings.vertex.default_count)
    params["text_box_is_active"] = True

    event = pygame_event_factory(event_type=pygame.KEYDOWN, key=pygame.K_RETURN)
    _, _, _, action = handle_input_screen_logic([event], **params)

    assert action == settings.vertex.default_count

def test_input_invalid_number_too_low(pygame_event_factory, default_input_screen_params):
    params = default_input_screen_params.copy()
    params["current_input_text"] = str(settings.vertex.min_count - 1)
    params["text_box_is_active"] = True

    mock_start_button_rect = mock.Mock(spec=pygame.Rect)
    mock_start_button_rect.collidepoint.return_value = True
    mock_text_box_rect = mock.Mock(spec=pygame.Rect)
    mock_text_box_rect.collidepoint.return_value = False
    mock_text_box_rect.centery = 300 # Default value

    with mock.patch('pygame.Rect', side_effect=[mock_text_box_rect, mock_start_button_rect]):
        event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=1, pos=(0,0))
        _, _, error_msg, action = handle_input_screen_logic([event], **params)

    assert action is None
    assert f"Range: {settings.vertex.min_count}-{settings.vertex.max_count}" in error_msg

def test_input_invalid_number_too_high(pygame_event_factory, default_input_screen_params):
    params = default_input_screen_params.copy()
    params["current_input_text"] = str(settings.vertex.max_count + 1)
    params["text_box_is_active"] = True

    mock_start_button_rect = mock.Mock(spec=pygame.Rect)
    mock_start_button_rect.collidepoint.return_value = True
    mock_text_box_rect = mock.Mock(spec=pygame.Rect)
    mock_text_box_rect.collidepoint.return_value = False
    mock_text_box_rect.centery = 300 # Default value

    with mock.patch('pygame.Rect', side_effect=[mock_text_box_rect, mock_start_button_rect]):
        event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=1, pos=(0,0))
        _, _, error_msg, action = handle_input_screen_logic([event], **params)

    assert action is None
    assert f"Range: {settings.vertex.min_count}-{settings.vertex.max_count}" in error_msg

def test_input_non_numeric_start_button(pygame_event_factory, default_input_screen_params): # Renamed for clarity
    params = default_input_screen_params.copy()
    params["current_input_text"] = "abc"
    params["text_box_is_active"] = True

    mock_start_button_rect = mock.Mock(spec=pygame.Rect)
    mock_start_button_rect.collidepoint.return_value = True
    mock_text_box_rect = mock.Mock(spec=pygame.Rect)
    mock_text_box_rect.collidepoint.return_value = False
    mock_text_box_rect.centery = 300 # Default value

    with mock.patch('pygame.Rect', side_effect=[mock_text_box_rect, mock_start_button_rect]):
        event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=1, pos=(0,0))
        _, _, error_msg, action = handle_input_screen_logic([event], **params)

    assert action is None
    assert "Invalid number!" in error_msg

def test_input_non_numeric_enter_key(pygame_event_factory, default_input_screen_params): # New test
    """Test non-numeric input and pressing Enter."""
    params = default_input_screen_params.copy()
    params["current_input_text"] = "abc"
    params["text_box_is_active"] = True

    event = pygame_event_factory(event_type=pygame.KEYDOWN, key=pygame.K_RETURN)
    _, _, error_msg, action = handle_input_screen_logic([event], **params)

    assert action is None
    assert "Invalid number!" in error_msg


def test_input_empty_start(pygame_event_factory, default_input_screen_params):
    params = default_input_screen_params.copy()
    params["current_input_text"] = ""
    params["text_box_is_active"] = True

    mock_start_button_rect = mock.Mock(spec=pygame.Rect)
    mock_start_button_rect.collidepoint.return_value = True
    mock_text_box_rect = mock.Mock(spec=pygame.Rect)
    mock_text_box_rect.collidepoint.return_value = False
    mock_text_box_rect.centery = 300 # Default value

    with mock.patch('pygame.Rect', side_effect=[mock_text_box_rect, mock_start_button_rect]):
        event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=1, pos=(0,0))
        _, _, error_msg, action = handle_input_screen_logic([event], **params)

    assert action is None
    assert "Input is empty!" in error_msg

def test_input_box_activation(pygame_event_factory, default_input_screen_params):
    params = default_input_screen_params.copy()

    mock_text_box_rect = mock.Mock(spec=pygame.Rect)
    mock_text_box_rect.collidepoint.return_value = True
    mock_text_box_rect.centery = 300 # Default value
    mock_start_button_rect = mock.Mock(spec=pygame.Rect)
    mock_start_button_rect.collidepoint.return_value = False

    with mock.patch('pygame.Rect', side_effect=[mock_text_box_rect, mock_start_button_rect]):
        event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=1, pos=(0,0))
        _, text_box_active, _, _ = handle_input_screen_logic([event], **params)

    assert text_box_active is True

def test_input_box_deactivation(pygame_event_factory, default_input_screen_params):
    params = default_input_screen_params.copy()
    params["text_box_is_active"] = True

    mock_text_box_rect = mock.Mock(spec=pygame.Rect)
    mock_text_box_rect.collidepoint.return_value = False
    mock_text_box_rect.centery = 300 # Default value
    mock_start_button_rect = mock.Mock(spec=pygame.Rect)
    mock_start_button_rect.collidepoint.return_value = False

    with mock.patch('pygame.Rect', side_effect=[mock_text_box_rect, mock_start_button_rect]):
        event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=1, pos=(0,0))
        _, text_box_active, _, _ = handle_input_screen_logic([event], **params)

    assert text_box_active is False

def test_input_digit_entry(pygame_event_factory, default_input_screen_params):
    params = default_input_screen_params.copy()
    params["text_box_is_active"] = True
    params["current_input_text"] = "1"

    event = pygame_event_factory(event_type=pygame.KEYDOWN, key=pygame.K_2, unicode_char="2")
    input_text, _, _, _ = handle_input_screen_logic([event], **params)
    assert input_text == "12"

def test_input_non_digit_entry_shows_error(pygame_event_factory, default_input_screen_params): # Renamed & modified
    """Test entering a non-digit character shows error and does not change text."""
    params = default_input_screen_params.copy()
    params["text_box_is_active"] = True
    initial_text = "12"
    params["current_input_text"] = initial_text

    # Using K_a and unicode 'a' for a clear non-digit, non-functional key
    event = pygame_event_factory(event_type=pygame.KEYDOWN, key=pygame.K_a, unicode_char="a")
    input_text, _, error_msg, _ = handle_input_screen_logic([event], **params)

    assert input_text == initial_text # Text should not change
    assert "Only digits allowed." in error_msg # Error message should be set

def test_input_backspace(pygame_event_factory, default_input_screen_params):
    params = default_input_screen_params.copy()
    params["text_box_is_active"] = True
    params["current_input_text"] = "123"

    event = pygame_event_factory(event_type=pygame.KEYDOWN, key=pygame.K_BACKSPACE)
    input_text, _, _, _ = handle_input_screen_logic([event], **params)
    assert input_text == "12"

def test_input_quit_event(pygame_event_factory, default_input_screen_params):
    params = default_input_screen_params.copy()
    event = pygame_event_factory(event_type=pygame.QUIT)
    _, _, _, action = handle_input_screen_logic([event], **params)
    assert action == "QUIT_APP"


# --- Tests for handle_game_events ---
# (These tests remain unchanged from the previous step)

def test_game_quit_event(pygame_event_factory, mock_game_session_obj, default_game_config_params):
    event = pygame_event_factory(event_type=pygame.QUIT)
    status = handle_game_events([event], mock_game_session_obj, default_game_config_params)
    assert status == "QUIT_APP"

def test_game_resize_event(pygame_event_factory, mock_game_session_obj, default_game_config_params):
    params = default_game_config_params.copy()
    new_width, new_height = 1024, 768
    mock_game_session_obj.temp_g_v_original_scaled_hack = [(0.1, 0.1), (0.5, 0.5)]
    mock_game_session_obj.temp_vertices_coords_hack = [(10, 10), (50, 50)]
    event = pygame_event_factory(event_type=pygame.VIDEORESIZE, w=new_width, h=new_height)
    status = handle_game_events([event], mock_game_session_obj, params)
    assert status == "VIDEO_RESIZE"
    assert params["current_screen_width"] == new_width
    assert params["current_screen_height"] == new_height
    assert mock_game_session_obj.temp_vertices_coords_hack[0] == (0.1 * new_width, 0.1 * new_height)
    assert mock_game_session_obj.temp_vertices_coords_hack[1] == (0.5 * new_width, 0.5 * new_height)

def test_game_mouse_down_select_vertex(pygame_event_factory, mock_game_session_obj, default_game_config_params):
    mock_game_session_obj.temp_vertices_coords_hack = [(100.0, 100.0), (200.0, 200.0)]
    click_pos = (105, 105)
    event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=1, pos=click_pos)
    status = handle_game_events([event], mock_game_session_obj, default_game_config_params)
    assert status == "CONTINUE"
    assert mock_game_session_obj.temp_m_down_hack is True
    assert mock_game_session_obj.temp_sel_v_idx_hack == 0

    mock_game_session_obj.temp_sel_v_idx_hack = None
    click_pos_away = (5, 5)
    event_away = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=1, pos=click_pos_away)
    status = handle_game_events([event_away], mock_game_session_obj, default_game_config_params)
    assert mock_game_session_obj.temp_sel_v_idx_hack is None

def test_game_mouse_motion_drag_vertex(pygame_event_factory, mock_game_session_obj, default_game_config_params):
    mock_game_session_obj.temp_sel_v_idx_hack = 0
    mock_game_session_obj.temp_m_down_hack = True
    mock_game_session_obj.temp_vertices_coords_hack = [(100.0, 100.0)]
    mock_game_session_obj.temp_g_v_original_scaled_hack = [(100.0 / 800, 100.0 / 600)]
    new_pos = (150, 150)
    event = pygame_event_factory(event_type=pygame.MOUSEMOTION, pos=new_pos)
    status = handle_game_events([event], mock_game_session_obj, default_game_config_params)
    assert status == "CONTINUE"
    assert mock_game_session_obj.temp_vertices_coords_hack[0] == new_pos
    assert mock_game_session_obj.temp_g_v_original_scaled_hack[0] == (
        new_pos[0] / default_game_config_params["current_screen_width"],
        new_pos[1] / default_game_config_params["current_screen_height"],
    )

def test_game_mouse_up_deselect_vertex(pygame_event_factory, mock_game_session_obj, default_game_config_params):
    mock_game_session_obj.temp_m_down_hack = True
    mock_game_session_obj.temp_sel_v_idx_hack = 0
    event = pygame_event_factory(event_type=pygame.MOUSEBUTTONUP, button=1)
    status = handle_game_events([event], mock_game_session_obj, default_game_config_params)
    assert status == "CONTINUE"
    assert mock_game_session_obj.temp_m_down_hack is False
    assert mock_game_session_obj.temp_sel_v_idx_hack is None

def test_game_pause_button_click_and_resume(pygame_event_factory, mock_game_session_obj, default_game_config_params):
    params = default_game_config_params.copy()
    pause_btn_cfg = settings.game_ui.pause_button
    event_pause = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=3, pos=(pause_btn_cfg.x + 5, pause_btn_cfg.y + 5))
    status = handle_game_events([event_pause], mock_game_session_obj, params)
    assert status == "GAME_PAUSED"
    assert mock_game_session_obj.paused is True

    mock_game_session_obj.paused = True
    resume_button_mock_rect = mock.Mock(spec=pygame.Rect)
    resume_button_mock_rect.collidepoint.return_value = True
    params["pause_screen_buttons"] = {"resume_button_rect": resume_button_mock_rect}
    event_resume = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=3, pos=(0,0))
    status = handle_game_events([event_resume], mock_game_session_obj, params)
    assert status == "GAME_RESUMED"
    assert mock_game_session_obj.paused is False

def test_game_reset_button_click_when_paused(pygame_event_factory, mock_game_session_obj, default_game_config_params):
    params = default_game_config_params.copy()
    mock_game_session_obj.paused = True
    reset_button_mock_rect = mock.Mock(spec=pygame.Rect)
    reset_button_mock_rect.collidepoint.return_value = True
    params["pause_screen_buttons"] = {"reset_button_rect": reset_button_mock_rect}
    event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=3, pos=(0,0))
    status = handle_game_events([event], mock_game_session_obj, params)
    assert status == "RESTART_SAME"

def test_game_quit_to_menu_button_click_when_paused(pygame_event_factory, mock_game_session_obj, default_game_config_params):
    params = default_game_config_params.copy()
    mock_game_session_obj.paused = True
    quit_button_mock_rect = mock.Mock(spec=pygame.Rect)
    quit_button_mock_rect.collidepoint.return_value = True
    params["pause_screen_buttons"] = {"quit_button_rect": quit_button_mock_rect}
    event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=3, pos=(0,0))
    status = handle_game_events([event], mock_game_session_obj, params)
    assert status == "MAIN_MENU"

def test_game_win_screen_new_game_button(pygame_event_factory, mock_game_session_obj, default_game_config_params):
    params = default_game_config_params.copy()
    mock_game_session_obj.is_won = True
    new_game_button_mock_rect = mock.Mock(spec=pygame.Rect)
    new_game_button_mock_rect.collidepoint.return_value = True
    params["win_screen_buttons"] = {"new_game_button_rect": new_game_button_mock_rect}
    event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=3, pos=(0,0))
    status = handle_game_events([event], mock_game_session_obj, params)
    assert status == "MAIN_MENU"

def test_game_win_screen_retry_button(pygame_event_factory, mock_game_session_obj, default_game_config_params):
    params = default_game_config_params.copy()
    mock_game_session_obj.is_won = True
    retry_button_mock_rect = mock.Mock(spec=pygame.Rect)
    retry_button_mock_rect.collidepoint.return_value = True
    params["win_screen_buttons"] = {"retry_same_button_rect": retry_button_mock_rect}
    event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=3, pos=(0,0))
    status = handle_game_events([event], mock_game_session_obj, params)
    assert status == "RESTART_SAME"

@mock.patch('input_handling.webbrowser.open_new_tab')
def test_game_post_to_x_button(mock_open_new_tab, pygame_event_factory, mock_game_session_obj, default_game_config_params):
    params = default_game_config_params.copy()
    mock_game_session_obj.is_won = True
    post_x_button_mock_rect = mock.Mock(spec=pygame.Rect)
    post_x_button_mock_rect.collidepoint.return_value = True
    params["win_screen_buttons"] = {"post_to_x_button_rect": post_x_button_mock_rect}
    mock_game_session_obj.temp_n_v_sess_hack = 10
    mock_game_session_obj.temp_edges_hack = [0]*5
    mock_game_session_obj.temp_elap_s_hack = 123.45
    event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=3, pos=(0,0))
    status = handle_game_events([event], mock_game_session_obj, params)
    assert status == "POST_TO_X_REQUESTED"

def test_game_capture_button(pygame_event_factory, mock_game_session_obj, default_game_config_params):
    params = default_game_config_params.copy()
    mock_game_session_obj.is_won = True
    capture_button_mock_rect = mock.Mock(spec=pygame.Rect)
    capture_button_mock_rect.collidepoint.return_value = True
    params["win_screen_buttons"] = {"capture_button_rect": capture_button_mock_rect}
    event = pygame_event_factory(event_type=pygame.MOUSEBUTTONDOWN, button=3, pos=(0,0))
    status = handle_game_events([event], mock_game_session_obj, params)
    assert status == "CAPTURE_VIEW_REQUESTED"
