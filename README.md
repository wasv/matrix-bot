# Matrix Example Bot

An example bot for the Matrix chat protocol, 
using the [matrix-nio library](https://github.com/poljar/matrix-nio).

## Configuration

### Minimal `config.json`

```json
{
    "home_server":"https://matrix.example.org",
    "user_id":"@testbot:matrix.example.org",
    "room_id":"#room:matrix.example.org"
}
```

### Auth

The password for the Matrix user can be set in the `NIO_PASSWORD`
environment variable or in a password key in the `config.json` file.

The recommended method is the environment variable, so that the 
`config.json` can be safely distributed.
