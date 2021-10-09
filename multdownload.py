import asyncio
import concurrent.futures
import requests
import os
import time
from sys import stdin
from math import ceil
#from tqdm import tqdm 
import logging

logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

def get_size_afk(url):
    response = requests.head(url)
    size = int(response.headers['Content-Length'])
    return size

piped=False

if not stdin.isatty():
    URL=stdin.read().strip().strip('"')
    piped=True

if piped==False:
    URL = input("URL: ").strip()
    OUTPUT = input("Name: ").strip().strip("'").strip('"')
    chunkStr=input("Chunk size(KB/MB): ")
    if "KB" in chunkStr or "kb" in chunkStr or "K" in chunkStr or "k" in chunkStr:
        chunk=int(chunkStr.strip("KbBk")) * 1024
    elif "MB" in chunkStr or "mb" in chunkStr or "M" in chunkStr or "m" in chunkStr:
        chunk=int(chunkStr.strip("MmBb"))* 1048576
    else:
        chunk=int(chunkStr.strip()) * 1048576
    filesAtATime=int(input("number of files to download at once(max 15): ").strip().strip("'").strip('"'))
else:
    OUTPUT = URL.split("/")[-1]
    chunk=int(ceil(get_size_afk(URL)/15))
    filesAtATime=15
if filesAtATime not in range(1,16):
    filesAtATime = 15
if filesAtATime >15:
    filesAtATime =15

async def get_size(url):
    response = requests.head(url)
    size = int(response.headers['Content-Length'])
    return size

def download_range(url, start, end, output):
    headers = {'Range': f'bytes={start}-{end}'}
    response = requests.get(url, headers=headers)
    
    with open(output, 'wb') as f:
        for part in response.iter_content(1024):
            f.write(part)
    


async def download(executor, url, output, chunk_size=10000000):
    loop = asyncio.get_event_loop()

    file_size = await get_size(url)
    chunks = range(0, file_size, chunk_size)

    tasks = [
        loop.run_in_executor(
            executor,
            download_range,
            url,
            start,
            start + chunk_size - 1,
            f'{output}.part{i}',
        )
        for i, start in enumerate(chunks)
    ]

    await asyncio.wait(tasks)

    with open(output, 'wb') as o:
        for i in range(len(chunks)):
            chunk_path = f'{output}.part{i}'

            with open(chunk_path, 'rb') as s:
                o.write(s.read())

            os.remove(chunk_path)


if __name__ == '__main__':
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=filesAtATime)
    loop = asyncio.get_event_loop()


    try:
        startRecv=time.perf_counter()
        loop.run_until_complete(
            download(executor, URL, OUTPUT,chunk)
        )
    finally:
        loop.close()
        endRecv=time.perf_counter()
        finalTimeRecv=endRecv-startRecv
        print(f"Downloaded in {round(endRecv,3)}s")
        if piped == False:
            input("Press any key to exit...")