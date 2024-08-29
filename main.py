import asyncio
import random
import ssl
import string
import uuid
from datetime import datetime
from itertools import batched

import environ
import structlog
from dpkt import Error
from dpkt.http import Request

from db import create_http_request_database_entry

HOST = "0.0.0.0"

HTTPS_PORT = 8889

HTTP_PORT = 8888

log = structlog.get_logger()

response_body = """HTTP/1.1 200 OK
Server: Apache/2.2.8 (Ubuntu) mod_ssl/2.2.8 OpenSSL/0.9.8g
Content-Length: {length}
Connection: close
Content-Type: text/html

{content}\n"""

env = environ.Env()

MIN_BODY_SIZE = env("MIN_BODY_SIZE", cast=int, default=512)
MAX_BODY_SIZE = env("MAX_BODY_SIZE", cast=int, default=10 * 1024)
CHUNK_SIZE = env("CHUNK_SIZE", cast=int, default=64)

ENABLE_SLEEP = env("ENABLE_SLEEP", cast=bool, default=True)
MIN_SLEEP_TIME = env("MIN_SLEEP_TIME", cast=int, default=0.01)
MAX_SLEEP_TIME = env("MAX_SLEEP_TIME", cast=int, default=0.1)

CERT_FILE_PATH = env("CERT_FILE_PATH", cast=str, default=None)
PRIVATE_KEY_FILE_PATH = env("PRIVATE_KEY_FILE_PATH", cast=str, default=None)
CHAIN_FILE_PATH = env("CHAIN_FILE_PATH", cast=str, default=None)
ENABLE_TLS = CERT_FILE_PATH is not None


def generate_response_body():
    length = random.randint(MIN_BODY_SIZE, MAX_BODY_SIZE)
    content = "".join(
        [
            random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.whitespace
            )
            for _ in range(length)
        ]
    )

    return response_body.format(
        content=content, length=length + 1
    )  # 1 extra for newline


async def handle_request(reader, writer):
    request_id = str(uuid.uuid4())
    start_time = datetime.now()
    data = await reader.read(512)
    addr = writer.get_extra_info("peername")

    try:
        request = Request(data)
        log.info(
            f"Received {request.method} request from {addr!r} for URI {request.uri}, "
            f"headers {dict(request.headers)}",
            request_id=request_id,
        )
    except Error:
        request = None
        log.info(
            f"Extracting request failed, received request "
            f"from {addr!r}, raw data is {data}"
        )

    response = generate_response_body()
    log.info(f"Sending {len(response)} byte response", request_id=request_id)

    byte_sent = 0
    for chunk in batched(response, CHUNK_SIZE):
        chunk = "".join(chunk)
        byte_sent += len(chunk)
        writer.write(chunk.encode())
        try:
            await writer.drain()
        except ConnectionError:
            total_time = round((datetime.now() - start_time).microseconds / 1000, 2)
            log.info(
                f"Connection lost after {total_time} seconds "
                f"and {byte_sent} sent bytes",
                request_id=request_id,
            )
            return

        if ENABLE_SLEEP:
            sleep_time = random.uniform(MIN_SLEEP_TIME, MAX_SLEEP_TIME)
            await asyncio.sleep(sleep_time)

    writer.close()
    await writer.wait_closed()

    end_time = datetime.now()
    total_time = round((end_time - start_time).microseconds / 1000, 2)
    log.info(f"Sent {byte_sent} bytes in {total_time} seconds", request_id=request_id)

    if request:
        await create_http_request_database_entry(
            request.uri, request.method, addr[0], start_time, end_time
        )


def get_ssl_context():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE_PATH, keyfile=PRIVATE_KEY_FILE_PATH)
    context.load_verify_locations(CHAIN_FILE_PATH)

    return context


async def main():
    http_server = await asyncio.start_server(
        handle_request,
        HOST,
        HTTP_PORT,
    )

    http_address = ", ".join(str(sock.getsockname()) for sock in http_server.sockets)
    log.info(f"Serving HTTP on {http_address}")

    if not ENABLE_TLS:
        log.info("Launching without TLS")
        async with http_server:
            await http_server.serve_forever()
    else:
        log.info("Launching with TLS")
        https_server = await asyncio.start_server(
            handle_request, HOST, HTTPS_PORT, ssl=get_ssl_context()
        )

        https_address = ", ".join(
            str(sock.getsockname()) for sock in https_server.sockets
        )
        log.info(f"Serving HTTPS on {https_address}")

        async with http_server, https_server:
            await asyncio.gather(
                http_server.serve_forever(), https_server.serve_forever()
            )


asyncio.run(main())
