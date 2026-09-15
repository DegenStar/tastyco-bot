import argparse
import asyncio
import json
import math
import os
import random
import re
import sys
import time
from base64 import urlsafe_b64decode
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cloudscraper
from colorama import Fore, Style, just_fix_windows_console
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils.conversions import to_hex


class HTTPError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__(f"HTTP {status}")


class NetworkError(RuntimeError):
    pass


class TastyCo:
    def __init__(self, config_dir=None) -> None:
        self.config_dir = (
            Path(config_dir) if config_dir else Path(__file__).resolve().parent / "config"
        )
        self.BASE_API = "https://api.tastyco.io"

        self.CAPTCHA = {
            "page_url": "https://app.tastyco.io/",
            "solver_api": "https://sctg.xyz",
            "site_key": "0x4AAAAAAET4O64ulvE1G0s4",
            "captcha_key": None,
        }

        self.REF_CODE = os.environ.get("TASTYCO_REF_CODE", "").strip()

        self.USE_PROXY = False
        self.ROTATE_PROXY = False

        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.accounts = {}

        self.user_agents = []

    def load_user_agents(self):
        self.user_agents = []
        filename = self.config_dir / "useragent.txt"
        try:
            with open(filename, "r", encoding="utf-8") as file:
                lines = file.readlines()

            for line in lines:
                line = line.strip()
                if line.startswith("Mozilla/5.0") and line not in self.user_agents:
                    self.user_agents.append(line)

            if not self.user_agents:
                self.log(
                    f"{Fore.RED + Style.BRIGHT}No User Agents Found In {filename}.{Style.RESET_ALL}"
                )
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}UserAgents Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.user_agents)}{Style.RESET_ALL}"
            )
        except FileNotFoundError:
            self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
            self.user_agents = []

    def clear_terminal(self):
        if sys.stdout.isatty():
            os.system("cls" if os.name == "nt" else "clear")

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True,
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
        filename = self.config_dir / "accounts.txt"
        try:
            with open(filename, "r", encoding="utf-8") as file:
                accounts = [line.strip() for line in file if line.strip()]
            return accounts
        except Exception as e:
            print(
                f"{Fore.RED + Style.BRIGHT}Failed To Load Accounts: {self.error_message(e)}{Style.RESET_ALL}"
            )
            return None

    def load_captcha_key(self):
        env_key = os.environ.get("TASTYCO_CAPTCHA_KEY", "").strip()
        if env_key:
            self.CAPTCHA["captcha_key"] = env_key
            return env_key
        filename = self.config_dir / "sctg.txt"
        try:
            with open(filename, "r", encoding="utf-8") as file:
                captcha_key = file.readline().strip()
            self.CAPTCHA["captcha_key"] = captcha_key or None
            return captcha_key
        except FileNotFoundError:
            self.log(f"{Fore.RED}File {filename} Not Found.{Style.RESET_ALL}")
            return None

    def load_proxies(self):
        filename = self.config_dir / "proxy.txt"
        self.proxies = []
        self.account_proxies.clear()
        self.proxy_index = 0
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                return
            with open(filename, "r", encoding="utf-8") as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]

            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )

        except Exception as e:
            self.log(
                f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {self.error_message(e)}{Style.RESET_ALL}"
            )
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
        return {"http": proxy_url, "https": proxy_url}

    def create_scraper(self, proxy_url=None):
        scraper = cloudscraper.create_scraper()
        # Explicit CLI proxy mode must not inherit ambient HTTP_PROXY settings.
        scraper.trust_env = False
        proxies = self.build_proxy_config(proxy_url)
        if proxies:
            scraper.proxies.update(proxies)
        return scraper

    async def request(self, method, url, proxy_url=None, **kwargs):
        """Run blocking HTTP in a worker; close every session and redact errors."""

        def send():
            try:
                with self.create_scraper(proxy_url) as scraper:
                    return scraper.request(method, url, **kwargs)
            except Exception as exc:
                # Requests exceptions may embed query tokens or proxy passwords.
                raise NetworkError(f"Network request failed ({type(exc).__name__})") from None

        return await asyncio.to_thread(send)

    @staticmethod
    def should_retry(error):
        return isinstance(error, NetworkError) or (
            isinstance(error, HTTPError) and (error.status in (408, 429) or error.status >= 500)
        )

    @staticmethod
    def error_message(error):
        if isinstance(error, (HTTPError, NetworkError)):
            return str(error)
        return type(error).__name__

    def display_proxy(self, proxy_url=None):
        if not proxy_url:
            return "No Proxy"

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
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Origin": "https://app.tastyco.io",
            "Pragma": "no-cache",
            "Referer": "https://app.tastyco.io/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": self.accounts[idx]["user_agent"],
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
                f"{Fore.CYAN + Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED + Style.BRIGHT} Generate EVM Wallet Failed {Style.RESET_ALL}"
                f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW + Style.BRIGHT} Invalid private key ({type(e).__name__}) {Style.RESET_ALL}"
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
            raise ValueError(f"Signing failed ({type(e).__name__})") from None

    def generate_datetime(self):
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def generate_nickname(self, min_length=8, max_length=10):
        vowels = "aeiou"
        consonants = "bcdfghjklmnpqrstvwxyz"
        patterns = [
            "CV",
            "CVC",
            "VC",
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

    def decode_token(self, idx: int, type="access"):
        try:
            if type == "refresh":
                token = self.accounts[idx]["refresh_token"]
            else:
                token = self.accounts[idx]["access_token"]

            header, payload, signature = token.split(".")
            decoded_payload = urlsafe_b64decode(payload + "=" * (-len(payload) % 4)).decode("utf-8")
            parsed_payload = json.loads(decoded_payload)
            exp_time = parsed_payload["exp"]
            if isinstance(exp_time, bool) or not isinstance(exp_time, (int, float)):
                return 0
            if not math.isfinite(exp_time) or exp_time <= 0:
                return 0

            return exp_time
        except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
            return 0

    def store_tokens(self, idx, response):
        tokens = response.get("tokens") if isinstance(response, dict) else None
        if not isinstance(tokens, dict):
            return False
        self.accounts[idx]["access_token"] = tokens.get("access_token")
        self.accounts[idx]["refresh_token"] = tokens.get("refresh_token")
        self.accounts[idx]["access_exp_time"] = self.decode_token(idx)
        self.accounts[idx]["refresh_exp_time"] = self.decode_token(idx, "refresh")
        valid = self.accounts[idx]["access_exp_time"] > time.time() + 60
        if not valid:
            self.log("Invalid or expired access token received.")
        return valid

    def mask_account(self, account):
        try:
            mask_account = account[:6] + "*" * 6 + account[-6:]
            return mask_account
        except Exception:
            return None

    def print_question(self):
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run Without Proxy{Style.RESET_ALL}")
                proxy_choice = int(
                    input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip()
                )

                if proxy_choice in [1, 2]:
                    proxy_type = "With" if proxy_choice == 1 else "Without"
                    print(
                        f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}"
                    )
                    self.USE_PROXY = True if proxy_choice == 1 else False
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(
                    f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}"
                )

        if self.USE_PROXY:
            while True:
                rotate_proxy = input(
                    f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}"
                ).strip()
                if rotate_proxy in ["y", "n"]:
                    self.ROTATE_PROXY = True if rotate_proxy == "y" else False
                    break
                else:
                    print(
                        f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}"
                    )

    def ensure_ok(self, response):
        if response.status_code >= 400:
            raise HTTPError(response.status_code)

    async def check_connection(self, proxy_url=None):
        url = "https://api.ipify.org?format=json"

        try:
            response = await self.request("GET", url, proxy_url=proxy_url, timeout=30)
            self.ensure_ok(response)
            return True
        except Exception as e:
            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED + Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
            )

        return None

    async def solve_turnstile(self, retries=5):
        self.log(f"{Fore.CYAN + Style.BRIGHT}Captcha :{Style.RESET_ALL}")

        for attempt in range(retries):
            try:
                if self.CAPTCHA["captcha_key"] is None:
                    self.log(
                        f"{Fore.BLUE + Style.BRIGHT}   Status  : {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}Captcha Key Is None{Style.RESET_ALL}"
                    )
                    return None

                submit_params = {
                    "key": self.CAPTCHA["captcha_key"],
                    "method": "turnstile",
                    "pageurl": self.CAPTCHA["page_url"],
                    "sitekey": self.CAPTCHA["site_key"],
                }
                submit_url = f"{self.CAPTCHA['solver_api']}/in.php"
                response = await self.request("GET", submit_url, params=submit_params, timeout=60)
                self.ensure_ok(response)
                result = response.text.strip()

                if not result.startswith("OK|") or not result[3:]:
                    self.log(
                        f"{Fore.BLUE + Style.BRIGHT}   Message : {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}Solver submission failed{Style.RESET_ALL}"
                    )
                    await asyncio.sleep(5)
                    continue

                _, task_id = result.split("|", 1)
                self.log(
                    f"{Fore.BLUE + Style.BRIGHT}   Task Id : {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}[created]{Style.RESET_ALL}"
                )

                for _ in range(30):
                    poll_params = {
                        "key": self.CAPTCHA["captcha_key"],
                        "id": task_id,
                        "action": "get",
                    }
                    poll_url = f"{self.CAPTCHA['solver_api']}/res.php"
                    poll_response = await self.request(
                        "GET", poll_url, params=poll_params, timeout=60
                    )
                    self.ensure_ok(poll_response)
                    poll_result = poll_response.text.strip()

                    if "NOT_READY" not in poll_result and "PROCESSING" not in poll_result:
                        if poll_result.startswith("OK|") and poll_result[3:]:
                            turnstile_token = poll_result.split("|", 1)[1]
                            self.log(
                                f"{Fore.BLUE + Style.BRIGHT}   Status  : {Style.RESET_ALL}"
                                f"{Fore.GREEN + Style.BRIGHT}Turnstile Solved Successfully{Style.RESET_ALL}"
                            )
                            return turnstile_token
                        else:
                            self.log(
                                f"{Fore.BLUE + Style.BRIGHT}   Message : {Style.RESET_ALL}"
                                f"{Fore.YELLOW + Style.BRIGHT}Solver returned an error{Style.RESET_ALL}"
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
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.BLUE + Style.BRIGHT}   Status  : {Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT}Trunstile Not Solved{Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT}{self.error_message(e)}{Style.RESET_ALL}"
                )
                return None

    async def login_request(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/user-auth/wallet/login-request"

        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                params = {
                    "strategy": "ETHEREUM_SIGNATURE",
                    "address": self.accounts[idx]["address"],
                }

                response = await self.request(
                    "GET", url, proxy_url=proxy_url, headers=headers, params=params, timeout=60
                )
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Login   :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Failed to Fetch Message {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
                )
                return None

        return None

    async def auth_login(
        self, idx: int, req_data: dict, turnstile_token: str, proxy_url=None, retries=5
    ):
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
                    "signature": self.generate_signature(idx, req_data),
                }

                response = await self.request(
                    "GET", url, proxy_url=proxy_url, headers=headers, params=params, timeout=60
                )
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Login   :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
                )
                return None

        return None

    async def auth_refresh(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/user-auth/refresh-tokens"

        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["X-Refresh-Token"] = self.accounts[idx]["refresh_token"]

                response = await self.request(
                    "GET", url, proxy_url=proxy_url, headers=headers, timeout=60
                )
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Refresh :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
                )
                return None

        return None

    async def set_invite(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/user/set-inviter/{self.REF_CODE}"

        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"

                response = await self.request(
                    "POST", url, proxy_url=proxy_url, headers=headers, timeout=60
                )
                self.ensure_ok(response)
                return True
            except Exception as e:
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Invite  :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Failed to Set {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
                )
                return None

        return None

    async def set_nickname(self, idx: int, nickname: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/user/set-nickname"

        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"
                params = {"nickname": nickname}

                response = await self.request(
                    "POST", url, proxy_url=proxy_url, headers=headers, params=params, timeout=60
                )
                self.ensure_ok(response)
                return True
            except Exception as e:
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Nickname:{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Failed to Set {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
                )
                return None

        return None

    async def scoreboard_me(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/scoreboard/me"

        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"

                response = await self.request(
                    "GET", url, proxy_url=proxy_url, headers=headers, timeout=60
                )
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Points  :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Failed to Fetch Data {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
                )
                return None

        return None

    async def daily_info(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/daily-rewards/today-info"

        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"

                response = await self.request(
                    "GET", url, proxy_url=proxy_url, headers=headers, timeout=60
                )
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Failed to Fetch Info {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
                )
                return None

        return None

    async def claim_daily(self, idx: int, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/daily-rewards/claim"

        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"

                response = await self.request(
                    "POST", url, proxy_url=proxy_url, headers=headers, timeout=60
                )
                self.ensure_ok(response)
                return True
            except Exception as e:
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Failed to Claim {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
                )
                return None

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
                    "filter[excludeCategories]": "LEARNING_ONBOARDING",
                }

                response = await self.request(
                    "GET", url, proxy_url=proxy_url, headers=headers, params=params, timeout=60
                )
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Missions:{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Failed to Fetch Data {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
                )
                return None

        return None

    async def missions_activity(self, idx: int, mission_id: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/mission-activity/{mission_id}"

        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"

                response = await self.request(
                    "POST", url, proxy_url=proxy_url, headers=headers, timeout=60
                )
                self.ensure_ok(response)
                return True
            except Exception as e:
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}   Start :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
                )
                return None

        return None

    async def missions_quiz_activity(
        self, idx: int, mission_id: str, metadata: dict, proxy_url=None, retries=5
    ):
        url = f"{self.BASE_API}/mission-activity/{mission_id}"

        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"
                headers["Content-Type"] = "application/json"
                payload = {
                    "missionAnswer": json.dumps(
                        {
                            "type": "quiz",
                            "passScore": metadata["quizPassScore"],
                            "answers": [
                                {
                                    "questionId": question["id"],
                                    "selectedOption": question["correctOption"],
                                }
                                for question in metadata["quizQuestions"]
                            ],
                        },
                        separators=(",", ":"),
                    )
                }

                response = await self.request(
                    "POST", url, proxy_url=proxy_url, headers=headers, json=payload, timeout=60
                )
                self.ensure_ok(response)
                return response.json()
            except Exception as e:
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}   Start :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
                )
                return None

        return None

    async def missions_reward(self, idx: int, mission_id: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/mission-reward/{mission_id}"

        for attempt in range(retries):
            try:
                headers = self.initialize_headers(idx)
                headers["Authorization"] = f"Bearer {self.accounts[idx]['access_token']}"

                response = await self.request(
                    "POST", url, proxy_url=proxy_url, headers=headers, timeout=60
                )
                self.ensure_ok(response)
                return True
            except Exception as e:
                if self.should_retry(e) and attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}   Claim :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} {self.error_message(e)} {Style.RESET_ALL}"
                )
                return None

        return None

    async def process_check_connection(self, idx: int, proxy_url=None):
        if not self.USE_PROXY:
            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} No Proxy {Style.RESET_ALL}"
            )
            return True

        if not self.proxies:
            self.log("Proxy mode enabled but no proxies loaded; skipping account.")
            return False

        # Test each distinct proxy at most once; never fall back to direct traffic.
        proxy_url = self.get_next_proxy_for_account(idx)
        candidates = [proxy_url]
        if self.ROTATE_PROXY:
            candidates.extend(self.check_proxy_schemes(proxy) for proxy in self.proxies)
        for proxy_url in dict.fromkeys(candidates):
            self.account_proxies[idx] = proxy_url

            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {self.display_proxy(proxy_url)} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy_url)
            if is_valid:
                return True

        return False

    async def process_user_login(self, idx: int, proxy_url=None):
        if not await self.process_check_connection(idx, proxy_url):
            return False
        if time.time() + 60 < (self.accounts[idx].get("access_exp_time") or 0):
            return True
        if self.USE_PROXY:
            proxy_url = self.get_next_proxy_for_account(idx)

        if time.time() + 60 < (self.accounts[idx].get("refresh_exp_time") or 0):
            refresh = await self.auth_refresh(idx, proxy_url)
            if self.store_tokens(idx, refresh):
                self.log("Tokens refreshed.")
                return True
            # A rejected refresh token must not trap this account until expiry.
            self.accounts[idx]["refresh_exp_time"] = 0

        request = await self.login_request(idx, proxy_url)
        if not request:
            return False
        turnstile_token = await self.solve_turnstile()
        if not turnstile_token:
            return False
        login = await self.auth_login(idx, request, turnstile_token, proxy_url)
        if not self.store_tokens(idx, login):
            return False
        self.log("Login successful.")
        return True

    @staticmethod
    def number(value):
        if isinstance(value, bool):
            raise ValueError("Expected a number")
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("Expected a finite number")
        return result

    @classmethod
    def display_points(cls, value):
        try:
            return str(int(cls.number(value)))
        except (TypeError, ValueError, OverflowError):
            return "Unknown"

    async def process_mission(self, idx, mission, proxy_url=None):
        mission_id = mission["id"]
        mission_type = mission.get("type")
        progress = self.number(mission.get("progress"))
        self.log(f"Mission: {mission.get('label', mission_id)}")

        if mission_type == "INVITE_REAL_USER":
            # Invitation targets can exceed one; progress=1 is not always eligible.
            amount = self.number(mission.get("amount"))
            if amount <= 0 or progress < amount:
                self.log("Not eligible for invitation reward.")
                return True
        elif progress == 0:
            if mission_type in {
                "CONNECT_TELEGRAM_BOT",
                "ACTIVITY_STREAK_3_DAY",
                "ACTIVITY_STREAK_5_DAY",
                "ACTIVITY_STREAK_7_DAY",
            }:
                self.log("Manual action or further progress required.")
                return True
            if mission_type == "QUESTION_MARKING":
                result = await self.missions_quiz_activity(
                    idx, mission_id, mission.get("metadata"), proxy_url
                )
                if not isinstance(result, dict) or not result.get("success"):
                    self.log("Quiz activity failed.")
                    return False
            elif not await self.missions_activity(idx, mission_id, proxy_url):
                return False
        elif progress != 1:
            self.log("Manual action required.")
            return True

        if not await self.missions_reward(idx, mission_id, proxy_url):
            return False
        self.log(f"Reward claimed: {self.display_points(mission.get('reward'))} points")
        return True

    async def process_accounts(self, idx: int, proxy_url=None):
        if not await self.process_user_login(idx, proxy_url):
            return False
        if self.USE_PROXY:
            proxy_url = self.get_next_proxy_for_account(idx)

        success = True
        scoreboard = await self.scoreboard_me(idx, proxy_url)
        if isinstance(scoreboard, dict):
            user = scoreboard.get("user") or {}
            nickname = user.get("nickname")
            if nickname is None:
                nickname = self.generate_nickname()
                if not await self.set_nickname(idx, nickname, proxy_url):
                    success = False
            self.log(f"Nickname: {nickname}")
            self.log(f"Points: {self.display_points(scoreboard.get('balance'))}")
            self.log(f"Rank: {scoreboard.get('rank')}")
            self.log(f"Role: {user.get('progressionRole')}")
            if self.REF_CODE and user.get("inviterId") is None and user.get("telegramProfiles"):
                if not await self.set_invite(idx, proxy_url):
                    success = False
        else:
            success = False

        daily = await self.daily_info(idx, proxy_url)
        if not isinstance(daily, dict):
            success = False
        elif daily.get("todayClaimed") is True:
            self.log("Daily reward already claimed.")
        elif daily.get("todayClaimed") is False:
            if await self.claim_daily(idx, proxy_url):
                self.log(
                    f"Daily reward claimed: {self.display_points(daily.get('allowedReward'))} points"
                )
            else:
                success = False
        else:
            self.log("Invalid daily reward status.")
            success = False

        response = await self.missions_list(idx, proxy_url)
        missions = response.get("data") if isinstance(response, dict) else None
        if not isinstance(missions, list):
            return False
        if not missions:
            self.log("No available missions.")
        for mission in missions:
            try:
                if not await self.process_mission(idx, mission, proxy_url):
                    success = False
            except (KeyError, TypeError, ValueError, AttributeError) as exc:
                self.log(f"Invalid mission data ({type(exc).__name__}); skipping.")
                success = False
        return success

    async def main(self, *, once=False, use_proxy=None, rotate_proxy=False):
        accounts = self.load_accounts()
        if not accounts:
            self.log("No accounts loaded.")
            return 1
        if not self.load_captcha_key():
            self.log("A CAPTCHA API key is required.")
            return 1
        self.load_user_agents()
        if not self.user_agents:
            self.log("At least one valid User-Agent is required.")
            return 1

        if use_proxy is None:
            if not sys.stdin.isatty():
                self.log("Non-interactive runs require --proxy or --no-proxy.")
                return 1
            await asyncio.to_thread(self.print_question)
        else:
            self.USE_PROXY = use_proxy
            self.ROTATE_PROXY = rotate_proxy

        while True:
            self.clear_terminal()
            self.welcome()
            self.log(f"Accounts total: {len(accounts)}")
            if self.USE_PROXY:
                self.load_proxies()
                if not self.proxies:
                    self.log("Proxy mode requires a non-empty proxy.txt.")
                    return 1

            failed = False
            for idx, private_key in enumerate(accounts, start=1):
                self.log(f"Account {idx}/{len(accounts)}")
                if idx not in self.accounts:
                    self.accounts[idx] = {
                        "user_agent": self.user_agents[(idx - 1) % len(self.user_agents)]
                    }
                if not self.generate_evm_wallet(idx, private_key):
                    failed = True
                    continue
                self.log(f"Address: {self.mask_account(self.accounts[idx]['address'])}")
                try:
                    if await self.process_accounts(idx) is False:
                        failed = True
                except Exception as exc:
                    failed = True
                    # Do not print payloads or credentials from unexpected exceptions.
                    self.log(f"Account {idx} failed ({type(exc).__name__}); continuing.")
                if idx < len(accounts):
                    await asyncio.sleep(random.uniform(2.0, 3.0))

            if once:
                return int(failed)

            next_run = self.get_next_run_time(anchor_minute=1)
            self.log(f"Next run: {next_run.isoformat()}")
            while True:
                remaining = (next_run - datetime.now(timezone.utc)).total_seconds()
                if remaining <= 0:
                    break
                await asyncio.sleep(min(remaining, 60))


