from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_utils import to_hex
from eth_account import Account
from eth_account.messages import encode_defunct
from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    BasicAuth
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from eth_account import Account
from datetime import datetime
from colorama import *
import asyncio, random, secrets, json, re, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class X1:
    def __init__(self) -> None:
        self.BASE_API = "https://tapi.kod.af"
        self.RPC_URL = "https://maculatus-rpc.x1eco.com/"
        self.EXPLORER = "https://maculatus-scan.x1eco.com/tx/"
        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.access_tokens = {}
        self.auto_transfer = False
        self.transfer_count = 0
        self.transfer_amount = 0
        self.min_delay = 0
        self.max_delay = 0

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}X1 EcoChain {Fore.BLUE + Style.BRIGHT}Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self):
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
        schemes = ["http://", "https://", "socks4://", "socks5://"]
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
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")
        
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address

            return address
        except Exception as e:
            return None
        
    def generate_random_recepient(self):
        try:
            private_key_bytes = secrets.token_bytes(32)
            private_key_hex = to_hex(private_key_bytes)
            account = Account.from_key(private_key_hex)
            recepient = account.address
            
            return recepient
        except Exception as e:
            return None
    
    def generate_signature(self, account: str):
        try:
            message = f"X1 Testnet Auth"
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=account)
            signature = to_hex(signed_message.signature)

            return signature
        except Exception as e:
            raise Exception(f"Generate Siganture Failed: {str(e)}")
        
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None
        
    async def get_web3_with_check(self, address: str, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        if use_proxy and proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(self.RPC_URL, request_kwargs=request_kwargs))
                web3.eth.get_block_number()
                return web3
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                raise Exception(f"Failed to Connect to RPC: {str(e)}")
        
    async def get_token_balance(self, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            balance = web3.eth.get_balance(address)
            token_balance = balance / (10 ** 18)

            return token_balance
        except Exception as e:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
        
    async def send_raw_transaction_with_retries(self, account, web3, tx, retries=5):
        for attempt in range(retries):
            try:
                signed_tx = web3.eth.account.sign_transaction(tx, account)
                raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_hash = web3.to_hex(raw_tx)
                return tx_hash
            except TransactionNotFound:
                pass
            except Exception as e:
                self.log(
                    f"{Fore.BLUE + Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} [Attempt {attempt + 1}] Send TX Error: {str(e)} {Style.RESET_ALL}"
                )
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Hash Not Found After Maximum Retries")

    async def wait_for_receipt_with_retries(self, web3, tx_hash, retries=5):
        for attempt in range(retries):
            try:
                receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
                return receipt
            except TransactionNotFound:
                pass
            except Exception as e:
                self.log(
                    f"{Fore.BLUE + Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} [Attempt {attempt + 1}] Wait for Receipt Error: {str(e)} {Style.RESET_ALL}"
                )
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Receipt Not Found After Maximum Retries")

    async def perform_transfer(self, account: str, address: str, recepient: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            amount_to_wei = web3.to_wei(self.transfer_amount, "ether")

            max_priority_fee = web3.to_wei(1, "gwei")
            max_fee = max_priority_fee
            
            transfer_tx = {
                "from": web3.to_checksum_address(address),
                "to": web3.to_checksum_address(recepient),
                "value": amount_to_wei,
                "gas": 21000,
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": web3.eth.get_transaction_count(address, "pending"),
                "chainId": web3.eth.chain_id,
            }

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, transfer_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.BLUE + Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED + Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    async def print_timer(self):
        for remaining in range(random.randint(self.min_delay, self.max_delay), 0, -1):
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Wait For{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {remaining} {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Seconds For Next Tx...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)

    def print_transfer_question(self):
        while True:
            try:
                transfer_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Transfer Count -> {Style.RESET_ALL}").strip())
                if transfer_count > 0:
                    self.transfer_count = transfer_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Count must be greater than 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                transfer_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Transfer Amount -> {Style.RESET_ALL}").strip())
                if transfer_amount > 0:
                    self.transfer_amount = transfer_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Amount must be greater than 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

    def print_delay_question(self):
        while True:
            try:
                min_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Min Delay Each Tx -> {Style.RESET_ALL}").strip())
                if min_delay >= 0:
                    self.min_delay = min_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                max_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Max Delay Each Tx -> {Style.RESET_ALL}").strip())
                if max_delay >= min_delay:
                    self.max_delay = max_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= Min Delay.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

    def print_question(self):
        while True:
            auto_transfer = input(f"{Fore.BLUE + Style.BRIGHT}Auto Send X1T Tokens? [y/n] -> {Style.RESET_ALL}").strip()
            
            if auto_transfer in ["y", "n"]:
                auto_transfer = auto_transfer == "y"

                if auto_transfer:
                    self.print_transfer_question()
                    self.print_delay_question()

                self.auto_transfer = auto_transfer
                break
            else:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

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
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

        rotate_proxy = False
        if proxy_choice == 1:
            while True:
                rotate_proxy = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()

                if rotate_proxy in ["y", "n"]:
                    rotate_proxy = rotate_proxy == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return proxy_choice, rotate_proxy
    
    async def check_connection(self, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
        
        return None
    
    async def auth_signin(self, address: str, signature: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/signin"
        data = json.dumps({"signature": signature})
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Login Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def user_data(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/me"
        headers = {
            **self.HEADERS[address],
            "Authorization": self.access_tokens[address],
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to fetch user data {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def request_faucet(self, address: str, proxy_url=None, retries=5):
        url = f"https://nft-api.x1.one/testnet/faucet"
        params = {"address": address}
        headers = {
            **self.HEADERS[address],
            "Authorization": self.access_tokens[address],
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, params=params, proxy=proxy, proxy_auth=proxy_auth) as response:
                        if not response.ok:
                            resp_text = await response.text()
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}Faucet  :{Style.RESET_ALL}"
                                f"{Fore.YELLOW+Style.BRIGHT} {resp_text} {Style.RESET_ALL}"
                            )
                            return None
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Faucet  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to request faucet {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def quest_list(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/quests"
        headers = {
            **self.HEADERS[address],
            "Authorization": self.access_tokens[address],
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Quests  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to fetch available quests {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def claim_quest(self, address: str, quest_id: str, title: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/quests"
        params = {"quest_id": quest_id}
        headers = {
            **self.HEADERS[address],
            "Authorization": self.access_tokens[address],
            "Content-Length": "0",
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, params=params, proxy=proxy, proxy_auth=proxy_auth) as response:
                        if response.status == 400:
                            self.log(
                                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                f"{Fore.RED+Style.BRIGHT} Not Completed {Style.RESET_ALL}"
                            )
                            return None
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Not Completed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy)
            if not is_valid:
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(address)
                    await asyncio.sleep(1)
                    continue

                return False

            return True
        
    async def process_perform_transfer(self, account: str, address: str, recepient: str, use_proxy: bool):
        tx_hash, block_number = await self.perform_transfer(account, address, recepient, use_proxy)
        if tx_hash and block_number:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Block    :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Tx Hash  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Explorer :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.EXPLORER}{tx_hash} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )
    
    async def process_auth_login(self, account: str, address: str, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None

            signature = self.generate_signature(account)

            signin = await self.auth_signin(address, signature, proxy)
            if signin:
                self.access_tokens[address] = signin["token"]

                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT} Login Success {Style.RESET_ALL}"
                )
                return True

            return False

    async def process_accounts(self, account: str, address: str, use_proxy: bool, rotate_proxy: bool):
        logined = await self.process_auth_login(account, address, use_proxy, rotate_proxy)
        if logined:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None

            user = await self.user_data(address, proxy)
            if user:
                points = user.get("points")

                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Points  :{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} {points} {Style.RESET_ALL}"
                )

            faucet = await self.request_faucet(address, proxy)
            if faucet:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Faucet  :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} Requested Successfully {Style.RESET_ALL}"
                )

            if self.auto_transfer:
                self.log(f"{Fore.CYAN+Style.BRIGHT}Transfer:{Style.RESET_ALL}")
                for i in range(self.transfer_count):
                    self.log(
                        f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                        f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{self.transfer_count}{Style.RESET_ALL}                                   "
                    )

                    recepient = self.generate_random_recepient()
                    self.log(
                        f"{Fore.BLUE+Style.BRIGHT}   Recepient:{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {recepient} {Style.RESET_ALL}"
                    )

                    self.log(
                        f"{Fore.BLUE+Style.BRIGHT}   Amount   :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {self.transfer_amount} X1T {Style.RESET_ALL}"
                    )

                    balance = await self.get_token_balance(address, use_proxy)
                    self.log(
                        f"{Fore.BLUE+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {balance} X1T {Style.RESET_ALL}"
                    )

                    if balance is None:
                        self.log(
                            f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                            f"{Fore.YELLOW+Style.BRIGHT} Fetch X1T Token Balance Failed {Style.RESET_ALL}"
                        )
                        continue

                    if balance < self.transfer_amount:
                        self.log(
                            f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                            f"{Fore.YELLOW+Style.BRIGHT} Insufficient X1T Token Balance {Style.RESET_ALL}"
                        )
                        return

                    await self.process_perform_transfer(account, address, recepient, use_proxy)
                    await self.print_timer()

            quests = await self.quest_list(address, proxy)
            if quests:
                self.log(f"{Fore.CYAN + Style.BRIGHT}Quests  :{Style.RESET_ALL}                                   ")

                for quest in quests:
                    quest_id = quest.get("id")
                    title = quest.get("title")
                    reward = quest.get("reward")
                    periodicity = quest.get("periodicity")
                    is_completed = quest.get("is_completed")
                    is_completed_today = quest.get("is_completed_today")

                    if periodicity == "one_time":
                        if is_completed:
                            self.log(
                                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                f"{Fore.YELLOW+Style.BRIGHT} Already Completed {Style.RESET_ALL}"
                            )
                            continue

                        claim = await self.claim_quest(address, quest_id, title, proxy)
                        if claim:
                            self.log(
                                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                f"{Fore.GREEN+Style.BRIGHT} Completed {Style.RESET_ALL}"
                                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                                f"{Fore.CYAN+Style.BRIGHT} Reward: {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{reward} Points{Style.RESET_ALL}"
                            )

                    elif periodicity == "daily":
                        if is_completed_today:
                            self.log(
                                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                f"{Fore.YELLOW+Style.BRIGHT} Already Completed Today {Style.RESET_ALL}"
                            )
                            continue

                        claim = await self.claim_quest(address, quest_id, title, proxy)
                        if claim:
                            self.log(
                                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                f"{Fore.GREEN+Style.BRIGHT} Completed {Style.RESET_ALL}"
                                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                                f"{Fore.CYAN+Style.BRIGHT} Reward: {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{reward} Points{Style.RESET_ALL}"
                            )
            
    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            proxy_choice, rotate_proxy = self.print_question()

            while True:
                use_proxy = True if proxy_choice == 1 else False

                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies()

                separator = "=" * 25
                for account in accounts:
                    if account:
                        address = self.generate_address(account)
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )

                        if not address:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Status  :{Style.RESET_ALL}"
                                f"{Fore.RED + Style.BRIGHT} Invalid Private Key or Library Version Not Supported {Style.RESET_ALL}"
                            )
                            continue

                        self.HEADERS[address] = {
                            "Accept": "*/*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://testnet.x1ecochain.com",
                            "Referer": "https://testnet.x1ecochain.com/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "cross-site",
                            "User-Agent": FakeUserAgent().random
                        }
                        
                        await self.process_accounts(account, address, use_proxy, rotate_proxy)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                
                delay = 24 * 60 * 60
                while delay > 0:
                    formatted_time = self.format_seconds(delay)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed...{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    await asyncio.sleep(1)
                    delay -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = X1()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] X1 EcoChain - BOT{Style.RESET_ALL}                                       "                              
        )