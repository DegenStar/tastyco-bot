from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils.conversions import to_hex
from base64 import urlsafe_b64decode
from datetime import datetime, timedelta, timezone
from colorama import *
import cloudscraper, asyncio, random, time, json, sys, re, os

class TastyCo:
    def __init__(self) -> None:
        self.BASE_API = "https://api.tastyco.io"

        self.CAPTCHA = {
            "page_url": "https://app.tastyco.io/",
            "solver_api": "https://sctg.xyz",
            "site_key": "0x4AAAAAAET4O64ulvE1G0s4",
            "captcha_key": None
        }
        
        self.REF_CODE = "31eZ0PFgB4vQRJb"

        self.USE_PROXY = False
        self.ROTATE_PROXY = False
        
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.accounts = {}
        
        self.user_agents = []

    def load_user_agents(self):
        filename = "useragent.txt"
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()

            for line in lines:
                line = line.strip()
                if line.startswith("Mozilla/5.0"):
                    self.user_agents.append(line)

            if not self.user_agents:
                self.log(f"{Fore.RED + Style.BRIGHT}No User Agents Found In {filename}.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}UserAgents Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.user_agents)}{Style.RESET_ALL}"
            )
        except FileNotFoundError:
            self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
            self.user_agents = []

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}TastyCo {Fore.BLUE + Style.BRIGHT}Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_accounts(self):
        filename = "accounts.txt"
        try:
            with open(filename, 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            return accounts
        except Exception as e:
            print(f"{Fore.RED + Style.BRIGHT}Failed To Load Accounts: {e}{Style.RESET_ALL}")
            return None

    def load_captcha_key(self):
        filename = "sctg.txt"
        try:
            with open(filename, 'r') as file:
                captcha_key = file.readline().strip()
            self.CAPTCHA["captcha_key"] = captcha_key
            return captcha_key
        except FileNotFoundError:
            self.log(f"{Fore.RED}File {filename} Not Found.{Style.RESET_ALL}")
            return None

    def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://", "socks5h://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"
    
    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None

        proxy_url = self.check_proxy_schemes(proxy)
        return {
            "http": proxy_url,
            "https": proxy_url
        }

    def create_scraper(self, proxy_url=None):
        scraper = cloudscraper.create_scraper()
        proxies = self.build_proxy_config(proxy_url)
        if proxies:
            scraper.proxies.update(proxies)
        return scraper
    
    def display_proxy(self, proxy_url=None):
        if not proxy_url: return "No Proxy"

        proxy_url = re.sub(r"^(http|https|socks4|socks5|socks5h)://", "", proxy_url)

        if "@" in proxy_url:
            proxy_url = proxy_url.split("@", 1)[1]

        return proxy_url

    def get_next_run_time(self, anchor_minute=1):
        now = datetime.now(timezone.utc)
        today_target = now.replace(hour=0, minute=anchor_minute, second=0, microsecond=0)

        if today_target > now:
            return today_target
        else:
            return today_target + timedelta(days=1)
    
    def initialize_headers(self, idx: int):
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Origin": "https://app.tastyco.io",
            "Pragma": "no-cache",
            "Referer": "https://app.tastyco.io/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": self.accounts[idx]["user_agent"]
        }

        return headers.copy()
        
    def generate_evm_wallet(self, idx: int, private_key: str):
        try:
            keypair = Account.from_key(private_key)
            address = keypair.address
            self.accounts[idx]["keypair"] = keypair
            self.accounts[idx]["address"] = address
            return True
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Generate EVM Wallet Failed {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
        
    def generate_signature(self, idx: int, req_data: dict):
        try:
            keypair = self.accounts[idx]["keypair"]

            message = req_data["message"]
            encoded_message = encode_defunct(text=message)
            signed_message = keypair.sign_message(encoded_message)
            signature = to_hex(signed_message.signature)

            return signature
        except Exception as e:
            raise Exception(f"Generate Req Payload Failed: {str(e)}")

    def generate_datetime(self):
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    
    def generate_nickname(self, min_length=8, max_length=10):
        vowels = "aeiou"
        consonants = "bcdfghjklmnpqrstvwxyz"
        patterns = [
            "CV", "CVC", "VC",
        ]

        target = random.randint(min_length, max_length)
        result = ""

        while len(result) < target:
            pattern = random.choice(patterns)

            for ch in pattern:
                if len(result) >= target:
                    break

                if ch == "C":
                    result += random.choice(consonants)
                else:
                    result += random.choice(vowels)

        result = result[:target]
        return result.capitalize()

    def decode_token(self, idx: int, type = "access"):
        try:
            if type == "refresh":
                token = self.accounts[idx]["refresh_token"]
            else:
                token = self.accounts[idx]["access_token"]

            header, payload, signature = token.split(".")
            decoded_payload = urlsafe_b64decode(payload + "==").decode("utf-8")
            parsed_payload = json.loads(decoded_payload)
            exp_time = parsed_payload["exp"]

            return exp_time
        except Exception as e:
            return None

    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None

    def print_question(self):
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run Without Proxy{Style.RESET_ALL}")
                proxy_choice = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip())

                if proxy_choice in [1, 2]:
                    proxy_type = (
                        "With" if proxy_choice == 1 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    self.USE_PROXY = True if proxy_choice == 1 else False
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

        if self.USE_PROXY:
            while True:
                rotate_proxy = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()
                if rotate_proxy in ["y", "n"]:
                    self.ROTATE_PROXY = True if rotate_proxy == "y" else False
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")
    
    def ensure_ok(self, response):
        if response.status_code >= 400:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
    
    async def check_connection(self, proxy_url=None):
        url = "https://api.ipify.org?format=json"

        try:
            scraper = self.create_scraper(proxy_url)
            response = scraper.get(url, timeout=30)
            self.ensure_ok(response)
            return True
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
        
        return None

    async def solve_turnstile(self, retries=5):
        self.log(f"{Fore.CYAN+Style.BRIGHT}Captcha :{Style.RESET_ALL}")
        
        for attempt in range(retries):
            try:
                if self.CAPTCHA["captcha_key"] is None:
                    self.log(
                        f"{Fore.BLUE + Style.BRIGHT}   Status  : {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}Captcha Key Is None{Style.RESET_ALL}"
                    )
                    return None

                scraper = cloudscraper.create_scraper()
                submit_params = {
                    "key": self.CAPTCHA["captcha_key"],
                    "method": "turnstile",
                    "pageurl": self.CAPTCHA["page_url"],
                    "sitekey": self.CAPTCHA["site_key"]
                }
                submit_url = f"{self.CAPTCHA['solver_api']}/in.php"
                response = scraper.get(url=submit_url, params=submit_params, timeout=60)
                result = response.text.strip()

                if "|" not in result:
                    self.log(
                        f"{Fore.BLUE + Style.BRIGHT}   Message : {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}{result}{Style.RESET_ALL}"
                    )
                    await asyncio.sleep(5)
                    continue

                _, task_id = result.split("|", 1)
                self.log(
                    f"{Fore.BLUE + Style.BRIGHT}   Task Id : {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{task_id}{Style.RESET_ALL}"
                )

                for _ in range(30):
                    poll_params = {
                        "key": self.CAPTCHA["captcha_key"],
                        "id": task_id,
                        "action": "get"
                    }
                    poll_url = f"{self.CAPTCHA['solver_api']}/res.php"
                    poll_response = scraper.get(url=poll_url, params=poll_params, timeout=60)
                    poll_result = poll_response.text.strip()

                    if "NOT_READY" not in poll_result and "PROCESSING" not in poll_result:
                        if "|" in poll_result:
                            turnstile_token = poll_result.split("|", 1)[1]
                            self.log(
                                f"{Fore.BLUE + Style.BRIGHT}   Status  : {Style.RESET_ALL}"
                                f"{Fore.GREEN + Style.BRIGHT}Turnstile Solved Successfully{Style.RESET_ALL}"
                            )
                            return turnstile_token
                        else:
                            self.log(
                                f"{Fore.BLUE + Style.BRIGHT}   Message : {Style.RESET_ALL}"
                                f"{Fore.YELLOW + Style.BRIGHT}{poll_result}{Style.RESET_ALL}"
                            )
                            break
                    else:
                        self.log(
                            f"{Fore.BLUE + Style.BRIGHT}   Message : {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}Captcha Not Ready{Style.RESET_ALL}"
                        )
                        await asyncio.sleep(30)
                        continue

            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.BLUE + Style.BRIGHT}   Status  : {Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT}Trunstile Not Solved{Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT}{str(e)}{Style.RESET_ALL}"
                )
                return None
    
    async def login_request(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/user-auth/wallet/login-request"
        
        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                params = {
                    "strategy": "ETHEREUM_SIGNATURE",
                    "address": self.accounts[idx]["address"]
                }

                scraper = self.create_scraper(proxy_url)
                response = scraper.get(url, headers=headers, params=params, timeout=60)
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Login   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Message {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def auth_login(self, idx: int, req_data: dict, turnstile_token: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/user-auth/login"
        
        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["X-Recaptcha-Token"] = turnstile_token
                params = {
                    "strategy": "ETHEREUM_SIGNATURE",
                    "address": self.accounts[idx]["address"],
                    "message": req_data["message"],
                    "token": req_data["token"],
                    "signature": self.generate_signature(idx, req_data)
                }

                scraper = self.create_scraper(proxy_url)
                response = scraper.get(url, headers=headers, params=params, timeout=60)
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Login   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def auth_refresh(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/user-auth/refresh-tokens"
        
        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["X-Refresh-Token"] = self.accounts[idx]["refresh_token"]

                scraper = self.create_scraper(proxy_url)
                response = scraper.get(url, headers=headers, timeout=60)
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Refresh :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def set_invite(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/user/set-inviter/{self.REF_CODE}"
        
        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"

                scraper = self.create_scraper(proxy_url)
                response = scraper.post(url, headers=headers, timeout=60)
                if response.status_code == 500: return False
                self.ensure_ok(response)
                return True
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Invite  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Set {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def set_nickname(self, idx: int, nickname: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/user/set-nickname"
        
        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"
                params = {
                    "nickname": nickname
                }

                scraper = self.create_scraper(proxy_url)
                response = scraper.post(url, headers=headers, params=params, timeout=60)
                self.ensure_ok(response)
                return True
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Nickname:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Set {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def scoreboard_me(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/scoreboard/me"
        
        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"

                scraper = self.create_scraper(proxy_url)
                response = scraper.get(url, headers=headers, timeout=60)
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Points  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Data {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def daily_info(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/daily-rewards/today-info"
        
        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"

                scraper = self.create_scraper(proxy_url)
                response = scraper.get(url, headers=headers, timeout=60)
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Info {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def claim_daily(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/daily-rewards/claim"
        
        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"

                scraper = self.create_scraper(proxy_url)
                response = scraper.post(url, headers=headers, timeout=60)
                self.ensure_ok(response)
                return True
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Claim {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def missions_list(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/missions"
        
        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"
                params = {
                    "filter[progress]": "true",
                    "filter[rewards]": "true",
                    "filter[completedPercent]": "true",
                    "filter[hidden]": "false",
                    "filter[target]": "WEB",
                    "filter[date]": self.generate_datetime(),
                    "filter[grouped]": "true",
                    "filter[status]": "AVAILABLE",
                    "filter[excludeCategories]": "LEARNING_ONBOARDING"
                }

                scraper = self.create_scraper(proxy_url)
                response = scraper.get(url, headers=headers, params=params, timeout=60)
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Missions:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Data {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def missions_activity(self, idx: int, mission_id: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/mission-activity/{mission_id}"
        
        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"

                scraper = self.create_scraper(proxy_url)
                response = scraper.post(url, headers=headers, timeout=60)
                self.ensure_ok(response)
                return True
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Start :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def missions_quiz_activity(self, idx: int, mission_id: str, metadata: dict, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/mission-activity/{mission_id}"
        
        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"
                headers["Content-Type"] = "application/json"
                payload = {
                    "missionAnswer": json.dumps({
                        "type": "quiz",
                        "passScore": metadata["quizPassScore"],
                        "answers": [
                            {
                                "questionId": question["id"],
                                "selectedOption": question["correctOption"]
                            }
                            for question in metadata["quizQuestions"]
                        ]
                    }, separators=(",", ":"))
                }

                scraper = self.create_scraper(proxy_url)
                response = scraper.post(url, headers=headers, json=payload, timeout=60)
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Start :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def missions_reward(self, idx: int, mission_id: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/mission-reward/{mission_id}"
        
        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"

                scraper = self.create_scraper(proxy_url)
                response = scraper.post(url, headers=headers, timeout=60)
                self.ensure_ok(response)
                return True
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Claim :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def process_check_connection(self, idx: int, proxy_url=None):
        if not self.USE_PROXY:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} No Proxy {Style.RESET_ALL}"
            )
            return True

        while True:
            if self.USE_PROXY:
                proxy_url = self.get_next_proxy_for_account(idx)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.display_proxy(proxy_url)} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy_url)
            if is_valid: return True

            if self.ROTATE_PROXY:
                proxy_url = self.rotate_proxy_for_account(idx)
                await asyncio.sleep(1)
                continue

            return False
    
    async def process_user_login(self, idx: int, proxy_url=None):
        is_valid = await self.process_check_connection(idx, proxy_url)
        if not is_valid: return False

        if int(time.time()) > self.accounts[idx].get("access_exp_time", 0):

            if self.USE_PROXY:
                proxy_url = self.get_next_proxy_for_account(idx)

            if int(time.time()) > self.accounts[idx].get("refresh_exp_time", 0):

                request = await self.login_request(idx, proxy_url)
                if not request: return False

                turnstile_token = await self.solve_turnstile()
                if not turnstile_token: return False

                login = await self.auth_login(idx, request, turnstile_token, proxy_url)
                if not login: return False

                self.accounts[idx]["access_token"] = login.get("tokens", {}).get("access_token")
                self.accounts[idx]["access_exp_time"] = self.decode_token(idx)
                self.accounts[idx]["refresh_token"] = login.get("tokens", {}).get("refresh_token")
                self.accounts[idx]["refresh_exp_time"] = self.decode_token(idx, "refresh")

                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Login   :{Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT} Success {Style.RESET_ALL}"
                )

            else:
                refresh = await self.auth_refresh(idx, proxy_url)
                if not refresh: return False

                self.accounts[idx]["access_token"] = refresh.get("tokens", {}).get("access_token")
                self.accounts[idx]["access_exp_time"] = self.decode_token(idx)
                self.accounts[idx]["refresh_token"] = refresh.get("tokens", {}).get("refresh_token")
                self.accounts[idx]["refresh_exp_time"] = self.decode_token(idx, "refresh")

                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Refresh :{Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT} Success {Style.RESET_ALL}"
                )

        return True

    async def process_accounts(self, idx: int, proxy_url=None):
        logined = await self.process_user_login(idx, proxy_url)
        if not logined: return False

        if self.USE_PROXY:
            proxy_url = self.get_next_proxy_for_account(idx)

        scoreboard = await self.scoreboard_me(idx, proxy_url)
        if scoreboard:
            nickname = scoreboard.get("user", {}).get("nickname")
            if nickname is None:
                nickname = self.generate_nickname()
                if await self.set_nickname(idx, nickname, proxy_url):
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}Nickname:{Style.RESET_ALL}"
                        f"{Fore.GREEN + Style.BRIGHT} Set {Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT}[{nickname}]{Style.RESET_ALL}"
                    )
            else:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Nickname:{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} {nickname} {Style.RESET_ALL}"
                )

            points = scoreboard.get("balance")
            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Points  :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {int(float(points))} {Style.RESET_ALL}"
            )

            rank = scoreboard.get("rank")
            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Rank    :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} #{rank} {Style.RESET_ALL}"
            )

            role = scoreboard.get("user", {}).get("progressionRole")
            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Role    :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {role} {Style.RESET_ALL}"
            )

            inviter_id = scoreboard.get("user", {}).get("inviterId")
            tg_profiles = scoreboard.get("user", {}).get("telegramProfiles", [])
            
            if inviter_id is None and tg_profiles:
                await self.set_invite(idx, proxy_url)

        daily = await self.daily_info(idx, proxy_url)
        if daily:
            claimed = daily.get("todayClaimed")
            reward = daily.get("allowedReward")

            if claimed:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} Already Claimed {Style.RESET_ALL}"
                )
            else:
                claim = await self.claim_daily(idx, proxy_url)
                if claim:
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                        f"{Fore.GREEN + Style.BRIGHT} Claimed {Style.RESET_ALL}"
                        f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT} Reward: {Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT}{reward} Points{Style.RESET_ALL}"
                    )

        missions_list = await self.missions_list(idx, proxy_url)
        if missions_list:
            missions = missions_list.get("data", [])

            if not missions:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Missions:{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} No Available Missions{Style.RESET_ALL}"
                )
            else:
                self.log(f"{Fore.CYAN + Style.BRIGHT}Missions:{Style.RESET_ALL}")

                for mission in missions:
                    title = mission.get("label")
                    mission_id = mission.get("id")
                    type = mission.get("type")
                    progress = mission.get("progress")
                    reward = mission.get("reward")

                    self.log(
                        f"{Fore.BLUE + Style.BRIGHT} ● {Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT}{title}{Style.RESET_ALL}"
                    )

                    if progress == "0":
                        if type == "CONNECT_TELEGRAM_BOT":
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}   Start :{Style.RESET_ALL}"
                                f"{Fore.YELLOW+Style.BRIGHT} Must Manual {Style.RESET_ALL}"
                            )
                            continue

                        if type in [
                            "ACTIVITY_STREAK_3_DAY",
                            "ACTIVITY_STREAK_5_DAY",
                            "ACTIVITY_STREAK_7_DAY",
                            "INVITE_REAL_USER"
                        ]:
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}   Claim :{Style.RESET_ALL}"
                                f"{Fore.YELLOW+Style.BRIGHT} Not Eligible {Style.RESET_ALL}"
                            )
                            continue

                        if type == "QUESTION_MARKING":
                            metadata = mission.get("metadata")

                            start_quiz = await self.missions_quiz_activity(idx, mission_id, metadata, proxy_url)
                            if start_quiz.get("success"):
                                self.log(
                                    f"{Fore.CYAN+Style.BRIGHT}   Start :{Style.RESET_ALL}"
                                    f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
                                )
                            else:
                                self.log(
                                    f"{Fore.CYAN+Style.BRIGHT}   Start :{Style.RESET_ALL}"
                                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                                )
                                continue

                        else:
                            if not await self.missions_activity(idx, mission_id, proxy_url): continue
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}   Start :{Style.RESET_ALL}"
                                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
                            )

                        if not await self.missions_reward(idx, mission_id, proxy_url): continue
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}   Claim :{Style.RESET_ALL}"
                            f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
                        )
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}   Reward:{Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT} {int(float(reward))} Points {Style.RESET_ALL}"
                        )

                    elif progress == "1":
                        if not await self.missions_reward(idx, mission_id, proxy_url): continue
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}   Claim :{Style.RESET_ALL}"
                            f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
                        )
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}   Reward:{Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT} {int(float(reward))} Points {Style.RESET_ALL}"
                        )

                    else:
                        if type == "INVITE_REAL_USER":
                            amount = mission.get("amount")

                            if int(float(progress)) >= int(float(amount)):
                                if not await self.missions_reward(idx, mission_id, proxy_url): continue
                                self.log(
                                    f"{Fore.CYAN+Style.BRIGHT}   Claim :{Style.RESET_ALL}"
                                    f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
                                )
                                self.log(
                                    f"{Fore.CYAN+Style.BRIGHT}   Reward:{Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} {int(float(reward))} Points {Style.RESET_ALL}"
                                )
                            else:
                                self.log(
                                    f"{Fore.CYAN+Style.BRIGHT}   Claim :{Style.RESET_ALL}"
                                    f"{Fore.YELLOW+Style.BRIGHT} Not Eligible {Style.RESET_ALL}"
                                )

                        else:
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}   Start :{Style.RESET_ALL}"
                                f"{Fore.RED+Style.BRIGHT} Must Manual {Style.RESET_ALL}"
                            )

    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                print(f"{Fore.RED+Style.BRIGHT}No Accounts Loaded.{Style.RESET_ALL}") 
                return

            self.load_captcha_key()
            self.load_user_agents()
            self.print_question()

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if self.USE_PROXY: self.load_proxies()

                separator = "=" * 25
                for idx, private_key in enumerate(accounts, start=1):
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {idx} {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {len(accounts)} {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                    )
                
                    if idx not in self.accounts:
                        ua_index = (idx - 1) % len(self.user_agents) if self.user_agents else 0
                        self.accounts[idx] = {
                            "user_agent": self.user_agents[ua_index]
                        }
                
                    wallet = self.generate_evm_wallet(idx, private_key)
                    if not wallet: continue
                
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Address :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {self.mask_account(self.accounts[idx]['address'])} {Style.RESET_ALL}"
                    )

                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}UA      :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {self.accounts[idx]['user_agent']} {Style.RESET_ALL}"
                    )
                
                    await self.process_accounts(idx)
                    await asyncio.sleep(random.uniform(2.0, 3.0))
                
                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*60)
                
                next_run = self.get_next_run_time(anchor_minute=1)
                
                while True:
                    now = datetime.now(timezone.utc)
                    remaining = (next_run - now).total_seconds()
                
                    if remaining <= 0:
                        break
                
                    formatted_time = self.format_seconds(remaining)
                
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed...{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    await asyncio.sleep(1)

        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = TastyCo()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] TastyCo - BOT{Style.RESET_ALL}                                       "                              
        )
        sys.exit(0)