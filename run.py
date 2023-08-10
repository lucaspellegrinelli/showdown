import os
import re
import random
import asyncio
import json
import logging
import traceback
from datetime import datetime
from copy import deepcopy

import constants
from config import ShowdownConfig, init_logging

from teams import load_team
from showdown.run_battle import pokemon_battle
from showdown.websocket_client import PSWebsocketClient

from data import all_move_json
from data import pokedex
from data.mods.apply_mods import apply_mods


logger = logging.getLogger(__name__)


def generate_gen3_team(team_dump_path, uber_replacements_path):
    with open(team_dump_path, "r") as f:
        team_dump = f.read()
        teams = re.split(r"=== \[.*\] .* ===", team_dump)
        teams = [team.strip() for team in teams]
        teams = [team for team in teams if team != ""]

    with open(uber_replacements_path, "r") as f:
        uber_replacements_raw = f.read()
        uber_replacements_raw = uber_replacements_raw.split("\n\n")
        uber_replacements_raw = [line.strip() for line in uber_replacements_raw]

        uber_replacements = {}
        for pokemon_set in uber_replacements_raw:
            pokemon_name = pokemon_set.split(" ")[0]
            uber_replacements.setdefault(pokemon_name, [])
            uber_replacements[pokemon_name].append(pokemon_set)

    random_team = random.choice(teams)
    uber_pokemon = random.choice(list(uber_replacements.keys()))
    uber_replacement = random.choice(uber_replacements[uber_pokemon])

    random_team_pokemons = random_team.split("\n\n")
    idx_to_replace = random.randint(0, len(random_team_pokemons) - 1)

    random_team_pokemons[idx_to_replace] = uber_replacement
    random.shuffle(random_team_pokemons)
    return "\n\n".join(random_team_pokemons)


def generate_new_team():
    team_dump_path = "teambuilderdata/gen3ou_teams.txt"
    uber_replacements_path = "teambuilderdata/uber_replacements.txt"
    output_path = "teams/teams/desafiopokemon/current"

    team = None
    while team is None or "Blissey" in team:
        team = generate_gen3_team(team_dump_path, uber_replacements_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(team)


def check_dictionaries_are_unmodified(original_pokedex, original_move_json):
    # The bot should not modify the data dictionaries
    # This is a "just-in-case" check to make sure and will stop the bot if it mutates either of them
    if original_move_json != all_move_json:
        logger.critical("Move JSON changed!\nDumping modified version to `modified_moves.json`")
        with open("modified_moves.json", 'w') as f:
            json.dump(all_move_json, f, indent=4)
        exit(1)
    else:
        logger.debug("Move JSON unmodified!")

    if original_pokedex != pokedex:
        logger.critical(
            "Pokedex JSON changed!\nDumping modified version to `modified_pokedex.json`"
        )
        with open("modified_pokedex.json", 'w') as f:
            json.dump(pokedex, f, indent=4)
        exit(1)
    else:
        logger.debug("Pokedex JSON unmodified!")


async def showdown():
    ShowdownConfig.configure()
    init_logging(
        ShowdownConfig.log_level,
        ShowdownConfig.log_to_file
    )
    apply_mods(ShowdownConfig.pokemon_mode)

    original_pokedex = deepcopy(pokedex)
    original_move_json = deepcopy(all_move_json)

    ps_websocket_client = await PSWebsocketClient.create(
        ShowdownConfig.username,
        ShowdownConfig.password,
        ShowdownConfig.websocket_uri
    )
    await ps_websocket_client.login()

    battles_run = 0
    wins = 0
    losses = 0
    while True:
        if ShowdownConfig.log_to_file:
            ShowdownConfig.log_handler.do_rollover(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.log"))

        generate_new_team()
        team = load_team(ShowdownConfig.team)
        if ShowdownConfig.bot_mode == constants.CHALLENGE_USER:
            await ps_websocket_client.challenge_user(
                ShowdownConfig.user_to_challenge,
                ShowdownConfig.pokemon_mode,
                team
            )
        elif ShowdownConfig.bot_mode == constants.ACCEPT_CHALLENGE:
            await ps_websocket_client.accept_challenge(
                ShowdownConfig.pokemon_mode,
                team,
                ShowdownConfig.room_name
            )
        elif ShowdownConfig.bot_mode == constants.SEARCH_LADDER:
            await ps_websocket_client.search_for_match(ShowdownConfig.pokemon_mode, team)
        else:
            raise ValueError("Invalid Bot Mode: {}".format(ShowdownConfig.bot_mode))

        winner = await pokemon_battle(ps_websocket_client, ShowdownConfig.pokemon_mode)
        if winner == ShowdownConfig.username:
            wins += 1
        else:
            losses += 1

        logger.info("W: {}\tL: {}".format(wins, losses))
        check_dictionaries_are_unmodified(original_pokedex, original_move_json)

        # battles_run += 1
        # if battles_run >= ShowdownConfig.run_count:
        #     break


if __name__ == "__main__":
    generate_new_team()
    try:
        asyncio.run(showdown())
    except Exception as e:
        logger.error(traceback.format_exc())
        raise