def cli(argv=None):
    parser = argparse.ArgumentParser(description="TastyCo account automation")
    parser.add_argument(
        "--config-dir", type=Path, help="Configuration directory (default: config/ next to bot.py)"
    )
    parser.add_argument("--once", action="store_true", help="Process accounts once and exit")
    proxy = parser.add_mutually_exclusive_group()
    proxy.add_argument("--proxy", dest="use_proxy", action="store_true", help="Require proxies")
    proxy.add_argument(
        "--no-proxy", dest="use_proxy", action="store_false", help="Use direct connections"
    )
    parser.set_defaults(use_proxy=None)
    parser.add_argument(
        "--rotate-proxy", action="store_true", help="Try other configured proxies on failure"
    )
    args = parser.parse_args(argv)
    if args.rotate_proxy and args.use_proxy is not True:
        parser.error("--rotate-proxy requires --proxy")

    just_fix_windows_console()
    bot = TastyCo(args.config_dir)
    try:
        # Read terminal input on the main thread so Ctrl+C can stop an idle prompt.
        if args.use_proxy is None and sys.stdin.isatty():
            bot.print_question()
            args.use_proxy = bot.USE_PROXY
            args.rotate_proxy = bot.ROTATE_PROXY
        return asyncio.run(
            bot.main(once=args.once, use_proxy=args.use_proxy, rotate_proxy=args.rotate_proxy)
        )
    except KeyboardInterrupt:
        print("\n[ EXIT ] TastyCo BOT")
        return 130
    except (OSError, EOFError) as exc:
        bot.log(f"Configuration/input error ({type(exc).__name__})")
        return 1


if __name__ == "__main__":
    sys.exit(cli())
