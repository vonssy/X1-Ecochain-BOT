from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    BasicAuth
)
from aiohttp_socks import ProxyConnector
from web3 import Web3, HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware
from web3.exceptions import TransactionNotFound
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_hex
from dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal, getcontext, ROUND_DOWN
from colorama import *
import asyncio, random, time, sys, re, os

load_dotenv()

getcontext().prec = 80

class X1:
    def __init__(self) -> None:
        self.API_URL = {
            "testnet": "https://testnet-api.x1eco.com",
            "nft": "https://nft-api.x1eco.com",
            "dex": "https://ms.kod.af",
            "rpc": "https://maculatus-rpc.x1eco.com/",
            "explorer": "https://maculatus-scan.x1eco.com/tx/",
        }

        self.SEND_AMOUNT = Decimal(os.getenv("SEND_AMOUNT") or "1")
        self.SWAP_AMOUNT = Decimal(os.getenv("SWAP_AMOUNT") or "1")

        self.CONTRACT_ADDRESS = {
            "WX1T": "0xe2ED17Ae5e68863E77899205a83A8f1E138c608f",
            "USDT": "0xd127BA1f0EfA2c5c7d9e6E7339DBafe2A6b1EAeC"
        }

        self.CONTRACT_ROUTER = {
            "swap": "0x1BEC6C32bAA0881EA3f3Ec5e95d10EF8a252589B"
        }

        self.UNISWAP_V3_ABI = [
            {
                "inputs": [
                    {
                        "components": [
                            { "internalType": "address", "name": "tokenIn", "type": "address" }, 
                            { "internalType": "address", "name": "tokenOut", "type": "address" }, 
                            { "internalType": "uint24", "name": "fee", "type": "uint24" }, 
                            { "internalType": "address", "name": "recipient", "type": "address" }, 
                            { "internalType": "uint256", "name": "deadline", "type": "uint256" }, 
                            { "internalType": "uint256", "name": "amountIn", "type": "uint256" }, 
                            { "internalType": "uint256", "name": "amountOutMinimum", "type": "uint256" }, 
                            { "internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160" }
                        ],
                        "internalType": "struct ISwapRouter.ExactInputSingleParams",
                        "name": "params",
                        "type": "tuple"
                    }
                ],
                "name": "exactInputSingle",
                "outputs": [
                    { "internalType": "uint256", "name": "amountOut", "type": "uint256" }
                ],
                "stateMutability": "payable",
                "type": "function"
            }
        ]

        self.REF_CODE = "W-p0XycS" # U can change it with yours.
        self.USE_PROXY = False
        self.ROTATE_PROXY = False
        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.accounts = {}
        
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/117.0.0.0"
        ]

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
        {Fore.GREEN + Style.BRIGHT}X1 Ecochain {Fore.BLUE + Style.BRIGHT}Auto BOT
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
    
    def display_proxy(self, proxy_url=None):
        if not proxy_url: return "No Proxy"

        proxy_url = re.sub(r"^(http|https|socks4|socks5)://", "", proxy_url)

        if "@" in proxy_url:
            proxy_url = proxy_url.split("@", 1)[1]

        return proxy_url
    
    def initialize_headers(self, address: str):
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Origin": "https://testnet.x1ecochain.com",
            "Pragma": "no-cache",
            "Referer": "https://testnet.x1ecochain.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": self.accounts[address]["user_agent"]
        }

        return headers.copy()
    
    def generate_address(self, private_key: str):
        try:
            acc = Account.from_key(private_key)
            address = acc.address
            return address
        except Exception as e:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Failed to Generate EVM Address {Style.RESET_ALL}"
            )
            return None
        
    def generate_random_recipient(self):
        try:
            account = Account.create()
            recipient = account.address
            
            return recipient
        except Exception as e:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Failed to Generate Random Recipient {Style.RESET_ALL}"
            )
            return None
    
    def generate_signature(self, private_key: str, message: str):
        try:
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=private_key)
            signature = to_hex(signed_message.signature)
            return signature
        except Exception as e:
            raise Exception(f"Generate Signature Failed: {str(e)}")
        
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None
        
    async def get_web3_with_check(self, address: str, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}

        if self.USE_PROXY:
            proxy_url = self.get_next_proxy_for_account(address)
            request_kwargs["proxies"] = {
                "http": proxy_url,
                "https": proxy_url,
            }

        for attempt in range(retries):
            try:
                provider = HTTPProvider(
                    self.API_URL['rpc'],
                    request_kwargs=request_kwargs
                )
                web3 = Web3(provider)

                web3.middleware_onion.inject(
                    ExtraDataToPOAMiddleware, 
                    layer=0
                )

                await asyncio.to_thread(lambda: web3.eth.block_number)
                return web3
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                raise Exception(f"Failed to Connect to RPC: {str(e)}")

    async def get_token_balance(self, address: str):
        try:
            web3 = await self.get_web3_with_check(address)

            raw_balance = await asyncio.to_thread(
                web3.eth.get_balance,
                address
            )

            token_balance = raw_balance / (10**18)

            return token_balance
        except Exception as e:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None

    async def send_raw_transaction_with_retries(self, private_key, web3, tx, retries=5):
        for attempt in range(retries):
            try:
                signed_tx = web3.eth.account.sign_transaction(tx, private_key)

                raw_tx = await asyncio.to_thread(
                    web3.eth.send_raw_transaction,
                    signed_tx.raw_transaction
                )

                return web3.to_hex(raw_tx)
            except TransactionNotFound:
                pass
            except Exception as e:
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} [Attempt {attempt + 1}] Send TX Error: {str(e)} {Style.RESET_ALL}"
                )
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Hash Not Found After Maximum Retries")

    async def wait_for_receipt_with_retries(self, web3, tx_hash, retries=5):
        for attempt in range(retries):
            try:
                receipt = await asyncio.to_thread(
                    web3.eth.wait_for_transaction_receipt,
                    tx_hash,
                    60
                )
                return receipt
            except TransactionNotFound:
                pass
            except Exception as e:
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT} [Attempt {attempt + 1}] Wait for Receipt Error: {str(e)} {Style.RESET_ALL}"
                )
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Receipt Not Found After Maximum Retries")
    
    async def perform_transfer(self, private_key: str, address: str, recipient: str):
        try:
            web3 = await self.get_web3_with_check(address)

            amount_to_wei = web3.to_wei(self.SEND_AMOUNT, "ether")

            latest_block = await asyncio.to_thread(web3.eth.get_block, "latest")
            base_fee = latest_block["baseFeePerGas"]

            max_priority_fee = web3.to_wei(1, "gwei")
            max_fee = base_fee + max_priority_fee

            nonce = await asyncio.to_thread(
                web3.eth.get_transaction_count,
                address,
                "pending"
            )

            chain_id = await asyncio.to_thread(lambda: web3.eth.chain_id)
            
            transfer_tx = {
                "from": web3.to_checksum_address(address),
                "to": web3.to_checksum_address(recipient),
                "value": amount_to_wei,
                "gas": 21000,
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce":nonce,
                "chainId": chain_id,
            }

            tx_hash = await self.send_raw_transaction_with_retries(private_key, web3, transfer_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

            return {
                "tx_hash": tx_hash, 
                "block_number": receipt.blockNumber
            }
        except Exception as e:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
        
    def calc_amount_out_min(self, pools: dict, token_in_symbol: str, amount_in_wei: int):
        try:
            pool = max(pools["data"]["pools"], key=lambda p: int(p["liquidity"]))

            token0 = pool["token0"]["symbol"]
            token1 = pool["token1"]["symbol"]

            sqrt_price_x96 = Decimal(pool["sqrtPrice"])
            fee_tier = Decimal(pool["feeTier"])

            price = (sqrt_price_x96 ** 2) / (Decimal(2) ** 192)

            amount_in = Decimal(amount_in_wei)

            if token_in_symbol == token0:
                amount_out = amount_in * price
                
            elif token_in_symbol == token1:
                amount_out = amount_in / price
                
            else:
                raise ValueError("Token not found in pool")

            fee_multiplier = Decimal(1) - (fee_tier / Decimal(1_000_000))
            amount_out *= fee_multiplier

            slippage_multiplier = Decimal(1) - (Decimal(2) / Decimal(100))
            amount_out *= slippage_multiplier

            amount_out_wei = amount_out.to_integral_value(rounding=ROUND_DOWN)

            return int(amount_out_wei)
        except Exception as e:
            raise Exception(f"Failed to Calculate Amount Out Min: {str(e)}")
        
    async def perform_swap(self, private_key: str, address: str, pools: dict):
        try:
            web3 = await self.get_web3_with_check(address)

            token_in = web3.to_checksum_address(self.CONTRACT_ADDRESS['WX1T'])
            token_out = web3.to_checksum_address(self.CONTRACT_ADDRESS['USDT'])
            router = web3.to_checksum_address(self.CONTRACT_ROUTER['swap'])

            deadline = int(time.time()) + 600

            amount_in = web3.to_wei(self.SWAP_AMOUNT, "ether")

            amount_out_min_wei = self.calc_amount_out_min(pools, "WX1T", amount_in)

            swap_params = {
                "tokenIn": token_in,
                "tokenOut": token_out,
                "fee": 500,
                "recipient": address,
                "deadline": deadline,
                "amountIn": amount_in,
                "amountOutMinimum": amount_out_min_wei,
                "sqrtPriceLimitX96": 0
            }

            router_contract = web3.eth.contract(address=router, abi=self.UNISWAP_V3_ABI)
            
            swap_func = router_contract.functions.exactInputSingle(swap_params)

            estimated_gas = await asyncio.to_thread(
                swap_func.estimate_gas,
                {
                    "from": address,
                    "value": amount_in
                }
            )

            latest_block = await asyncio.to_thread(web3.eth.get_block, "latest")
            base_fee = latest_block["baseFeePerGas"]

            max_priority_fee = web3.to_wei(1, "gwei")
            max_fee = base_fee + max_priority_fee

            nonce = await asyncio.to_thread(
                web3.eth.get_transaction_count,
                address,
                "pending"
            )

            chain_id = await asyncio.to_thread(lambda: web3.eth.chain_id)

            swap_tx = await asyncio.to_thread(
                swap_func.build_transaction,
                {
                    "from": address,
                    "value": amount_in,
                    "gas": int(estimated_gas * 1.2),
                    "maxFeePerGas": int(max_fee),
                    "maxPriorityFeePerGas": int(max_priority_fee),
                    "nonce": nonce,
                    "chainId": chain_id,
                }
            )

            tx_hash = await self.send_raw_transaction_with_retries(private_key, web3, swap_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

            return {
                "tx_hash": tx_hash, 
                "block_number": receipt.blockNumber
            }
        except Exception as e:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Message :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
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

    async def ensure_ok(self, response):
        if response.status >= 400:
            error_text = await response.text()
            raise Exception(f"HTTP {response.status}: {error_text}")
    
    async def check_connection(self, proxy_url=None):
        url = "https://api.ipify.org?format=json"

        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url=url, proxy=proxy, proxy_auth=proxy_auth) as response:
                    await self.ensure_ok(response)
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
        
        return None
    
    async def auth_message(self, address: str, proxy_url=None, retries=5):
        url = f"{self.API_URL['testnet']}/signin"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Content-Type"] = "application/json"
                params = {
                    "address": address
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, params=params, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Login   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Auth Message {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def auth_signin(self, private_key: str, address: str, message: str, proxy_url=None, retries=5):
        url = f"{self.API_URL['testnet']}/signin"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Content-Type"] = "application/json"
                payload = {
                    "signature": self.generate_signature(private_key, message),
                    "address": address,
                    "ref_code": self.REF_CODE
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, json=payload, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
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
    
    async def auth_me(self, address: str, proxy_url=None, retries=5):
        url = f"{self.API_URL['testnet']}/me"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Authorization"] = self.accounts[address]["token"]
                headers["Content-Type"] = "application/json"

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Stats   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Data {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def quests_list(self, address: str, proxy_url=None, retries=5):
        url = f"{self.API_URL['testnet']}/quests"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Authorization"] = self.accounts[address]["token"]
                headers["Content-Type"] = "application/json"

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Quests  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Data {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def request_faucet(self, address: str, proxy_url=None, retries=5):
        url = f"{self.API_URL['nft']}/testnet/faucet"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Authorization"] = self.accounts[address]["token"]
                headers["Content-Type"] = "application/json"
                params = {
                    "address": address
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, params=params, proxy=proxy, proxy_auth=proxy_auth) as response:
                        if response.status == 500: return True
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Failed to Request Faucet {Style.RESET_ALL}"
                )

        return None
    
    async def pool_by_tokens(self, address: str, proxy_url=None, retries=5):
        url = f"{self.API_URL['dex']}/subgraphs/name/uniswap-v3"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Content-Type"] = "application/json"
                headers["Origin"] = "https://ecodex.one"
                headers["Referer"] = "https://ecodex.one/"
                payload = {
                    "query": "\n    query PoolByTokens($a: String!, $b: String!) {\n      pools(\n        where: {\n          token0_in: [$a, $b]\n          token1_in: [$a, $b]\n        }\n        first: 5\n      ) {\n        id\n        feeTier\n        sqrtPrice\n        liquidity\n        tick\n        token0 { id symbol name decimals }\n        token1 { id symbol name decimals }\n        ticks(first: 500, orderBy: tickIdx, orderDirection: asc) {\n          tickIdx\n          liquidityNet\n          liquidityGross\n        }\n      }\n    }\n  ",
                    "variables": {
                        "a": self.CONTRACT_ADDRESS["WX1T"].lower(),
                        "b": self.CONTRACT_ADDRESS["USDT"].lower()
                    },
                    "operationName": "PoolByTokens"
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, json=payload, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Failed to Fetch Pools {Style.RESET_ALL}"
                )

        return None
    
    async def complete_quest(self, address: str, quest_id: str, proxy_url=None, retries=5):
        url = f"{self.API_URL['testnet']}/quests"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Authorization"] = self.accounts[address]["token"]
                headers["Content-Type"] = "application/json"
                params = {
                    "quest_id": quest_id
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, params=params, proxy=proxy, proxy_auth=proxy_auth) as response:
                        if response.status == 400:
                            self.log(
                                f"{Fore.BLUE+Style.BRIGHT}   Complete :{Style.RESET_ALL}"
                                f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                            )
                            return None
                        
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Complete :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Failed {Style.RESET_ALL}"
                )

        return None
    
    async def process_check_connection(self, address: str, proxy_url=None):
        while True:
            if self.USE_PROXY:
                proxy_url = self.get_next_proxy_for_account(address)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.display_proxy(proxy_url)} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy_url)
            if is_valid: return True

            if self.ROTATE_PROXY:
                proxy_url = self.rotate_proxy_for_account(address)
                await asyncio.sleep(1)
                continue

            return False
        
    async def process_auth_signin(self, private_key: str, address: str, proxy_url=None):
        auth_msg = await self.auth_message(address, proxy_url)
        if not auth_msg: return False

        message = auth_msg.get("message")

        auth_sign = await self.auth_signin(private_key, address, message, proxy_url)
        if not auth_sign: return False

        self.accounts[address]["token"] = auth_sign.get("token")

        self.log(
            f"{Fore.CYAN+Style.BRIGHT}Login   :{Style.RESET_ALL}"
            f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
        )

        return True
        
    async def process_auth_me(self, address: str, proxy_url=None):
        me = await self.auth_me(address, proxy_url)
        if not me: return False

        self.log(f"{Fore.CYAN+Style.BRIGHT}Stats   :{Style.RESET_ALL}")

        points = me.get("points")
        ref_points = me.get("ref_points")
        rank = me.get("rank")
        ref_rank = me.get("referral_rank")

        self.log(
            f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
            f"{Fore.BLUE+Style.BRIGHT}Points    :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {points} {Style.RESET_ALL}"
        )
        self.log(
            f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
            f"{Fore.BLUE+Style.BRIGHT}Ref Points:{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {ref_points} {Style.RESET_ALL}"
        )
        self.log(
            f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
            f"{Fore.BLUE+Style.BRIGHT}Rank      :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} #{rank} {Style.RESET_ALL}"
        )
        self.log(
            f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
            f"{Fore.BLUE+Style.BRIGHT}Ref Rank  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} #{ref_rank} {Style.RESET_ALL}"
        )

        return True
    
    async def process_request_faucet(self, address: str, proxy_url=None):
        request = await self.request_faucet(address, proxy_url)
        if not request: return False

        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
            f"{Fore.GREEN+Style.BRIGHT} Requested Successfully {Style.RESET_ALL}"
        )

        return True
    
    async def process_request_faucet(self, address: str, proxy_url=None):
        request = await self.request_faucet(address, proxy_url)
        if not request: return False

        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
            f"{Fore.GREEN+Style.BRIGHT} Requested Successfully {Style.RESET_ALL}"
        )

        return True
    
    async def process_perform_transfer(self, private_key: str, address: str):
        recipient = self.generate_random_recipient()
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Recipient:{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {recipient} {Style.RESET_ALL}                                   "
        )
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Amount   :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {self.SEND_AMOUNT} X1T {Style.RESET_ALL}                                   "
        )

        balance = await self.get_token_balance(address)
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} X1T {Style.RESET_ALL}                                   "
        )

        if balance is None:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Failed to Fetch X1T Token Balance {Style.RESET_ALL}"
            )
            return False
        
        if balance < self.SEND_AMOUNT:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Insufficient X1T Token Balance {Style.RESET_ALL}"
            )
            return False

        transfer = await self.perform_transfer(private_key, address, recipient)
        if not transfer: return False

        block_number = transfer["block_number"]
        tx_hash = transfer["tx_hash"]
        explorer = self.API_URL["explorer"]

        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
            f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}                                   "
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
            f"{Fore.WHITE+Style.BRIGHT} {explorer}{tx_hash} {Style.RESET_ALL}"
        )

        return True
    
    async def process_perform_swap(self, private_key: str, address: str, proxy_url=None):
        pools = await self.pool_by_tokens(address, proxy_url)
        if not pools: return False

        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Amount   :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {self.SWAP_AMOUNT} X1T {Style.RESET_ALL}                                   "
        )

        balance = await self.get_token_balance(address)
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} X1T {Style.RESET_ALL}                                   "
        )

        if balance is None:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Failed to Fetch X1T Token Balance {Style.RESET_ALL}"
            )
            return False
        
        if balance < self.SWAP_AMOUNT:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Insufficient X1T Token Balance {Style.RESET_ALL}"
            )
            return False

        swap = await self.perform_swap(private_key, address, pools)
        if not swap: return False

        block_number = swap["block_number"]
        tx_hash = swap["tx_hash"]
        explorer = self.API_URL["explorer"]

        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
            f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}                                   "
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
            f"{Fore.WHITE+Style.BRIGHT} {explorer}{tx_hash} {Style.RESET_ALL}"
        )

        return True
    
    async def process_complete_quest(self, address: str, quest_id: str, proxy_url=None):
        complete = await self.complete_quest(address, quest_id, proxy_url)
        if not complete: return False

        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Complete :{Style.RESET_ALL}"
            f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
        )

        return True
    
    async def process_handle_quests(self, private_key: str, address: str, proxy_url=None):
        quests = await self.quests_list(address, proxy_url)
        if not quests: return False

        self.log(f"{Fore.CYAN+Style.BRIGHT}Quests  :{Style.RESET_ALL}")

        for quest in quests:
            quest_id = quest.get("id")
            title = quest.get("title")
            type = quest.get("type")
            reward = quest.get("reward")
            periodicity = quest.get("periodicity")
            is_completed = quest.get("is_completed")
            is_completed_today = quest.get("is_completed_today")

            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
            )

            if periodicity == "one_time":
                if is_completed:
                    self.log(
                        f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Already Completed {Style.RESET_ALL}"
                    )
                    continue

            elif periodicity == "daily":
                if is_completed_today:
                    self.log(
                        f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Already Completed {Style.RESET_ALL}"
                    )
                    continue

            if type == "faucet":
                if not await self.process_request_faucet(address, proxy_url): continue

            elif type == "transfer":
                if not await self.process_perform_transfer(private_key, address): continue

            elif type == "swap":
                if not await self.process_perform_swap(private_key, address, proxy_url): continue

            complete = await self.complete_quest(address, quest_id, proxy_url)
            if not complete: continue

            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Complete :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Reward   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {reward} Points {Style.RESET_ALL}"
            )

        return True

    async def process_accounts(self, private_key: str, address: str, proxy_url=None):
        if not await self.process_check_connection(address, proxy_url): return False

        if self.USE_PROXY:
            proxy_url = self.get_next_proxy_for_account(address)

        if not await self.process_auth_signin(private_key, address, proxy_url): return False

        await self.process_auth_me(address, proxy_url)
        await self.process_handle_quests(private_key, address, proxy_url)
        
    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                print(f"{Fore.RED+Style.BRIGHT}No Accounts Loaded.{Style.RESET_ALL}")
                return False
            
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

                    address = self.generate_address(private_key)
                    if not address: continue

                    if address not in self.accounts:
                        self.accounts[address] = {
                            "user_agent": random.choice(self.USER_AGENTS)
                        }

                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Address :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                    )
                    
                    await self.process_accounts(private_key, address)
                    await asyncio.sleep(random.uniform(2.0, 3.0))

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

        except Exception as e:
            raise e
        except asyncio.CancelledError:
            raise

if __name__ == "__main__":
    bot = X1()
    try:
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] X1 Ecochain - BOT{Style.RESET_ALL}                                       "                              
        )
    finally:
        sys.exit(0)