import asyncio
import aiohttp
import json
import ssl 
async def get_last_date():
    url = "https://npsnav.rishikeshsreehari.workers.dev/get-last-date?fund_id=SM001001"
    
    # Configure SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Configure client timeout
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, ssl=ssl_context) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Success! Last date: {data['last_date']}")
                    return data['last_date']
                else:
                    print(f"Error: Status {response.status}")
        except Exception as e:
            print(f"Error: {e}")

def main():
    print("Fetching last date...")
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # For Windows
    last_date = asyncio.run(get_last_date())
    print(f"Completed. Last date: {last_date}")

if __name__ == "__main__":
    main()