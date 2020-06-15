from nio import AsyncClient, LoginResponse, MatrixRoom, RoomMessageText

import asyncio
import json
import os
import sys

CONFIG_FILE = os.environ['NIO_CONFIG_FILE'] if 'NIO_CONFIG_FILE' in os.environ\
    else "config.json"


async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    print(
        f"Message received in room {room.display_name}\n"
        f"{room.user_name(event.sender)} | {event.body}"
    )


async def run_client(client: AsyncClient, config: dict):
    # If there are no previously-saved credentials, we'll use the password
    if not os.path.exists(config['creds_file']):
        resp = await client.login(config['password'])
        # check that we logged in succesfully
        if (isinstance(resp, LoginResponse)):
            with open(config['creds_file'], "w") as f:
                # write the login details to disk
                json.dump({
                    "access_token": resp.access_token,
                    "device_id": resp.device_id,
                    "user_id": resp.user_id
                }, f)
        else:
            print(f"Failed to log in: {resp}")
            sys.exit(1)

    with open(config['creds_file'], "r") as f:
        creds = json.load(f)

    client.access_token = creds['access_token']
    client.user_id = creds['user_id']
    client.device_id = creds['device_id']

    client.add_event_callback(message_callback, RoomMessageText)

    # Now we can send messages as the user
    await client.join(config['room_id'])
    print("Logged in using stored credentials")

    resp = await client.room_send(
        room_id=config['room_id'],
        message_type="m.room.message",
        content={
            "msgtype": "m.text",
            "body": "Hello world!"
        }
    )
    print("Result of test message:")
    print(f"Status: {resp.transport_response.status}, Event: {resp.event_id}")

    await client.sync_forever(30000, full_state=True)


async def main() -> None:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    if 'creds_file' not in config:
        config['creds_file'] = "auth.json"

    if 'NIO_PASSWORD' in os.environ:
        config['password'] = os.environ['NIO_PASSWORD']

    client = AsyncClient(config['home_server'], config['user_id'])

    if not config['room_id'].startswith('!'):
        resp = await client.room_resolve_alias(config['room_id'])
        config['room_id'] = resp.room_id

    try:
        await run_client(client, config)
    finally:
        await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        pass
