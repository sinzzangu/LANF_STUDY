import aiohttp
from urllib.parse import quote

API_KEY = None
REGION = "kr"
ACCOUNT_URL = "https://asia.api.riotgames.com"  # Account API는 아시아 서버 고정
BASE_URL = f"https://{REGION}.api.riotgames.com"

session: aiohttp.ClientSession | None = None

def set_api_key(key: str):
    """외부에서 API 키를 주입하는 함수"""
    global API_KEY
    API_KEY = key

async def create_session():
    global session
    if session is None or session.closed:
        if not API_KEY:
            raise ValueError("API key not set. Call set_api_key() first.")
        
        headers = {"X-Riot-Token": API_KEY}  # Create headers with current API_KEY
        session = aiohttp.ClientSession(headers=headers)

async def close_session():
    global session
    if session and not session.closed:
        await session.close()

async def get_account_by_riot_id(name: str, tag: str) -> dict:
    """이름#태그로 계정 정보 조회 (puuid 등 획득)"""
    await create_session()

    name_encoded = quote(name)
    tag_encoded = quote(tag)

    url = f"{ACCOUNT_URL}/riot/account/v1/accounts/by-riot-id/{name_encoded}/{tag_encoded}"  # Fixed URL path
    print(f"🔍 Making request to: {url}")  # Debug log
    
    async with session.get(url) as resp:
        print(f"📡 Response status: {resp.status}")  # Debug log
        if resp.status != 200:
            response_text = await resp.text()
            print(f"❌ Error response: {response_text}")  # Debug log
        resp.raise_for_status()
        return await resp.json()

async def get_summoner_by_puuid(puuid: str) -> dict:
    """PUUID로 소환사 상세 정보 조회"""
    await create_session()
    url = f"{BASE_URL}/lol/summoner/v4/summoners/by-puuid/{puuid}"
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()

async def get_league_info(summoner_id: str) -> list:
    """소환사 ID로 리그 정보 조회"""
    await create_session()
    url = f"{BASE_URL}/lol/league/v4/entries/by-summoner/{summoner_id}"
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()

async def get_recent_match_ids(puuid: str, count: int = 20) -> list:
    """PUUID로 최근 매치 ID 리스트 조회"""
    await create_session()
    url = f"https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()

async def get_match_detail(match_id: str) -> dict:
    """매치 ID로 상세 매치 정보 조회"""
    await create_session()
    url = f"https://asia.api.riotgames.com/lol/match/v5/matches/{match_id}"
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()