import unittest
from datetime import datetime, timedelta
from google.cloud import firestore
from runo import *

db = firestore.Client()

TEST_GAME_FILE_PATH = 'games_test'
TEST_MAX_GAMES_PER_DAY = 5


class GameTestCase(unittest.TestCase):
    def setUp(self):
        set_GAME_FILE_PATH(TEST_GAME_FILE_PATH)
        set_MAX_GAMES_PER_DAY(TEST_MAX_GAMES_PER_DAY)

    def tearDown(self):
        game_files = db.collection(TEST_GAME_FILE_PATH).get()
        for game_file in game_files:
            game_file.reference.delete()

    def test_can_create_new_game(self):
        for __ in range(TEST_MAX_GAMES_PER_DAY):
            # Ensure that the game was created successfully
            self.assertTrue(save_state(create_new_game('MyGame', 'PlayerOne')))
        # Ensure that the game failed to be created
        self.assertFalse(create_new_game('MyGame', 'PlayerOne'))

    def test_house_keeping(self):
        day_ago = serialize_datetime(datetime.utcnow() - timedelta(days=1))
        for __ in range(TEST_MAX_GAMES_PER_DAY):
            game_data = create_new_game('MyGame', 'PlayerOne')
            # Ensure that the game was created successfully
            self.assertTrue(game_data)
            # Mock the created_at datetime to be a day old
            game_data['created_at'] = day_ago
            # Ensure that the game was able to be saved
            self.assertTrue(save_state(game_data))
        # Ensure that the game was created successfully, due to
        # successful house-keeping
        self.assertTrue(create_new_game('MyGame', 'PlayerOne'))

    def test_create_new_game(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        self.assertIsNotNone(game_data)

    def test_create_new_game_low_min_players(self):
        game_data = create_new_game('MyGame', 'PlayerOne', min_players=1)
        self.assertEqual(game_data['min_players'], 2)

    def test_create_new_game_high_max_players(self):
        game_data = create_new_game('MyGame', 'PlayerOne', max_players=11)
        self.assertEqual(game_data['max_players'], 10)

    def test_create_new_game_defaults(self):
        game_data = create_new_game('', '', points_to_win='', min_players='',
                                    max_players='')
        self.assertIn(DEFAULT_GAME_NAME, game_data['name'])
        self.assertIn(DEFAULT_PLAYER_NAME, game_data['players'][0]['name'])
        self.assertEqual(game_data['points_to_win'],
                         POINTS_TO_WIN)
        self.assertEqual(game_data['min_players'],
                         MIN_PLAYERS)
        self.assertEqual(game_data['max_players'],
                         MAX_PLAYERS)
        game_data = create_new_game(None, None, points_to_win=None,
                                    min_players=None, max_players=None)
        self.assertIn(DEFAULT_GAME_NAME, game_data['name'])
        self.assertIn(DEFAULT_PLAYER_NAME, game_data['players'][0]['name'])
        self.assertEqual(game_data['points_to_win'],
                         POINTS_TO_WIN)
        self.assertEqual(game_data['min_players'],
                         MIN_PLAYERS)
        self.assertEqual(game_data['max_players'],
                         MAX_PLAYERS)

    def test_save_state(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        result = save_state(game_data)
        self.assertTrue(result)

    def test_load_state(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        game_data = load_state(game_data['id'])
        self.assertNotEqual(game_data, {})

    def test_get_open_games_one_game_available(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        save_state(game_data)
        open_games = get_open_games()
        # Ensure that there is only one open game
        self.assertEqual(len(open_games), 1)
        # Ensure that MyGame is the one that's in the list
        self.assertIn(game_data, open_games)

    def test_get_open_games_two_games_available(self):
        game_one = create_new_game('GameOne', 'PlayerOne')
        save_state(game_one)
        game_two = create_new_game('GameTwo', 'PlayerOne')
        save_state(game_two)
        open_games = get_open_games()
        # Ensure that there are two open games
        self.assertEqual(len(open_games), 2)
        # Ensure that the previously-created games are in the list
        self.assertIn(game_one, open_games)
        self.assertIn(game_two, open_games)

    def test_get_open_games_two_games_but_one_already_started(self):
        game_one = create_new_game('GameOne', 'PlayerOne')
        save_state(game_one)
        game_two = create_new_game('GameTwo', 'PlayerOne')
        add_player_to_game(game_two, 'PlayerTwo')
        # Start GameTwo
        start_game(game_two)
        save_state(game_two)
        open_games = get_open_games()
        # Ensure that there is only one open game
        self.assertEqual(len(open_games), 1)
        # Ensure that GameOne is the one that's in the list
        self.assertIn(game_one, open_games)

    def test_get_open_games_two_games_but_one_already_ended(self):
        game_one = create_new_game('GameOne', 'PlayerOne')
        save_state(game_one)
        game_two = create_new_game('GameTwo', 'PlayerOne')
        # End GameTwo
        game_two['ended_at'] = 'sometime'
        save_state(game_two)
        open_games = get_open_games()
        # Ensure that there is only one open game
        self.assertEqual(len(open_games), 1)
        # Ensure that GameOne is the one that's in the list
        self.assertIn(game_one, open_games)

    def test_get_open_games_two_games_but_both_already_ended(self):
        game_one = create_new_game('GameOne', 'PlayerOne')
        # End GameOne
        game_one['ended_at'] = 'sometime'
        save_state(game_one)
        game_two = create_new_game('GameTwo', 'PlayerOne')
        # End GameTwo
        game_two['ended_at'] = 'sometime'
        save_state(game_two)
        open_games = get_open_games()
        # Ensure that there are no games
        self.assertEqual(open_games, [])

    def test_get_open_games_when_there_are_no_games(self):
        open_games = get_open_games()
        # Ensure that there are no games
        self.assertEqual(open_games, [])

    def test_new_game_deck_has_108_cards(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        self.assertEqual(len(game_data['deck']), 108)

    def test_new_game_is_not_active(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        self.assertFalse(game_data['active'])

    def test_new_game_is_not_reversed(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        self.assertFalse(game_data['reverse'])

    def test_new_game_created_at(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        self.assertIsNotNone(game_data['created_at'])

    def test_started_at_is_none_before_game_starts(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        self.assertIsNone(game_data['started_at'])

    def test_started_at_is_not_none_after_game_starts(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        self.assertIsNotNone(game_data['started_at'])

    def test_stack_has_no_cards_before_game_starts(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        self.assertEqual(len(game_data['stack']), 0)

    def test_stack_has_one_card_after_game_starts(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        self.assertEqual(len(game_data['stack']), 1)

    def test_player_that_creates_game_is_admin_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        self.assertTrue(game_data['players'][0]['admin'])

    def test_add_player_to_game(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        player = add_player_to_game(game_data, 'PlayerTwo')
        self.assertIsNotNone(player)
        self.assertEqual(len(game_data['players']), 2)

    def test_add_player_to_game_fails_when_max_players_reached(self):
        game_data = create_new_game('MyGame', 'PlayerOne', max_players=2)
        player2 = add_player_to_game(game_data, 'PlayerTwo')
        self.assertIsNotNone(player2)
        player3 = add_player_to_game(game_data, 'PlayerThree')
        self.assertIsNone(player3)
        self.assertEqual(len(game_data['players']), 2)

    def test_add_player_to_game_generates_ux_id(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        save_state(game_data)
        game_data = load_state(game_data['id'])
        for player in game_data['players']:
            self.assertEqual(len(player['ux_id']), PLAYER_UX_ID_LENGTH)

    def test_each_player_has_seven_cards_after_game_starts(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        start_game(game_data)
        for player in game_data['players']:
            self.assertEqual(len(player['hand']), 7)

    def test_no_player_is_active_before_game_starts(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        for player in game_data['players']:
            self.assertFalse(player['active'])

    def test_admin_player_is_active_after_game_starts(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        start_game(game_data)
        admin_player = [p for p in game_data['players'] if p['admin']][0]
        self.assertTrue(admin_player['active'])

    def test_get_state(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        game_id = game_data['id']
        player_id = game_data['players'][0]['id']
        result = get_state(game_id, player_id)
        # Check that result is not empty
        self.assertTrue(result)

    def test_get_state_returns_empty_when_game_id_not_valid(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        player_id = game_data['players'][0]['id']
        result = get_state('bad_game_id', player_id)
        self.assertEqual(result, {})

    def test_get_state_returns_empty_when_player_id_not_valid(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        game_id = game_data['id']
        result = get_state(game_id, 'bad_player_id')
        self.assertEqual(result, {})

    def test_get_state_masks_id_of_other_players(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        save_state(game_data)
        game_id = game_data['id']
        player_one_id = game_data['players'][0]['id']
        result = get_state(game_id, player_one_id)
        self.assertEqual(result['players'][0]['id'], player_one_id)
        self.assertIsNone(result['players'][1]['id'])

    def test_get_state_masks_hand_of_other_players(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        save_state(game_data)
        game_id = game_data['id']
        player_one_id = game_data['players'][0]['id']
        result = get_state(game_id, player_one_id)
        self.assertIn('hand', result['players'][0])
        for card in result['players'][0]['hand']:
            self.assertIn(card, game_data['players'][0]['hand'])
        self.assertNotIn('hand', result['players'][1])

    def test_get_state_returns_draw_required_for_active_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        save_state(game_data)
        game_id = game_data['id']
        player_id = game_data['players'][0]['id']
        game_data = get_state(game_id, player_id)
        # Ensure that the "draw_required" key exists in PlayerOne's dict
        self.assertIn('draw_required', game_data['players'][0])

    def test_get_state_sets_draw_required_for_active_player_if_needed(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Initialize PlayerOne's hand to have only one card
        game_data['players'][0]['hand'] = [create_card('4', 'RED')]
        # Initialize top of discard pile to a not matching card
        game_data['stack'][-1] = create_card('5', 'BLUE')
        save_state(game_data)
        game_id = game_data['id']
        player_id = game_data['players'][0]['id']
        game_data = get_state(game_id, player_id)
        # Ensure that the "draw_required" key exists in PlayerOne's dict
        self.assertIn('draw_required', game_data['players'][0])
        # Ensure that "draw_required" is set to true
        self.assertTrue(game_data['players'][0]['draw_required'])

    def test_get_state_no_draw_required_for_inactive_players(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        player_two = add_player_to_game(game_data, 'PlayerTwo')
        player_three = add_player_to_game(game_data, 'PlayerThree')
        start_game(game_data)
        save_state(game_data)
        game_id = game_data['id']
        # Ensure that "draw_required" key does not exist in PlayerTwo's dict
        game_data = get_state(game_id, player_two['id'])
        self.assertNotIn('draw_required', game_data['players'][1])
        # Ensure that "draw_required" key does not exist in PlayerThree's dict
        game_data = get_state(game_id, player_three['id'])
        self.assertNotIn('draw_required', game_data['players'][2])

    def test_get_active_player_returns_none_before_game_starts(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        result = get_active_player(game_data)
        self.assertIsNone(result)

    def test_get_active_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])

    def test_activate_next_player_fails_before_game_starts(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        with self.assertRaises(TypeError):
            activate_next_player(game_data)

    def test_activate_next_player_succeeds_even_if_only_one_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        current_player = get_active_player(game_data)
        activate_next_player(game_data)
        next_player = get_active_player(game_data)
        self.assertEqual(current_player, next_player)

    def test_activate_next_player_cycle_two_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Ensure top of stack isn't a REVERSE or SKIP card
        game_data['stack'][-1]['value'] = 0
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])
        activate_next_player(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][1])
        activate_next_player(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])

    def test_activate_next_player_cycle_two_player_reverse(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        game_data['reverse'] = True
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Ensure top of stack isn't a REVERSE or SKIP card
        game_data['stack'][-1]['value'] = 0
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])
        activate_next_player(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][1])
        activate_next_player(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])

    def test_activate_next_player_cycle_multi_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        add_player_to_game(game_data, 'PlayerFour')
        start_game(game_data)
        # Ensure top of stack isn't a SKIP card
        game_data['stack'][-1]['value'] = 0
        for i in range(0, 4):
            active_player = get_active_player(game_data)
            self.assertEqual(active_player, game_data['players'][i])
            activate_next_player(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])

    def test_activate_next_player_cycle_multi_player_reverse(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        game_data['reverse'] = True
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        add_player_to_game(game_data, 'PlayerFour')
        start_game(game_data)
        # Ensure top of stack isn't a SKIP card
        game_data['stack'][-1]['value'] = 0
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])
        for i in range(3, -1, -1):
            activate_next_player(game_data)
            active_player = get_active_player(game_data)
            self.assertEqual(active_player, game_data['players'][i])

    def test_activate_next_player_with_reverse_card_two_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Set the top of stack to a REVERSE card
        game_data['stack'][-1]['value'] = 'REVERSE'
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])
        activate_next_player(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])

    def test_activate_next_player_with_skip_card_two_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Set the top of stack to a SKIP card
        game_data['stack'][-1]['value'] = 'SKIP'
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])
        activate_next_player(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])

    def test_activate_next_player_with_skip_card_two_player_reverse(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        game_data['reverse'] = True
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Set the top of stack to a SKIP card
        game_data['stack'][-1]['value'] = 'SKIP'
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])
        activate_next_player(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])

    def test_activate_next_player_with_skip_card_multi_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        add_player_to_game(game_data, 'PlayerFour')
        start_game(game_data)
        # Set the top of stack to a SKIP card
        game_data['stack'][-1]['value'] = 'SKIP'
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])
        activate_next_player(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][2])
        activate_next_player(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])

    def test_activate_next_player_with_skip_card_multi_player_reverse(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        game_data['reverse'] = True
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        add_player_to_game(game_data, 'PlayerFour')
        start_game(game_data)
        # Set the top of stack to a SKIP card
        game_data['stack'][-1]['value'] = 'SKIP'
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])
        activate_next_player(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][2])
        activate_next_player(game_data)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])

    def test_activate_next_player_draw_two_card_two_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Add a DRAW_TWO card to the stack
        game_data['stack'].append(create_card('DRAW_TWO', 'GREEN'))
        activate_next_player(game_data)
        affected_player = game_data['players'][1]
        self.assertEqual(len(affected_player['hand']), 9)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])

    def test_activate_next_player_draw_two_card_multi_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        start_game(game_data)
        # Add a DRAW_TWO card to the stack
        game_data['stack'].append(create_card('DRAW_TWO', 'GREEN'))
        activate_next_player(game_data)
        affected_player = game_data['players'][1]
        self.assertEqual(len(affected_player['hand']), 9)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][2])

    def test_activate_next_player_draw_four_card_two_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Add a WILD_DRAW_FOUR card to the stack
        game_data['stack'].append(create_card('WILD_DRAW_FOUR'))
        activate_next_player(game_data)
        affected_player = game_data['players'][1]
        self.assertEqual(len(affected_player['hand']), 11)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][0])

    def test_activate_next_player_draw_four_card_multi_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        start_game(game_data)
        # Add a WILD_DRAW_FOUR card to the stack
        game_data['stack'].append(create_card('WILD_DRAW_FOUR'))
        activate_next_player(game_data)
        affected_player = game_data['players'][1]
        self.assertEqual(len(affected_player['hand']), 11)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][2])

    def test_can_play_card_succeeds_with_any_special_card(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        # Set the top of stack to an arbitrary card color and value
        game_data['stack'][-1]['color'] = 'RED'
        game_data['stack'][-1]['value'] = 5
        card = create_card('WILD')
        self.assertTrue(can_play_card(game_data, card))
        card = create_card('WILD_DRAW_FOUR')
        self.assertTrue(can_play_card(game_data, card))

    def test_can_play_card_succeeds_with_matching_color(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        card_values = CARD_VALUES + SPECIAL_COLOR_CARDS
        game_data['stack'][-1] = create_card('any_value', 'RED')
        for value in CARD_VALUES:
            card = create_card(value, 'RED')
            self.assertTrue(can_play_card(game_data, card))

    def test_can_play_card_succeeds_with_matching_value(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        game_data['stack'][-1] = create_card('5', 'any_color')
        for color in CARD_COLORS:
            card = create_card('5', color)
            self.assertTrue(can_play_card(game_data, card))

    def test_can_play_card_fails_if_color_and_value_not_matching(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        # Set the top of stack to an arbitrary card color and value
        game_data['stack'][-1] = create_card('5', 'GREEN')
        # Pick a card that doesn't have a matching value or color
        card = create_card('6', 'RED')
        self.assertFalse(can_play_card(game_data, card))

    def test_reclaim_stack(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        game_data['deck'] = []
        game_data['stack'] = [create_card('WILD') for __ in range(4)]
        top = game_data['stack'][-1]
        to_be_reclaimed = game_data['stack'][0:3]
        reclaim_stack(game_data)
        self.assertEqual(game_data['stack'], [top])
        self.assertEqual(len(to_be_reclaimed), len(game_data['deck']))
        for card in to_be_reclaimed:
            self.assertIn(card, game_data['deck'])

    def test_reclaim_stack_scrubs_wild_cards(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        cards = []
        cards += [create_card('WILD', 'GREEN') for __ in range(4)]
        cards += [create_card('WILD_DRAW_FOUR', 'GREEN') for __ in range(4)]
        game_data['stack'] = cards
        reclaim_stack(game_data)
        for card in game_data['deck']:
            self.assertIsNone(card['color'])

    def test_reclaim_stack_does_not_scrub_normal_cards(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        cards = []
        cards += [create_card('0', 'GREEN') for __ in range(4)]
        game_data['stack'] = cards
        reclaim_stack(game_data)
        for card in game_data['deck']:
            self.assertIsNotNone(card['color'])

    def test_draw_card(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        player = game_data['players'][0]
        draw_card(game_data, player)
        self.assertEqual(len(player['hand']), 8)

    def test_draw_cards_triggers_reclaim_stack(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        game_data['deck'] = [create_card('WILD') for __ in range(3)]
        game_data['stack'] = [create_card('WILD') for __ in range(4)]
        top = game_data['stack'][-1]
        to_be_reclaimed = game_data['stack'][0:3]
        player = game_data['players'][0]
        draw_card(game_data, player)
        draw_card(game_data, player)
        draw_card(game_data, player)
        self.assertEqual(game_data['stack'], [top])
        self.assertEqual(len(to_be_reclaimed), len(game_data['deck']))
        for card in to_be_reclaimed:
            self.assertIn(card, game_data['deck'])

    def test_draw_two_triggers_reclaim_stack(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        game_data['deck'] = [create_card('WILD') for __ in range(2)]
        game_data['stack'] = [create_card('WILD') for __ in range(4)]
        top = game_data['stack'][-1]
        to_be_reclaimed = game_data['stack'][0:3]
        player = game_data['players'][0]
        draw_two(game_data, player)
        self.assertEqual(game_data['stack'], [top])
        self.assertEqual(len(to_be_reclaimed), len(game_data['deck']))
        for card in to_be_reclaimed:
            self.assertIn(card, game_data['deck'])

    def test_draw_four_triggers_reclaim_stack(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        game_data['deck'] = [create_card('WILD') for __ in range(4)]
        game_data['stack'] = [create_card('WILD') for __ in range(4)]
        top = game_data['stack'][-1]
        to_be_reclaimed = game_data['stack'][0:3]
        player = game_data['players'][0]
        draw_four(game_data, player)
        self.assertEqual(game_data['stack'], [top])
        self.assertEqual(len(to_be_reclaimed), len(game_data['deck']))
        for card in to_be_reclaimed:
            self.assertIn(card, game_data['deck'])

    def test_deal_cards_avoid_starting_stack_with_special_cards(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        for special_type in SPECIAL_CARDS + SPECIAL_COLOR_CARDS:
            game_data['deck'] = []
            for __ in range(8):
                game_data['deck'].append(create_card(special_type, 'any_color'))
            start_game(game_data)
            self.assertFalse(game_data['stack'])

    def test_deal_cards_claims_entire_stack(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        game_data['deck'] = [create_card('4', 'RED')]
        game_data['stack'] = [create_card('4', 'BLUE') for __ in range(8)]
        deal_cards(game_data)
        self.assertEqual(len(game_data['stack']), 1)

    def test_play_card(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        player = game_data['players'][0]
        card = player['hand'][0]
        card['value'] = '5'
        card['color'] = 'RED'
        game_data['stack'][-1]['color'] = 'RED'
        save_state(game_data)
        result = play_card(game_data['id'], player['id'], card['id'])
        game_data = load_state(game_data['id'])
        player = game_data['players'][0]
        self.assertTrue(result)
        # The card played should be on top of the stack
        self.assertEqual(game_data['stack'][-1], card)
        # Stack should contain two cards now
        self.assertEqual(len(game_data['stack']), 2)
        # Player's hand should contain one less than the original seven
        self.assertEqual(len(player['hand']), 6)
        # The second player should now be the active player
        self.assertEqual(get_active_player(game_data), game_data['players'][1])

    def test_play_card_fails_when_game_id_not_valid(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        player = game_data['players'][0]
        card = player['hand'][0]
        card['value'] = '5'
        card['color'] = 'RED'
        game_data['stack'][-1]['color'] = 'RED'
        save_state(game_data)
        result = play_card('bad_game_id', player['id'], card['id'])
        self.assertFalse(result)

    def test_play_card_fails_when_player_id_not_valid(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        player = game_data['players'][0]
        card = player['hand'][0]
        card['value'] = '5'
        card['color'] = 'RED'
        game_data['stack'][-1]['color'] = 'RED'
        save_state(game_data)
        result = play_card(game_data['id'], 'bad_player_id', card['id'])
        self.assertFalse(result)

    def test_play_card_fails_when_card_id_not_valid(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        player = game_data['players'][0]
        card = player['hand'][0]
        card['value'] = '5'
        card['color'] = 'RED'
        game_data['stack'][-1]['color'] = 'RED'
        save_state(game_data)
        result = play_card(game_data['id'], player['id'], 'bad_card_id')
        self.assertFalse(result)

    def test_play_card_fails_when_player_not_active(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        player = game_data['players'][0]
        card = player['hand'][0]
        card['value'] = '5'
        card['color'] = 'RED'
        game_data['stack'][-1]['color'] = 'RED'
        player['active'] = False
        save_state(game_data)
        result = play_card(game_data['id'], player['id'], card['id'])
        self.assertFalse(result)

    def test_play_card_fails_when_game_not_active(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        player = game_data['players'][0]
        card = player['hand'][0]
        card['value'] = '5'
        card['color'] = 'RED'
        game_data['stack'][-1]['color'] = 'RED'
        game_data['active'] = False
        save_state(game_data)
        result = play_card(game_data['id'], player['id'], card['id'])
        self.assertFalse(result)

    def test_play_card_fails_if_card_not_playable(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        player = game_data['players'][0]
        card = player['hand'][0]
        card['value'] = '5'
        card['color'] = 'RED'
        game_data['stack'][-1]['value'] = '4'
        game_data['stack'][-1]['color'] = 'GREEN'
        save_state(game_data)
        result = play_card(game_data['id'], player['id'], card['id'])
        self.assertFalse(result)

    def test_play_card_fails_if_special_card_with_no_selected_color(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        player = game_data['players'][0]
        card = player['hand'][0]
        card['value'] = 'WILD'
        card['color'] = None
        save_state(game_data)
        result = play_card(game_data['id'], player['id'], card['id'])
        self.assertFalse(result)
        player = game_data['players'][1]
        card = player['hand'][0]
        card['value'] = 'WILD_DRAW_FOUR'
        card['color'] = None
        save_state(game_data)
        result = play_card(game_data['id'], player['id'], card['id'])
        self.assertFalse(result)

    def test_play_card_fails_if_special_card_with_bad_selected_color(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        player = game_data['players'][0]
        card = player['hand'][0]
        card['value'] = 'WILD'
        card['color'] = None
        save_state(game_data)
        result = play_card(game_data['id'], player['id'], card['id'], 'PINK')
        self.assertFalse(result)

    def test_play_card_special_card_with_valid_selected_color(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        player = game_data['players'][0]
        card = player['hand'][0]
        card['value'] = 'WILD'
        card['color'] = None
        save_state(game_data)
        result = play_card(game_data['id'], player['id'], card['id'], 'RED')
        self.assertTrue(result)

    def test_play_card_sets_reverse_flag_when_reverse_card_is_played(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        player = game_data['players'][0]
        card = player['hand'][0]
        card['value'] = 'REVERSE'
        card['color'] = 'RED'
        game_data['stack'][-1]['color'] = 'RED'
        save_state(game_data)
        play_card(game_data['id'], player['id'], card['id'])
        game_data = load_state(game_data['id'])
        self.assertTrue(game_data['reverse'])

    def test_play_card_player_goes_out(self):
        game_data = create_new_game('MyGame', 'PlayerOne', 1)
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        add_player_to_game(game_data, 'PlayerFour')
        add_player_to_game(game_data, 'PlayerFive')
        start_game(game_data)
        player = game_data['players'][0]
        card = create_card('5', 'GREEN')
        player['hand'] = [card]
        game_data['stack'][-1]['color'] = 'GREEN'
        save_state(game_data)
        play_card(game_data['id'], player['id'], card['id'])
        game_data = load_state(game_data['id'])
        player = game_data['players'][0]
        self.assertTrue(player['game_winner'])

    def test_play_card_player_goes_out_check_active_player_next_round(self):
        game_data = create_new_game('MyGame', 'PlayerOne', points_to_win=10000)
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        add_player_to_game(game_data, 'PlayerFour')
        add_player_to_game(game_data, 'PlayerFive')
        start_game(game_data)
        player = game_data['players'][0]
        card = create_card('5', 'GREEN')
        player['hand'] = [card]
        game_data['stack'][-1]['color'] = 'GREEN'
        save_state(game_data)
        play_card(game_data['id'], player['id'], card['id'])
        game_data = load_state(game_data['id'])
        player = game_data['players'][0]
        self.assertFalse(player['game_winner'])
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][1])

    def test_play_card_fails_when_illegal_wild_draw_four_is_played(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Set top of stack to red card
        game_data['stack'][-1]['color'] = 'RED'
        # Ensure the player has a red card
        player = game_data['players'][0]
        player['hand'][0]['value'] = '5'
        player['hand'][0]['color'] = 'RED'
        # Give the player a WILD_DRAW_FOUR card
        player['hand'][1]['value'] = 'WILD_DRAW_FOUR'
        player['hand'][1]['color'] = None
        save_state(game_data)
        card = player['hand'][1]
        result = play_card(game_data['id'], player['id'], card['id'],
                           selected_color='GREEN')
        # Should fail since the WILD_DRAW_FOUR should be allowed if the
        # player has a matching color card that could be played.
        self.assertFalse(result)

    def test_play_card_draw_four_card_with_same_color_as_top_of_stack(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        player = game_data['players'][0]
        player['hand'] = []
        player['hand'].append(create_card('WILD_DRAW_FOUR'))
        card = player['hand'][0]
        # Set top of stack to arbitrary red card
        game_data['stack'][-1]['value'] = '5'
        game_data['stack'][-1]['color'] = 'RED'
        save_state(game_data)
        result = play_card(game_data['id'], player['id'], card['id'], 'RED')
        self.assertTrue(result)

    def test_count_points_for_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        player = game_data['players'][0]
        hand = []
        hand.append(create_card('WILD'))
        hand.append(create_card('WILD_DRAW_FOUR'))
        hand.append(create_card('5', 'GREEN'))
        hand.append(create_card('3', 'RED'))
        hand.append(create_card('2', 'BLUE'))
        hand.append(create_card('REVERSE', 'RED'))
        hand.append(create_card('SKIP', 'YELLOW'))
        player['hand'] = hand
        points = count_points_for_player(player)
        self.assertEqual(points, 150)

    def test_count_points(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        start_game(game_data)
        hand = []
        hand.append(create_card('WILD'))
        hand.append(create_card('WILD_DRAW_FOUR'))
        hand.append(create_card('5', 'GREEN'))
        hand.append(create_card('3', 'RED'))
        hand.append(create_card('2', 'BLUE'))
        hand.append(create_card('REVERSE', 'RED'))
        hand.append(create_card('SKIP', 'YELLOW'))
        game_data['players'][1]['hand'] = hand
        game_data['players'][2]['hand'] = hand
        winner = game_data['players'][0]
        points = count_points(game_data, winner)
        self.assertEqual(points, 300)

    def test_set_round_winner(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        add_player_to_game(game_data, 'PlayerFour')
        start_game(game_data)
        hand = []
        hand.append(create_card('5', 'GREEN'))
        hand.append(create_card('3', 'RED'))
        hand.append(create_card('2', 'BLUE'))
        hand.append(create_card('REVERSE', 'RED'))
        hand.append(create_card('SKIP', 'YELLOW'))
        game_data['players'][1]['hand'] = hand
        game_data['players'][2]['hand'] = hand
        game_data['players'][3]['hand'] = hand
        winner = game_data['players'][0]
        set_round_winner(game_data, winner)
        self.assertEqual(winner['points'], 150)
        self.assertEqual(winner['rounds_won'], 1)
        self.assertFalse(winner['game_winner'])

    def test_set_round_winner_deal_cards(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        add_player_to_game(game_data, 'PlayerFour')
        start_game(game_data)
        hand = []
        hand.append(create_card('5', 'GREEN'))
        hand.append(create_card('3', 'RED'))
        hand.append(create_card('2', 'BLUE'))
        hand.append(create_card('REVERSE', 'RED'))
        hand.append(create_card('SKIP', 'YELLOW'))
        game_data['players'][1]['hand'] = hand
        game_data['players'][2]['hand'] = hand
        game_data['players'][3]['hand'] = hand
        winner = game_data['players'][0]
        set_round_winner(game_data, winner)
        for player in game_data['players']:
            self.assertEqual(len(player['hand']), 7)

    def test_set_round_winner_triggers_set_game_winner(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        add_player_to_game(game_data, 'PlayerFour')
        start_game(game_data)
        hand = []
        hand.append(create_card('WILD'))
        hand.append(create_card('WILD_DRAW_FOUR'))
        hand.append(create_card('5', 'GREEN'))
        hand.append(create_card('3', 'RED'))
        hand.append(create_card('2', 'BLUE'))
        hand.append(create_card('REVERSE', 'RED'))
        hand.append(create_card('SKIP', 'YELLOW'))
        game_data['players'][1]['hand'] = hand
        game_data['players'][2]['hand'] = hand
        game_data['players'][3]['hand'] = hand
        winner = game_data['players'][0]
        set_round_winner(game_data, winner)
        self.assertTrue(winner['game_winner'])

    def test_set_round_winner_without_set_game_winner_due_to_high_goal(self):
        game_data = create_new_game('MyGame', 'PlayerOne', points_to_win=451)
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        add_player_to_game(game_data, 'PlayerFour')
        start_game(game_data)
        hand = []
        hand.append(create_card('WILD'))
        hand.append(create_card('WILD_DRAW_FOUR'))
        hand.append(create_card('5', 'GREEN'))
        hand.append(create_card('3', 'RED'))
        hand.append(create_card('2', 'BLUE'))
        hand.append(create_card('REVERSE', 'RED'))
        hand.append(create_card('SKIP', 'YELLOW'))
        game_data['players'][1]['hand'] = hand
        game_data['players'][2]['hand'] = hand
        game_data['players'][3]['hand'] = hand
        winner = game_data['players'][0]
        set_round_winner(game_data, winner)
        self.assertFalse(winner['game_winner'])

    def test_game_no_longer_active_after_set_game_winner(self):
        game_data = create_new_game('MyGame', 'PlayerOne', 451)
        start_game(game_data)
        set_game_winner(game_data, game_data['players'][0])
        self.assertFalse(game_data['active'])

    def test_game_no_player_active_after_set_game_winner(self):
        game_data = create_new_game('MyGame', 'PlayerOne', 451)
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        set_game_winner(game_data, game_data['players'][0])

        self.assertFalse(game_data['players'][0]['active'])
        self.assertFalse(game_data['players'][1]['active'])
        # for player in game_data['players']:
        #     self.assertFalse(player['active'])

    def test_ended_at_not_none_after_set_game_winner(self):
        game_data = create_new_game('MyGame', 'PlayerOne', 451)
        start_game(game_data)
        set_game_winner(game_data, game_data['players'][0])
        self.assertIsNotNone(game_data['ended_at'])

    def test_reclaim_cards(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        add_player_to_game(game_data, 'PlayerFour')
        start_game(game_data)
        self.assertEqual(len(game_data['deck']), 79)
        top_card = game_data['stack'][-1]
        reclaim_cards(game_data)
        self.assertEqual(len(game_data['stack']), 29)
        self.assertEqual(top_card, game_data['stack'][-1])
        for player in game_data['players']:
            self.assertFalse(player['hand'])

    def test_player_draw_card(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        # Set top of stack to an arbitrary card
        game_data['stack'][-1]['color'] = 'RED'
        game_data['stack'][-1]['value'] = '5'
        player = game_data['players'][0]
        # Set player's hand to not have a match, so the draw succeeds
        player['hand'] = []
        player['hand'].append(create_card('3', 'GREEN'))
        player['hand'].append(create_card('6', 'YELLOW'))
        player['hand'].append(create_card('7', 'BLUE'))
        save_state(game_data)
        result = player_draw_card(game_data['id'], player['id'])
        game_data = load_state(game_data['id'])
        player = game_data['players'][0]
        self.assertTrue(result)
        self.assertEqual(len(player['hand']), 4)

    def test_player_draw_card_fails_when_game_id_not_valid(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        # Set top of stack to an arbitrary card
        game_data['stack'][-1]['color'] = 'RED'
        game_data['stack'][-1]['value'] = '5'
        player = game_data['players'][0]
        # Set player's hand to not have a match, so the draw succeeds
        player['hand'] = []
        player['hand'].append(create_card('3', 'GREEN'))
        player['hand'].append(create_card('6', 'YELLOW'))
        player['hand'].append(create_card('7', 'BLUE'))
        save_state(game_data)
        result = player_draw_card('bad_game_id', player['id'])
        self.assertFalse(result)

    def test_player_draw_card_fails_when_player_id_not_valid(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        # Set top of stack to an arbitrary card
        game_data['stack'][-1]['color'] = 'RED'
        game_data['stack'][-1]['value'] = '5'
        player = game_data['players'][0]
        # Set player's hand to not have a match, so the draw succeeds
        player['hand'] = []
        player['hand'].append(create_card('3', 'GREEN'))
        player['hand'].append(create_card('6', 'YELLOW'))
        player['hand'].append(create_card('7', 'BLUE'))
        save_state(game_data)
        result = player_draw_card(game_data['id'], 'bad_player_id')
        self.assertFalse(result)

    def test_player_draw_card_fails_when_game_not_active(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        # Set top of stack to an arbitrary card
        game_data['stack'][-1]['color'] = 'RED'
        game_data['stack'][-1]['value'] = '5'
        player = game_data['players'][0]
        # Set player's hand to not have a match, so the draw succeeds
        player['hand'] = []
        player['hand'].append(create_card('3', 'GREEN'))
        player['hand'].append(create_card('6', 'YELLOW'))
        player['hand'].append(create_card('7', 'BLUE'))
        game_data['active'] = False
        player = game_data['players'][0]
        save_state(game_data)
        result = player_draw_card(game_data['id'], player['id'])
        self.assertFalse(result)

    def test_player_draw_card_fails_when_player_not_active(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        # Set top of stack to an arbitrary card
        game_data['stack'][-1]['color'] = 'RED'
        game_data['stack'][-1]['value'] = '5'
        player = game_data['players'][0]
        # Set player's hand to not have a match, so the draw succeeds
        player['hand'] = []
        player['hand'].append(create_card('3', 'GREEN'))
        player['hand'].append(create_card('6', 'YELLOW'))
        player['hand'].append(create_card('7', 'BLUE'))
        player['active'] = False
        save_state(game_data)
        result = player_draw_card(game_data['id'], player['id'])
        self.assertFalse(result)

    def test_player_draw_card_advances_to_next_player(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Set top of stack to an arbitrary card
        game_data['stack'][-1]['color'] = 'RED'
        game_data['stack'][-1]['value'] = '5'
        player = game_data['players'][0]
        # Set top of deck to a non-matching card, to ensure that the next
        # player is activated after the draw
        game_data['deck'][-1]['color'] = 'BLUE'
        game_data['deck'][-1]['value'] = '7'
        # Set player's hand to not have a match, so the draw succeeds
        player['hand'] = []
        player['hand'].append(create_card('3', 'GREEN'))
        player['hand'].append(create_card('6', 'YELLOW'))
        player['hand'].append(create_card('7', 'BLUE'))
        save_state(game_data)
        player = game_data['players'][0]
        result = player_draw_card(game_data['id'], player['id'])
        game_data = load_state(game_data['id'])
        player = game_data['players'][0]
        self.assertTrue(result)
        self.assertEqual(len(player['hand']), 4)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][1])

    def test_player_draw_card_advances_to_next_player_ignore_reverse(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Set top of stack to non-color-matching REVERSE
        game_data['stack'][-1]['value'] = 'REVERSE'
        game_data['stack'][-1]['color'] = 'RED'
        player = game_data['players'][0]
        # Set top of deck to a non-matching card, to ensure that the next
        # player is activated after the draw
        game_data['deck'][-1]['color'] = 'BLUE'
        game_data['deck'][-1]['value'] = '7'
        # Set player's hand to not have a match, so the draw succeeds
        player['hand'] = []
        player['hand'].append(create_card('3', 'GREEN'))
        player['hand'].append(create_card('6', 'YELLOW'))
        player['hand'].append(create_card('7', 'BLUE'))
        save_state(game_data)
        player = game_data['players'][0]
        result = player_draw_card(game_data['id'], player['id'])
        game_data = load_state(game_data['id'])
        player = game_data['players'][0]
        self.assertTrue(result)
        self.assertEqual(len(player['hand']), 4)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][1])

    def test_player_draw_card_advances_to_next_player_ignore_skip(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Set top of stack to non-color-matching SKIP
        game_data['stack'][-1]['value'] = 'SKIP'
        game_data['stack'][-1]['color'] = 'RED'
        player = game_data['players'][0]
        # Set top of deck to a non-matching card, to ensure that the next
        # player is activated after the draw
        game_data['deck'][-1]['color'] = 'BLUE'
        game_data['deck'][-1]['value'] = '7'
        # Set player's hand to not have a match, so the draw succeeds
        player['hand'] = []
        player['hand'].append(create_card('3', 'GREEN'))
        player['hand'].append(create_card('6', 'YELLOW'))
        player['hand'].append(create_card('7', 'BLUE'))
        save_state(game_data)
        player = game_data['players'][0]
        result = player_draw_card(game_data['id'], player['id'])
        game_data = load_state(game_data['id'])
        player = game_data['players'][0]
        self.assertTrue(result)
        self.assertEqual(len(player['hand']), 4)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][1])

    def test_player_draw_card_advances_to_next_player_ignore_draw_two(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Set top of stack to non-color-matching DRAW_TWO
        game_data['stack'][-1]['value'] = 'DRAW_TWO'
        game_data['stack'][-1]['color'] = 'RED'
        player = game_data['players'][0]
        # Set top of deck to a non-matching card, to ensure that the next
        # player is activated after the draw
        game_data['deck'][-1]['color'] = 'BLUE'
        game_data['deck'][-1]['value'] = '7'
        # Set player's hand to not have a match, so the draw succeeds
        player['hand'] = []
        player['hand'].append(create_card('3', 'GREEN'))
        player['hand'].append(create_card('6', 'YELLOW'))
        player['hand'].append(create_card('7', 'BLUE'))
        save_state(game_data)
        player = game_data['players'][0]
        result = player_draw_card(game_data['id'], player['id'])
        game_data = load_state(game_data['id'])
        player = game_data['players'][0]
        self.assertTrue(result)
        self.assertEqual(len(player['hand']), 4)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][1])

    def test_player_draw_card_advances_to_next_player_ignore_draw_four(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Set top of stack to non-color-matching WILD_DRAW_FOUR
        game_data['stack'][-1]['value'] = 'WILD_DRAW_FOUR'
        game_data['stack'][-1]['color'] = 'RED'
        player = game_data['players'][0]
        # Set top of deck to a non-matching card, to ensure that the next
        # player is activated after the draw
        game_data['deck'][-1]['color'] = 'BLUE'
        game_data['deck'][-1]['value'] = '7'
        # Set player's hand to not have a match, so the draw succeeds
        player['hand'] = []
        player['hand'].append(create_card('3', 'GREEN'))
        player['hand'].append(create_card('6', 'YELLOW'))
        player['hand'].append(create_card('7', 'BLUE'))
        save_state(game_data)
        player = game_data['players'][0]
        result = player_draw_card(game_data['id'], player['id'])
        game_data = load_state(game_data['id'])
        player = game_data['players'][0]
        self.assertTrue(result)
        self.assertEqual(len(player['hand']), 4)
        active_player = get_active_player(game_data)
        self.assertEqual(active_player, game_data['players'][1])

    def test_player_draw_card_does_not_advance_if_drawn_card_is_playable(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        # Set top of stack to an arbitrary card
        game_data['stack'][-1]['color'] = 'RED'
        game_data['stack'][-1]['value'] = '5'
        player = game_data['players'][0]
        # Set top of deck to a matching card, to test that the first
        # player remains active after the draw
        game_data['deck'][-1]['color'] = 'RED'
        game_data['deck'][-1]['value'] = '1'
        # Set player's hand to not have a match, so the draw succeeds
        player['hand'] = []
        player['hand'].append(create_card('3', 'GREEN'))
        player['hand'].append(create_card('6', 'YELLOW'))
        player['hand'].append(create_card('7', 'BLUE'))
        save_state(game_data)
        player = game_data['players'][0]
        result = player_draw_card(game_data['id'], player['id'])
        game_data = load_state(game_data['id'])
        player = game_data['players'][0]
        self.assertTrue(result)
        self.assertEqual(len(player['hand']), 4)
        active_player = get_active_player(game_data)
        # Ensure that the first player is still active
        self.assertEqual(active_player, game_data['players'][0])

    def test_join_game(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        save_state(game_data)
        result = join_game(game_data['id'], 'PlayerTwo')
        self.assertIsNotNone(result)

    def test_join_game_defaults(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        save_state(game_data)
        result = join_game(game_data['id'], '')
        self.assertIsNotNone(result)
        game_data = load_state(game_data['id'])
        self.assertIn(DEFAULT_PLAYER_NAME, game_data['players'][1]['name'])
        result = join_game(game_data['id'], None)
        self.assertIsNotNone(result)
        game_data = load_state(game_data['id'])
        self.assertIn(DEFAULT_PLAYER_NAME, game_data['players'][2]['name'])

    def test_join_game_fails_when_game_id_not_valid(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        save_state(game_data)
        result = join_game('bad_game_id', 'PlayerTwo')
        self.assertIsNone(result)

    def test_join_game_fails_when_game_is_already_active(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        save_state(game_data)
        result = join_game(game_data['id'], 'PlayerTwo')
        self.assertIsNone(result)

    def test_join_game_fails_when_game_is_over(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        game_data['ended_at'] = 'sometime'
        save_state(game_data)
        result = join_game(game_data['id'], 'PlayerTwo')
        self.assertIsNone(result)

    def test_join_game_fails_when_max_players_reached(self):
        game_data = create_new_game('MyGame', 'PlayerOne', max_players=1)
        save_state(game_data)
        result = join_game(game_data['id'], 'PlayerTwo')
        self.assertIsNone(result)

    def test_leave_game(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        player2 = add_player_to_game(game_data, 'PlayerTwo')
        save_state(game_data)
        result = leave_game(game_data['id'], player2['id'])
        self.assertTrue(result)
        game_data = load_state(game_data['id'])
        self.assertFalse(game_data['ended_at'])
        self.assertEqual(len(game_data['players']), 1)

    def test_leave_game_fails_when_game_id_not_valid(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        save_state(game_data)
        player = game_data['players'][0]
        result = leave_game('bad_game_id', player['id'])
        self.assertFalse(result)

    def test_leave_game_fails_when_player_id_not_valid(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        save_state(game_data)
        player = game_data['players'][0]
        result = leave_game(game_data['id'], 'bad_player_id')
        self.assertFalse(result)

    def test_leave_game_fails_when_game_is_over(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        game_data['ended_at'] = 'sometime'
        save_state(game_data)
        player = game_data['players'][0]
        result = leave_game(game_data['id'], player['id'])
        self.assertFalse(result)

    def test_leave_game_reassign_admin_role_when_admin_leaves(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        save_state(game_data)
        # Verify that PlayerTwo is not admin
        self.assertFalse(game_data['players'][1]['admin'])
        # Remove the first player, which is the admin
        leave_game(game_data['id'], game_data['players'][0]['id'])
        game_data = load_state(game_data['id'])
        # PlayerTwo should now be in the first position
        self.assertEqual(game_data['players'][0]['name'], 'PlayerTwo')
        # PlayerTwo should now be admin
        self.assertTrue(game_data['players'][0]['admin'])

    def test_leave_game_reassign_admin_role_when_admin_leaves_active_game(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        start_game(game_data)
        # Verify that PlayerTwo is not admin
        self.assertFalse(game_data['players'][1]['admin'])
        # Make PlayerTwo the active player
        activate_next_player(game_data, card_drawn=True)
        save_state(game_data)
        # Remove the first player, which is the admin
        leave_game(game_data['id'], game_data['players'][0]['id'])
        game_data = load_state(game_data['id'])
        # PlayerTwo should now be in the first position
        self.assertEqual(game_data['players'][0]['name'], 'PlayerTwo')
        # PlayerTwo should now be admin
        self.assertTrue(game_data['players'][0]['admin'])
        # PlayerTwo should still be active
        self.assertTrue(game_data['players'][0]['active'])

    def test_leave_game_activate_next_player_when_active_player_leaves(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        start_game(game_data)
        # Make PlayerTwo the active player
        activate_next_player(game_data, card_drawn=True)
        # PlayerTwo should be active now
        self.assertTrue(game_data['players'][1]['active'])
        save_state(game_data)
        # Remove PlayerTwo, which is the active player
        leave_game(game_data['id'], game_data['players'][1]['id'])
        game_data = load_state(game_data['id'])
        # PlayerThree should now be in the second position
        self.assertEqual(game_data['players'][1]['name'], 'PlayerThree')
        # PlayerThree should now be active
        self.assertTrue(game_data['players'][1]['active'])

    def test_leave_game_no_activate_next_player_when_game_not_started(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        save_state(game_data)
        # Remove a player
        leave_game(game_data['id'], game_data['players'][0]['id'])
        game_data = load_state(game_data['id'])
        # Verify that no player is wrongly activated
        for player in game_data['players']:
            self.assertFalse(player['active'])

    def test_leave_game_when_active_admin_leaves(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        start_game(game_data)
        # Verify that PlayerTwo is not admin
        self.assertFalse(game_data['players'][1]['admin'])
        # Verify that PlayerTwo is not active
        self.assertFalse(game_data['players'][1]['active'])
        save_state(game_data)
        # Remove the first player, which is the active player and admin
        leave_game(game_data['id'], game_data['players'][0]['id'])
        game_data = load_state(game_data['id'])
        # PlayerTwo should now be in the first position
        self.assertEqual(game_data['players'][0]['name'], 'PlayerTwo')
        # PlayerTwo should now be admin
        self.assertTrue(game_data['players'][0]['admin'])
        # PlayerTwo should still be active
        self.assertTrue(game_data['players'][0]['active'])

    def test_leave_game_no_players_remaining_in_game_not_yet_started(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        save_state(game_data)
        # Remove both players
        leave_game(game_data['id'], game_data['players'][0]['id'])
        leave_game(game_data['id'], game_data['players'][1]['id'])
        game_data = load_state(game_data['id'])
        # Players list should now be empty
        self.assertFalse(game_data['players'])
        # Game should have ended
        self.assertIsNotNone(game_data['ended_at'])

    def test_leave_game_one_player_remaining_in_active_game(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        start_game(game_data)
        save_state(game_data)
        # Remove first two players, leaving only PlayerThree
        leave_game(game_data['id'], game_data['players'][0]['id'])
        leave_game(game_data['id'], game_data['players'][1]['id'])
        game_data = load_state(game_data['id'])
        # Players list should only contain one player
        self.assertEqual(len(game_data['players']), 1)
        # PlayerThree should be in the first position
        self.assertEqual(game_data['players'][0]['name'], 'PlayerThree')
        # PlayerThree should not be active
        self.assertFalse(game_data['players'][0]['active'])
        # Game should no longer be active
        self.assertFalse(game_data['active'])
        # Game should have ended
        self.assertIsNotNone(game_data['ended_at'])

    def test_leave_game_reclaim_cards_when_player_leaves_active_game(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        start_game(game_data)
        # Set PlayerOne's hand
        hand = []
        hand.append(create_card('1', 'RED'))
        hand.append(create_card('2', 'BLUE'))
        hand.append(create_card('3', 'GREEN'))
        hand.append(create_card('4', 'YELLOW'))
        game_data['players'][0]['hand'] = hand
        save_state(game_data)
        # Remove PlayerOne
        leave_game(game_data['id'], game_data['players'][0]['id'])
        game_data = load_state(game_data['id'])
        # Bottom of stack should contain the removed player's cards
        bottom_cards = game_data['stack'][:4]
        self.assertEqual(bottom_cards, hand)

    def test_leave_game_reclaim_cards_when_two_players_leave_active_game(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        add_player_to_game(game_data, 'PlayerThree')
        add_player_to_game(game_data, 'PlayerFour')
        start_game(game_data)
        # Set PlayerOne's hand
        hand1 = []
        hand1.append(create_card('1', 'RED'))
        hand1.append(create_card('2', 'BLUE'))
        hand1.append(create_card('3', 'GREEN'))
        hand1.append(create_card('4', 'YELLOW'))
        game_data['players'][0]['hand'] = hand1
        # Set PlayerTwo's hand
        hand2 = []
        hand2.append(create_card('5', 'YELLOW'))
        hand2.append(create_card('6', 'GREEN'))
        hand2.append(create_card('7', 'BLUE'))
        hand2.append(create_card('8', 'RED'))
        game_data['players'][1]['hand'] = hand2
        save_state(game_data)
        # Remove PlayerOne and PlayerTwo
        leave_game(game_data['id'], game_data['players'][0]['id'])
        leave_game(game_data['id'], game_data['players'][1]['id'])
        game_data = load_state(game_data['id'])
        # Bottom of stack should contain the cards for both removed players
        self.assertEqual(game_data['stack'][:4], hand2)
        self.assertEqual(game_data['stack'][4:8], hand1)

    def test_admin_start_game(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        save_state(game_data)
        player = game_data['players'][0]
        result = admin_start_game(game_data['id'], player['id'])
        self.assertTrue(result)

    def test_admin_start_game_fails_when_game_id_not_valid(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        save_state(game_data)
        player = game_data['players'][0]
        result = admin_start_game('bad_game_id', player['id'])
        self.assertFalse(result)

    def test_admin_start_game_fails_when_player_id_not_valid(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        save_state(game_data)
        player = game_data['players'][0]
        result = admin_start_game(game_data['id'], 'bad_player_id')
        self.assertFalse(result)

    def test_admin_start_game_fails_when_game_id_already_active(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        start_game(game_data)
        save_state(game_data)
        player = game_data['players'][0]
        result = admin_start_game(game_data['id'], player['id'])
        self.assertFalse(result)

    def test_admin_start_game_fails_when_game_is_over(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        game_data['ended_at'] = 'sometime'
        save_state(game_data)
        player = game_data['players'][0]
        result = admin_start_game(game_data['id'], player['id'])
        self.assertFalse(result)

    def test_admin_start_game_fails_when_player_not_admin(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        add_player_to_game(game_data, 'PlayerTwo')
        player = game_data['players'][0]
        player['admin'] = False
        save_state(game_data)
        result = admin_start_game(game_data['id'], player['id'])
        self.assertFalse(result)

    def test_admin_start_game_fails_when_min_players_not_reached(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        player = game_data['players'][0]
        save_state(game_data)
        result = admin_start_game(game_data['id'], player['id'])
        self.assertFalse(result)

    def test_player_has_matching_color_card_succeeds(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        # Set top of stack to red card
        game_data['stack'][-1]['color'] = 'RED'
        # Ensure the player has a red card
        player = game_data['players'][0]
        player['hand'][0]['value'] = '5'
        player['hand'][0]['color'] = 'RED'
        result = player_has_matching_color_card(game_data, player)
        self.assertTrue(result)

    def test_player_has_matching_color_card_fails(self):
        game_data = create_new_game('MyGame', 'PlayerOne')
        start_game(game_data)
        # Set top of stack to an impossible color
        game_data['stack'][-1]['color'] = 'IMPOSSIBLE_COLOR_TO_MATCH'
        player = game_data['players'][0]
        result = player_has_matching_color_card(game_data, player)
        self.assertFalse(result)


if __name__ == '__main__':
    tests = unittest.TestLoader().loadTestsFromTestCase(GameTestCase)
    unittest.TextTestRunner(verbosity=2).run(tests)
