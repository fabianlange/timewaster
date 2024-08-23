import asyncio

import asyncssh
import structlog

SSH_PORT = 8022

log = structlog.get_logger()


def handle_client(process: asyncssh.SSHServerProcess) -> None:
    process.stdout.write("Bonjour mon amour\n")
    process.exit(0)


class MySSHServer(asyncssh.SSHServer):
    def connection_made(self, conn: asyncssh.SSHServerConnection) -> None:
        log.info(
            "SSH connection received from %s." % conn.get_extra_info("peername")[0]
        )

    def password_auth_supported(self) -> bool:
        return True

    def validate_password(self, username: str, password: str) -> bool:
        log.info(f"Login attempted with username {username} and password {password}")
        return False

    def kbdint_auth_supported(self):
        return False


async def start_server() -> None:
    log.info(f"Serving SSH on {SSH_PORT}")

    await asyncssh.create_server(
        MySSHServer,
        "",
        SSH_PORT,
        server_host_keys=["/root/ssh_host_key"],
        process_factory=handle_client,
    )


loop = asyncio.get_event_loop()
loop.run_until_complete(start_server())
loop.run_forever()
