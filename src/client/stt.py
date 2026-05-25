import asyncio
import socket

from speechmatics.tts import AsyncClient, Voice, OutputFormat

async def main():
    # Connect to the ESP32 server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 8080))

    async with AsyncClient() as client:
        async with await client.generate(
            text=input("Enter text: "),
            voice=Voice.THEO,
            output_format=OutputFormat.WAV_16000
        ) as response:
            async for chunk in response.content.iter_chunked(1024):
                client_socket.send(chunk)
            audio = b''.join([chunk async for chunk in response.content.iter_chunked(1024)])
            with open("../../audio/output.wav", "wb") as wav:
                wav.write(audio)

    client_socket.close()

if __name__ == "__main__":
    asyncio.run(main())