""" CLI:Register user or auth already registered user to Send, Receive or Store Messages """
import os
import json
import argparse
from datetime import datetime
import paho.mqtt.client as mqtt
from colorama import init, deinit, Fore, Back, Style
import tmessage.auth as auth  # auth.py

# Initialize colorama
init()

# Create the parser
PARSER = argparse.ArgumentParser(prog='AMU-OSS-MESSAGING',
                                 description='cli based group messaging\
                                 for amu-oss sessions',
                                 epilog='Happy learning!')

# Add the arguments
PARSER.add_argument('--user', action='store', type=str, required=True)
PARSER.add_argument('--server', action='store', type=str)
PARSER.add_argument('--port', action='store', type=int)
PARSER.add_argument('--dont-store', action='store_false',
                    help='Disables storing of messages.')

ARGS = PARSER.parse_args()

IS_STORE = ARGS.dont_store
MQTT_TOPIC = "amu"
BROKER_ENDPOINT = ARGS.server or "test.mosquitto.org"
BROKER_PORT = ARGS.port or 1883


MQTT_CLIENT = mqtt.Client()
CURRENT_USER = ARGS.user


def on_message(client, userdata, message):
    # pylint: disable=unused-argument
    """ callback functions to Process any Messages"""
    current_msg = message.payload.decode("utf-8")

    # to get the username between []
    user = current_msg.partition('[')[-1].rpartition(']')[0]
    if user != CURRENT_USER:
        print(Back.GREEN + Fore.BLACK + current_msg +
              Back.RESET + Fore.RESET + "")
        _, _, message = current_msg.partition('] ')
        if IS_STORE:
            store_messages(user, message)


FOLDER_NAME = 'messages'
SESSION_START_DATE = datetime.now().strftime('%Y-%m-%d_%H:%M')

DATA = {}


def store_messages(user, raw_msg):
    """ Store messages in JSON file """
    if not os.path.exists(FOLDER_NAME):
        os.mkdir(FOLDER_NAME)

    DATA['time'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    DATA['content'] = raw_msg
    DATA['from'] = user

    with open('messages/{}.json'.format(SESSION_START_DATE), 'a', encoding='utf-8') as outfile:
        json.dump(DATA, outfile, ensure_ascii=False, indent=4)


def main():
    """ Register a new User or Authenticates the already registered User to send message """
    try:
        if auth.check_existed(CURRENT_USER):
            password = input(f'User {CURRENT_USER} found\nEnter password: ')
            payload = auth.authenticate(CURRENT_USER, password)
        else:
            print(f'Welcome {CURRENT_USER} to tmessage!\nPlease register...')
            displayed_name = input(f'Enter your name used for display: ')
            password = input(f'Enter password: ')
            password_confirm = input(f'Re-enter password: ')
            while password != password_confirm:
                print('Passwords do not match, please try again...')
                password = input(f'Enter password: ')
                password_confirm = input(f'Re-enter password: ')
            payload = auth.register(CURRENT_USER, displayed_name,
                                    password, password_confirm)
        print('User Authorized')
        user_name = payload["user_name"]
        displayed_name = payload["displayed_name"]

        MQTT_CLIENT.on_message = on_message
        MQTT_CLIENT.connect(BROKER_ENDPOINT, BROKER_PORT)
        MQTT_CLIENT.subscribe(MQTT_TOPIC)
        MQTT_CLIENT.loop_start()
        while True:
            raw_msg = str(input(Back.RESET + Fore.RESET))
            pub_msg = f'[{user_name}] {displayed_name}: {raw_msg}'
            if raw_msg != '':
                MQTT_CLIENT.publish(MQTT_TOPIC, pub_msg)
                if IS_STORE:
                    store_messages(CURRENT_USER, raw_msg)
            else:
                print(Back.WHITE + Fore.RED +
                      "Can't send empty message", end='\n')
    except KeyboardInterrupt:
        # pylint: disable=pointless-statement
        MQTT_CLIENT.disconnect()
        Style.RESET_ALL
        deinit()
        print('\nGoodbye!')
    except ConnectionRefusedError:
        # pylint: disable=pointless-statement
        Style.RESET_ALL
        deinit()
        print("\nCan't connect please check your network connection")
    except Exception as err:  # pylint: disable=broad-except
        # pylint: disable=pointless-statement
        Style.RESET_ALL
        deinit()
        print(f'\n{err}')


if __name__ == "__main__":
    main()
