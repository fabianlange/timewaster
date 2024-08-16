import asyncio
import random
import string
import time
import uuid
from itertools import batched

import structlog
from dpkt import Error
from dpkt.http import Request

log = structlog.get_logger()

response_body = """HTTP/1.1 200 OK
Server: Apache/2.2.8 (Ubuntu) mod_ssl/2.2.8 OpenSSL/0.9.8g
Content-Length: {length}
Connection: close
Content-Type: text/html

{content}\n"""

MIN_BODY_SIZE = 512
MAX_BODY_SIZE = 1024 * 10
CHUNK_SIZE = 64


def generate_response_body():
    length = random.randint(MIN_BODY_SIZE, MAX_BODY_SIZE)
    content = "".join(
        [
            random.choice(string.ascii_uppercase + string.ascii_lowercase)
            for _ in range(length)
        ]
    )

    return response_body.format(
        content=content, length=length + 1
    )  # 1 extra for newline


async def handle_echo(reader, writer):
    request_id = str(uuid.uuid4())
    start_time = time.monotonic()
    data = await reader.read(512)
    addr = writer.get_extra_info("peername")

    try:
        request = Request(data)
        log.info(
            f"Received request from {addr!r} for URI {request.uri}, "
            f"headers {dict(request.headers)}",
            request_id=request_id,
        )
    except Error:
        log.info(
            f"Extracting request failed, received request "
            f"from {addr!r}, raw data is {data}"
        )

    response = generate_response_body()
    log.info(f"Sending {len(response)} byte response", request_id=request_id)

    for chunk in batched(response, CHUNK_SIZE):
        chunk = "".join(chunk)
        writer.write(chunk.encode())
        await writer.drain()
        sleep_time = random.random()
        await asyncio.sleep(sleep_time)

    log.info("Closing connection", request_id=request_id)
    writer.close()
    await writer.wait_closed()

    total_time = round(time.monotonic() - start_time, 2)
    log.info(f"Finished request in {total_time} seconds", request_id=request_id)


async def main():
    server = await asyncio.start_server(handle_echo, "0.0.0.0", 8888)

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    log.info(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


asyncio.run(main())
