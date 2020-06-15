import asyncio
import json
import nio
import os
import sys

class CustomClient(nio.AsyncClient):
    config = {}

    def __init__(self, homeserver: str, user: str, password='',
                 device_id='', store_path='', creds_file='auth.json',
                 ssl=None, proxy=None, config=None):
        # Calling super.__init__ means we're running the __init__ method
        # defined in AsyncClient, which this class derives from. That does a
        # bunch of setup for us automatically
        super().__init__(homeserver, user=user, device_id=device_id,
                         store_path=store_path, config=config,
                         ssl=ssl, proxy=proxy)

        # if the store location doesn't exist, we'll make it
        if store_path and not os.path.isdir(store_path):
            os.mkdir(store_path)


        self.password = password
        self.creds_file = creds_file

        # auto-join room invites
        self.add_event_callback(self.cb_autojoin_room, nio.InviteEvent)

        # print all the messages we receive
        self.add_event_callback(self.cb_print_messages, nio.RoomMessageText)

    def cb_autojoin_room(self, room: nio.MatrixRoom, event: nio.InviteEvent):
        """Callback to automatically joins a Matrix room on invite.

        Arguments:
            room {MatrixRoom} -- Provided by nio
            event {InviteEvent} -- Provided by nio
        """
        self.join(room.room_id)
        print(f"Joined Room: {room.name} - Is encrypted? {room.encrypted}")

    async def cb_print_messages(self, room: nio.MatrixRoom,
                                event: nio.RoomMessageText):
        """Callback to print all received messages to stdout.

        Arguments:
            room {MatrixRoom} -- Provided by nio
            event {RoomMessageText} -- Provided by nio
        """
        if event.decrypted:
            encrypted_symbol = "🛡 "
        else:
            encrypted_symbol = "⚠️ "
        print(f"{room.display_name} |{encrypted_symbol}| "
              f"{room.user_name(event.sender)}: {event.body}")

    async def login(self):
        # If there are no previously-saved credentials, we'll use the password
        if os.path.exists(self.creds_file):
            with open(self.creds_file, "r") as f:
                creds = json.load(f)
        else:
            resp = await super().login(self.password)
            # check that we logged in succesfully
            if (isinstance(resp, nio.LoginResponse)):
                creds = {}
                creds['access_token'] = resp.access_token
                creds['user_id'] = resp.user_id
                creds['device_id'] = resp.device_id

                with open(self.creds_file, "w") as f:
                    # write the login details to disk
                    json.dump(creds, f)
            else:
                print(f"Failed to log in: {resp}")
                sys.exit(1)

        self.access_token = creds['access_token']
        self.user_id = creds['user_id']
        self.device_id = creds['device_id']

        print("Logged in.")


async def main() -> None:
    config_file = "config.json"
    if 'NIO_CONFIG_FILE' in os.environ:
        config_file = os.environ['NIO_CONFIG_FILE']

    with open(config_file, "r") as f:
        config = json.load(f)

    if 'NIO_PASSWORD' in os.environ:
        password = os.environ['NIO_PASSWORD']
    elif 'password' in config:
        password = config['password']
    else:
        password = None

    client = CustomClient(config['home_server'], config['user_id'],
                          password=password)

    await client.login()

    try:
        await client.sync_forever(30000, full_state=True)
    finally:
        await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        pass
