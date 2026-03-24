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
from eth_abi.abi import encode
from eth_utils import to_hex
from dotenv import load_dotenv
from solcx import compile_standard, install_solc
from datetime import datetime, timezone
from decimal import Decimal, getcontext, ROUND_DOWN
from colorama import *
import asyncio, random, time, sys, re, os

load_dotenv()

getcontext().prec = 80

install_solc("0.8.27", show_progress=False)

class X1:
    def __init__(self) -> None:
        self.API_URL = {
            "testnet": "https://testnet-api.x1eco.com",
            "nft": "https://nft-api.x1eco.com",
            "dex": "https://ms.kod.af",
            "constructor": "https://api-constructor.x1ecochain.com",
            "rpc": "https://maculatus-rpc.x1eco.com/",
            "explorer": "https://maculatus-scan.x1eco.com/tx/",
        }

        self.SEND_PERCENT = Decimal(os.getenv("SEND_PERCENT", "10"))
        self.SWAP_PERCENT = Decimal(os.getenv("SWAP_PERCENT", "10"))
        self.LIQUIDITY_AMOUNT = Decimal(os.getenv("LIQUIDITY_AMOUNT", "1"))
        self.DEPLOY_AMOUNT = 100

        self.CONTRACT_ADDRESS = {
            "WX1T": "0xe2ED17Ae5e68863E77899205a83A8f1E138c608f",
            "USDT": "0xd127BA1f0EfA2c5c7d9e6E7339DBafe2A6b1EAeC"
        }

        self.CONTRACT_ROUTER = {
            "swap": "0x1BEC6C32bAA0881EA3f3Ec5e95d10EF8a252589B",
            "mint": "0x4505eEA72B4D215284305d794CCAc618cd5eA531",
            "deploy": "0x8364089f85CFc7Bb455f1c8F2D924568cE433f9F",
            "payable": "0x34264ec130f9aD5Fc9aa20aB95e42067b1304B5a",
        }

        self.CONTRACT_ABI = [
            {
                "type": "function",
                "name": "balanceOf",
                "stateMutability": "view",
                "inputs": [
                    { "internalType": "address", "name": "account", "type": "address" }
                ],
                "outputs": [
                    { "internalType": "uint256", "name": "", "type": "uint256" }
                ]
            },
            {
                "type": "function",
                "name": "allowance",
                "stateMutability": "view",
                "inputs": [
                    { "internalType": "address", "name": "owner",   "type": "address" },
                    { "internalType": "address", "name": "spender", "type": "address" }
                ],
                "outputs": [
                    { "internalType": "uint256", "name": "", "type": "uint256" }
                ]
            },
            {
                "type": "function",
                "name": "approve",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "internalType": "address", "name": "spender", "type": "address"  },
                    { "internalType": "uint256", "name": "value",   "type": "uint256" }
                ],
                "outputs": [
                    { "internalType": "bool", "name": "", "type": "bool" }
                ]
            },
            {
                "type": "function",
                "name": "exactInputSingle",
                "stateMutability": "payable",
                "inputs": [
                    {
                        "internalType": "struct ISwapRouter.ExactInputSingleParams",
                        "name": "params",
                        "type": "tuple",
                        "components": [
                            { "internalType": "address", "name": "tokenIn", "type": "address" }, 
                            { "internalType": "address", "name": "tokenOut", "type": "address" }, 
                            { "internalType": "uint24", "name": "fee", "type": "uint24" }, 
                            { "internalType": "address", "name": "recipient", "type": "address" }, 
                            { "internalType": "uint256", "name": "deadline", "type": "uint256" }, 
                            { "internalType": "uint256", "name": "amountIn", "type": "uint256" }, 
                            { "internalType": "uint256", "name": "amountOutMinimum", "type": "uint256" }, 
                            { "internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160" }
                        ]
                    }
                ],
                "outputs": [
                    { "internalType": "uint256", "name": "amountOut", "type": "uint256" }
                ]
            },
            {
                "type": "function",
                "name": "mint",
                "stateMutability": "payable",
                "inputs": [
                    {
                        "internalType": "tuple",
                        "name": "params",
                        "type": "tuple",
                        "components": [
                            { "internalType": "address", "name": "token0", "type": "address" },
                            { "internalType": "address", "name": "token1", "type": "address" },
                            { "internalType": "uint24", "name": "fee", "type": "uint24" },
                            { "internalType": "int24", "name": "tickLower", "type": "int24" },
                            { "internalType": "int24", "name": "tickUpper", "type": "int24" },
                            { "internalType": "uint256", "name": "amount0Desired", "type": "uint256" },
                            { "internalType": "uint256", "name": "amount1Desired", "type": "uint256" },
                            { "internalType": "uint256", "name": "amount0Min", "type": "uint256" },
                            { "internalType": "uint256", "name": "amount1Min", "type": "uint256" },
                            { "internalType": "address", "name": "recipient", "type": "address" },
                            { "internalType": "uint256", "name": "deadline", "type": "uint256" }
                        ]
                    }
                ],
                "outputs": [
                    { "internalType": "uint256", "name": "tokenId", "type": "uint256" },
                    { "internalType": "uint128", "name": "liquidity", "type": "uint128" },
                    { "internalType": "uint256", "name": "amount0", "type": "uint256" },
                    { "internalType": "uint256", "name": "amount1", "type": "uint256" }
                ]
            },
            {
                "type": "function",
                "name": "sendAndDeploy",
                "stateMutability": "payable",
                "inputs": [
                    { "internalType": "address payable", "name": "to", "type": "address" },
                    { "internalType": "uint256", "name": "amount", "type": "uint256" },
                    { "internalType": "bytes", "name": "creationCode", "type": "bytes" }
                ],
                "outputs": []
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
    
    def initialize_headers(self, address: str, headers_type="base"):
        if headers_type == "base":
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
        else:
            headers = {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Host": "api-constructor.x1ecochain.com",
                "Origin": "https://constructor.x1ecochain.com",
                "Pragma": "no-cache",
                "Referer": "https://constructor.x1ecochain.com/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
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
        
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None
        
    def generate_constructor_msg(self, address: str, nonce: str):
        now = datetime.now(timezone.utc)
        issued_at = now.isoformat(timespec="milliseconds").replace("+00:00", "Z")

        message = "\n".join([
            "constructor.x1ecochain.com wants you to sign in with your Ethereum account:",
            address,
            "",
            "Sign in to Token Constructor.",
            "",
            "URI: https://constructor.x1ecochain.com",
            "Version: 1",
            "Chain ID: 10778",
            f"Nonce: {nonce}",
            f"Issued At: {issued_at}",
        ])

        return message
    
    def generate_signature(self, private_key: str, message: str):
        try:
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=private_key)
            signature = to_hex(signed_message.signature)
            return signature
        except Exception as e:
            raise Exception(f"Generate Signature Failed: {str(e)}")
        
    def generate_token_params(self):
        PREFIXES = [
            "Eco", "Neo", "Meta", "Flux", "Nova", "Omni", "Apex", "Volt",
            "Zeta", "Hexa", "Plex", "Velo", "Dyna", "Core", "Nexo", "Orbi",
            "Pyro", "Aero", "Giga", "Hyper", "Luma", "Meso", "Nano", "Opti",
        ]
        SUFFIXES = [
            "Chain", "Node", "Net", "Fi", "X", "Protocol", "Hub", "Base",
            "Link", "Flow", "Grid", "Vault", "Wave", "Sphere", "Lab", "Works",
            "Forge", "Gate", "Port", "Space", "Sync", "Pulse", "Byte", "Coin",
        ]

        prefix = random.choice(PREFIXES)
        suffix = random.choice(SUFFIXES)
        number = random.randint(1, 999)
        name   = f"{prefix}{suffix}{number:03d}"
        symbol = (prefix[:2] + suffix[:2]).upper()

        zeros   = random.randint(6, 9)
        leading = 1 if zeros == 9 else random.randint(1, 9)
        premint = str(leading * (10 ** zeros))

        return {
            "name":          name,
            "symbol":        symbol,
            "permit":        True,
            "decimals":      "18",
            "premintAmount": premint,
            "mintable":      False,
            "burnable":      False,
            "pausable":      False,
            "whitelist":     False,
            "taxable":       False,
            "taxFee":        2,
        }

    def build_solidity_source(self, token_params):
        name           = token_params["name"]
        symbol         = token_params["symbol"]
        permit         = token_params.get("permit", False)
        decimals       = token_params.get("decimals", "18")
        premint_amount = token_params.get("premintAmount", "0")
        mintable       = token_params.get("mintable", False)
        burnable       = token_params.get("burnable", False)
        pausable       = token_params.get("pausable", False)
        whitelist      = token_params.get("whitelist", False)
        taxable        = token_params.get("taxable", False)
        tax_fee_bps    = round(token_params.get("taxFee", 0) * 100)

        permit_mod = (
            {
                "import":                 f'import {{ERC20Permit}} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";',
                "inheritance":            "ERC20Permit",
                "constructorInheritance": f'ERC20Permit("{name}")',
            }
            if permit else
            {"import": "", "inheritance": "", "constructorInheritance": ""}
        )

        mint_mod = (
            {
                "import":          "",
                "constant":        'bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");',
                "constructorArg":  "address minter",
                "constructorRole": "_grantRole(MINTER_ROLE, minter);",
                "function": (
                    f'function mint(address to, uint256 amount) public '
                    f'{"onlyRole(MINTER_ROLE)" if whitelist else "onlyOwner"} {{\n'
                    f'        _mint(to, amount);\n    }}'
                ),
            }
            if mintable else
            {"import": "", "constant": "", "constructorArg": "", "constructorRole": "", "function": ""}
        )

        burn_mod = (
            {
                "import":      'import {ERC20Burnable} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";',
                "inheritance": "ERC20Burnable",
            }
            if burnable else
            {"import": "", "inheritance": ""}
        )

        pause_mod = (
            {
                "import":      'import {ERC20Pausable} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";',
                "inheritance": "ERC20Pausable",
                "constant":    'bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");',
                "constructorArg":  "address pauser",
                "constructorRole": "_grantRole(PAUSER_ROLE, pauser);",
                "function": (
                    f'function pause() public {"onlyRole(PAUSER_ROLE)" if whitelist else "onlyOwner"} {{\n'
                    f'        _pause();\n    }}\n\n'
                    f'    function unpause() public {"onlyRole(PAUSER_ROLE)" if whitelist else "onlyOwner"} {{\n'
                    f'        _unpause();\n    }}'
                ),
                "overrideFunction": (
                    'function _update(address from, address to, uint256 value)\n'
                    '        internal\n'
                    '        override(ERC20, ERC20Pausable)\n'
                    '    {\n'
                    + (
                        '        if (from != address(0) && whitelistActive) {\n'
                        '            require(hasRole(WHITELIST_ROLE, from), "Whitelist: Sender lacks role");\n'
                        '        }\n'
                        if whitelist else ''
                    )
                    + '        super._update(from, to, value);\n    }'
                ),
            }
            if pausable else
            {"import": "", "inheritance": "", "constant": "", "constructorArg": "", "constructorRole": "", "function": "", "overrideFunction": ""}
        )

        wl_mod = (
            {
                "import":      'import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";',
                "constant":    'bytes32 public constant WHITELIST_ROLE = keccak256("WHITELIST_ROLE");\n    bool public whitelistActive = true;',
                "inheritance": "AccessControl",
                "constructorArg":  "address defaultAdmin",
                "constructorRole": "_grantRole(DEFAULT_ADMIN_ROLE, defaultAdmin);\n        _grantRole(WHITELIST_ROLE, defaultAdmin);",
                "function": (
                    'function setWhitelistActive(bool _active) public onlyRole(DEFAULT_ADMIN_ROLE) {\n'
                    '        whitelistActive = _active;\n    }'
                ),
                "overrideFunction": (
                    f'function _update(address from, address to, uint256 value)\n'
                    f'        internal\n'
                    f'        override{"(ERC20, ERC20Pausable)" if pausable else "(ERC20)"}\n'
                    f'    {{\n'
                    f'        if (from != address(0) && whitelistActive) {{\n'
                    f'            require(hasRole(WHITELIST_ROLE, from), "Whitelist: Sender lacks role");\n'
                    f'        }}\n'
                    f'        super._update(from, to, value);\n    }}'
                ),
            }
            if whitelist else
            {"import": "", "constant": "", "inheritance": "", "constructorArg": "", "constructorRole": "", "function": "", "overrideFunction": ""}
        )

        ownable_mod = (
            {"import": "", "inheritance": "", "constructorArg": "", "constructorInheritance": ""}
            if whitelist else
            {
                "import":                 'import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";',
                "inheritance":            "Ownable",
                "constructorArg":         "address initialOwner",
                "constructorInheritance": "Ownable(initialOwner)",
            }
        )

        decimals_mod = {
            "constructorFunction": f"_mint(recipient, {premint_amount} * 10 ** decimals());",
            "overrideFunction": (
                f'function decimals() public view override returns (uint8) {{\n'
                f'        return {decimals};\n    }}'
            ),
        }

        tax_mod = (
            {
                "constant":            f"address public taxWallet;\n    uint256 public taxFeeBps = {tax_fee_bps};",
                "constructorArg":      "address _taxWallet",
                "constructorFunction": "taxWallet = _taxWallet;",
                "function": (
                    f'function setTaxWallet(address _newTaxWallet) external {"onlyRole(DEFAULT_ADMIN_ROLE)" if whitelist else "onlyOwner"} {{\n'
                    f'        require(_newTaxWallet != address(0), "Tax wallet cannot be zero address");\n'
                    f'        taxWallet = _newTaxWallet;\n    }}'
                ),
                "overrideFunction": (
                    f'function _update(address from, address to, uint256 value)\n'
                    f'        internal\n'
                    f'        override{"(ERC20, ERC20Pausable)" if pausable else "(ERC20)"}\n'
                    f'    {{\n'
                    + (
                        '        \n        if (from != address(0) && whitelistActive) {\n'
                        '            require(hasRole(WHITELIST_ROLE, from), "Whitelist: Sender lacks role");\n'
                        '        }\n'
                        if whitelist else ''
                    )
                    + f'        if (from == address(0) || to == address(0) || {"hasRole(DEFAULT_ADMIN_ROLE, from)" if whitelist else "from == owner()"} || from == taxWallet) {{\n'
                    f'            super._update(from, to, value);\n'
                    f'            return;\n'
                    f'        }}\n\n'
                    f'        uint256 taxAmount = (value * taxFeeBps) / 10000;\n'
                    f'        uint256 amountAfterTax = value - taxAmount;\n\n'
                    f'        if (taxAmount > 0) {{\n'
                    f'            super._update(from, taxWallet, taxAmount);\n'
                    f'        }}\n'
                    f'        super._update(from, to, amountAfterTax);\n    }}'
                ),
            }
            if taxable else
            {"constant": "", "constructorArg": "", "constructorFunction": "", "function": "", "overrideFunction": ""}
        )

        imports = [x for x in [
            wl_mod["import"],
            mint_mod["import"],
            'import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";',
            burn_mod["import"],
            pause_mod["import"],
            permit_mod["import"],
            ownable_mod["import"],
        ] if x]

        inheritances = [x for x in [
            "ERC20",
            burn_mod["inheritance"],
            pause_mod["inheritance"],
            ownable_mod["inheritance"],
            wl_mod["inheritance"],
            permit_mod["inheritance"],
        ] if x]

        constants        = [x for x in ([pause_mod["constant"], mint_mod["constant"], wl_mod["constant"], tax_mod["constant"]] if whitelist else [tax_mod["constant"]]) if x]
        constructor_args = [x for x in ([wl_mod["constructorArg"], pause_mod["constructorArg"], mint_mod["constructorArg"], tax_mod["constructorArg"]] if whitelist else [ownable_mod["constructorArg"], tax_mod["constructorArg"]]) if x]
        ctor_inherit     = [x for x in [f'ERC20("{name}", "{symbol}")', "" if whitelist else ownable_mod["constructorInheritance"], permit_mod["constructorInheritance"]] if x]
        ctor_body        = [x for x in ([tax_mod["constructorFunction"], decimals_mod["constructorFunction"], wl_mod["constructorRole"], pause_mod["constructorRole"], mint_mod["constructorRole"]] if whitelist else [tax_mod["constructorFunction"], decimals_mod["constructorFunction"]]) if x]

        if taxable:
            update_override = tax_mod["overrideFunction"]
        elif pausable:
            update_override = pause_mod["overrideFunction"]
        else:
            update_override = wl_mod["overrideFunction"]

        functions = [x for x in [
            wl_mod["function"],
            pause_mod["function"],
            mint_mod["function"],
            decimals_mod["overrideFunction"],
            tax_mod["function"],
            update_override,
        ] if x]

        all_ctor_args      = ", ".join(["address recipient"] + [a for a in constructor_args if a.strip()])
        constants_block    = ("\n    " + "\n    ".join(constants) + "\n") if constants else ""
        ctor_inherit_block = ("\n        " + "\n        ".join(ctor_inherit) + "\n   ") if ctor_inherit else ""
        ctor_body_block    = ("\n        " + "\n        ".join(ctor_body) + "\n    ") if ctor_body else ""
        functions_block    = ("\n\n    " + "\n\n    ".join(functions)) if functions else ""

        return (
            "// SPDX-License-Identifier: MIT\n"
            "// Compatible with OpenZeppelin Contracts ^5.5.0\n"
            "pragma solidity ^0.8.27;\n\n"
            + "\n".join(imports) + "\n\n"
            + f"contract {name} is {', '.join(inheritances)} {{"
            + constants_block + "\n"
            + f"    constructor({all_ctor_args}) "
            + ctor_inherit_block + " "
            + "{" + ctor_body_block + "}"
            + functions_block + "\n}"
        )

    def resolve_path(self, base, rel):
        parts = base.split("/")
        parts.pop()
        for seg in rel.split("/"):
            if seg == ".":
                continue
            elif seg == "..":
                parts.pop()
            else:
                parts.append(seg)
        return "/".join(parts)

    async def resolve_imports(self, entry_path, source_code, sources=None, proxy_url=None):
        if sources is None:
            sources = {}
        sources[entry_path] = {"content": source_code}

        for m in re.finditer(r'import\s+(?:\{[^}]*\}\s+from\s+)?["\']([^"\']+)["\']', source_code):
            raw      = m.group(1)
            resolved = self.resolve_path(entry_path, raw) if raw.startswith(("./", "../")) else raw
            if resolved in sources:
                continue

            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                url = (
                    f"https://cdn.jsdelivr.net/npm/@openzeppelin/contracts@5.0.0/"
                    + resolved.replace("@openzeppelin/contracts/", "")
                    if resolved.startswith("@openzeppelin/contracts")
                    else f"https://cdn.jsdelivr.net/npm/{resolved}"
                )
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                    async with session.get(url=url, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        await self.resolve_imports(resolved, await response.text(), sources)
            except Exception:
                pass

        return sources

    def compile_solidity(self, contract_name, sources):
        output = compile_standard(
            {
                "language": "Solidity",
                "sources":  sources,
                "settings": {
                    "optimizer":       {"enabled": False},
                    "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}},
                },
            },
            solc_version="0.8.27",
        )

        errors = [e for e in output.get("errors", []) if e["severity"] == "error"]
        if errors:
            raise RuntimeError("\n".join(e["formattedMessage"] for e in errors))

        fn        = f"{contract_name}Token.sol"
        contracts = output["contracts"].get(fn, {})
        contract  = contracts.get(contract_name) or contracts.get("Token")
        if not contract:
            raise RuntimeError(f'Contract "{contract_name}" not found')

        return {"bytecode": contract["evm"]["bytecode"]["object"], "abi": contract["abi"]}

    def encode_constructor_args(self, features, addresses):
        recipient  = addresses["recipient"]
        owner      = addresses.get("owner",     recipient)
        pauser     = addresses.get("pauser",    owner)
        minter     = addresses.get("minter",    owner)
        tax_wallet = addresses.get("taxWallet", owner)

        types  = ["address", "address"]
        values = [recipient, owner]

        if features.get("whitelist"):
            if features.get("pausable"):
                types.append("address"); values.append(pauser)
            if features.get("mintable"):
                types.append("address"); values.append(minter)
        if features.get("taxable"):
            types.append("address"); values.append(tax_wallet)

        return "0x" + encode(types, values).hex()

    async def generate_creation_code(self, address, token_params):
        solidity_source = self.build_solidity_source(token_params)
        file_name       = f"{token_params['name']}Token.sol"
        sources         = await self.resolve_imports(file_name, solidity_source)
        compiled        = self.compile_solidity(token_params["name"], sources)

        addresses = {
            "recipient": address,
            "owner":     address,
        }

        features = {
            "whitelist": token_params.get("whitelist", False),
            "pausable":  token_params.get("pausable",  False),
            "mintable":  token_params.get("mintable",  False),
            "taxable":   token_params.get("taxable",   False),
        }
        encoded_args = self.encode_constructor_args(features, addresses)

        return "0x" + compiled["bytecode"] + encoded_args[2:]
        
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

    async def get_token_balance(self, address: str, asset=None):
        try:
            web3 = await self.get_web3_with_check(address)

            if asset is None:
                balance = await asyncio.to_thread(
                    web3.eth.get_balance,
                    address
                )
            else:
                contract_address = web3.to_checksum_address(asset)
                token_contract = web3.eth.contract(
                    address=contract_address,
                    abi=self.CONTRACT_ABI
                )

                balance = await asyncio.to_thread(
                    token_contract.functions.balanceOf(address).call
                )

            return web3.from_wei(balance, "ether")

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
    
    async def perform_transfer(self, private_key: str, address: str, recipient: str, amount: Decimal):
        try:
            web3 = await self.get_web3_with_check(address)

            amount_to_wei = web3.to_wei(amount, "ether")

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
                "nonce": nonce,
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
        
    async def perform_swap(self, private_key: str, address: str, pools: dict, amount: Decimal):
        try:
            web3 = await self.get_web3_with_check(address)

            token_in = web3.to_checksum_address(self.CONTRACT_ADDRESS['WX1T'])
            token_out = web3.to_checksum_address(self.CONTRACT_ADDRESS['USDT'])
            router = web3.to_checksum_address(self.CONTRACT_ROUTER['swap'])

            deadline = int(time.time()) + 600

            amount_in = web3.to_wei(amount, "ether")

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

            router_contract = web3.eth.contract(address=router, abi=self.CONTRACT_ABI)
            
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
        
    async def approving_token(self, private_key: str, address: str, asset: str, spender: str, amount_to_wei: int):
        try:
            web3 = await self.get_web3_with_check(address)
            
            token_contract = web3.eth.contract(address=asset, abi=self.CONTRACT_ABI)
            allowance = await asyncio.to_thread(
                token_contract.functions.allowance(address, spender).call
            )

            if allowance < amount_to_wei:
                approve_func = token_contract.functions.approve(spender, 2**256 - 1)

                estimated_gas = await asyncio.to_thread(
                    approve_func.estimate_gas,
                    {
                        "from": address
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

                approve_tx = await asyncio.to_thread(
                    approve_func.build_transaction,
                    {
                        "from": address,
                        "gas": int(estimated_gas * 1.2),
                        "maxFeePerGas": int(max_fee),
                        "maxPriorityFeePerGas": int(max_priority_fee),
                        "nonce": nonce,
                        "chainId": chain_id,
                    }
                )

                tx_hash = await self.send_raw_transaction_with_retries(private_key, web3, approve_tx)
                receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

                block_number = receipt.blockNumber
                explorer = self.API_URL["explorer"]

                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} Token Approved {Style.RESET_ALL}"
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
                
                await asyncio.sleep(random.uniform(3.0, 5.0))

            return True
        except Exception as e:
            raise Exception(f"Approving Token Contract Failed: {str(e)}")
        
    async def perform_add_liquidity(self, private_key: str, address: str, pools: dict, usdt_balance: float):
        try:
            web3 = await self.get_web3_with_check(address)

            token0 = web3.to_checksum_address(self.CONTRACT_ADDRESS['USDT'])
            token1 = web3.to_checksum_address(self.CONTRACT_ADDRESS['WX1T'])
            router = web3.to_checksum_address(self.CONTRACT_ROUTER['mint'])

            amount1_desired = web3.to_wei(self.LIQUIDITY_AMOUNT, "ether")

            amount0_desired = self.calc_amount_out_min(pools, "WX1T", amount1_desired)
            amount0_desired_from_wei = web3.from_wei(amount0_desired, "ether")

            self.log(
                f"{Fore.GREEN+Style.BRIGHT}      2. {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{amount0_desired_from_wei} USDT{Style.RESET_ALL}"
            )

            if usdt_balance < amount0_desired_from_wei:
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient USDT Token Balance {Style.RESET_ALL}"
                )
                return False

            await self.approving_token(private_key, address, token0, router, amount0_desired)

            deadline = int(time.time()) + 600

            mint_params = {
                "token0": token0,
                "token1": token1,
                "fee": 500,
                "tickLower": -887270,
                "tickUpper": 887270,
                "amount0Desired": amount0_desired,
                "amount1Desired": amount1_desired,
                "amount0Min": 0,
                "amount1Min": 0,
                "recipient": address,
                "deadline": deadline
            }

            router_contract = web3.eth.contract(address=router, abi=self.CONTRACT_ABI)
            
            mint_func = router_contract.functions.mint(mint_params)

            estimated_gas = await asyncio.to_thread(
                mint_func.estimate_gas,
                {
                    "from": address,
                    "value": amount1_desired
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

            mint_tx = await asyncio.to_thread(
                mint_func.build_transaction,
                {
                    "from": address,
                    "value": amount1_desired,
                    "gas": int(estimated_gas * 1.2),
                    "maxFeePerGas": int(max_fee),
                    "maxPriorityFeePerGas": int(max_priority_fee),
                    "nonce": nonce,
                    "chainId": chain_id,
                }
            )

            tx_hash = await self.send_raw_transaction_with_retries(private_key, web3, mint_tx)
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
        
    async def perform_deploy_token(self, private_key: str, address: str, token_params: dict):
        try:
            web3 = await self.get_web3_with_check(address)

            payable = web3.to_checksum_address(self.CONTRACT_ROUTER['payable']) 
            router = web3.to_checksum_address(self.CONTRACT_ROUTER['deploy'])

            amount_to_wei = web3.to_wei(self.DEPLOY_AMOUNT, "ether")

            creation_code = await self.generate_creation_code(address, token_params)

            creation_code_bytes = web3.to_bytes(hexstr=creation_code)

            router_contract = web3.eth.contract(address=router, abi=self.CONTRACT_ABI)

            deploy_func = router_contract.functions.sendAndDeploy(payable, amount_to_wei, creation_code_bytes)

            estimated_gas = await asyncio.to_thread(
                deploy_func.estimate_gas,
                {
                    "from": address,
                    "value": amount_to_wei
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

            deploy_tx = await asyncio.to_thread(
                deploy_func.build_transaction,
                {
                    "from": address,
                    "value": amount_to_wei,
                    "gas": int(estimated_gas * 1.2),
                    "maxFeePerGas": int(max_fee),
                    "maxPriorityFeePerGas": int(max_priority_fee),
                    "nonce": nonce,
                    "chainId": chain_id,
                }
            )

            tx_hash = await self.send_raw_transaction_with_retries(private_key, web3, deploy_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

            token_address = web3.to_checksum_address(receipt["logs"][1]["address"])

            return {
                "tx_hash": tx_hash, 
                "block_number": receipt.blockNumber,
                "token_address": token_address,
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
                headers["Authorization"] = self.accounts[address]["tokens"]["base"]
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
                headers["Authorization"] = self.accounts[address]["tokens"]["base"]
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
                headers["Authorization"] = self.accounts[address]["tokens"]["base"]
                headers["Content-Type"] = "application/json"
                params = {
                    "address": address
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, params=params, proxy=proxy, proxy_auth=proxy_auth) as response:
                        
                        if response.status == 500:
                            resp_text = await response.text()
                            self.log(
                                f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                                f"{Fore.RED+Style.BRIGHT} {resp_text} {Style.RESET_ALL}"
                            )

                            if "Please try again later." in resp_text: 
                                return True

                            elif "Something went wrong" in resp_text:
                                raise Exception(resp_text)

                            self.log(
                                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                                f"{Fore.YELLOW+Style.BRIGHT} Failed to Request Faucet {Style.RESET_ALL}"
                            )
                            return False
                        
                        await self.ensure_ok(response)

                        self.log(
                            f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                            f"{Fore.GREEN+Style.BRIGHT} Requested Successfully {Style.RESET_ALL}"
                        )
                        return True
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
    
    async def complete_quest(self, address: str, quest_id: str, proxy_url=None, retries=60):
        url = f"{self.API_URL['testnet']}/quests"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Authorization"] = self.accounts[address]["tokens"]["base"]
                headers["Content-Type"] = "application/json"
                params = {
                    "quest_id": quest_id
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, params=params, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
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
    
    async def auth_nonce(self, address: str, proxy_url=None, retries=60):
        url = f"{self.API_URL['constructor']}/api/v1/auth/nonce"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address, "constructor")
                params = {
                    "address": address
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, params=params, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Failed to Fetch Auth Nonce {Style.RESET_ALL}"
                )

        return None
    
    async def auth_verify(self, private_key: str, address: str, message: str, proxy_url=None, retries=60):
        url = f"{self.API_URL['constructor']}/api/v1/auth/verify"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address, "constructor")
                headers["Content-Type"] = "application/json"
                payload = {
                    "message": message,
                    "signature": self.generate_signature(private_key, message)
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, json=payload, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Failed to Auth Verify {Style.RESET_ALL}"
                )

        return None
    
    async def save_contracts(self, address: str, token_name: str, token_address: str, proxy_url=None, retries=60):
        url = f"{self.API_URL['constructor']}/api/v1/contracts"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address, "constructor")
                headers["Authorization"] = f"Bearer {self.accounts[address]['tokens']['constructor']}"
                headers["Content-Type"] = "application/json"
                payload = {
                    "address": token_address,
                    "features": "ERC20 Token",
                    "name": token_name,
                    "owner": address
                }

                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, json=payload, proxy=proxy, proxy_auth=proxy_auth) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Message  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Failed to Save Contract {Style.RESET_ALL}"
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

        self.accounts[address]["tokens"]["base"] = auth_sign.get("token")

        user_data = auth_sign.get("user", {})
        linked_accounts = user_data.get("linked_accounts", [])
        self.accounts[address]["linked_types"] = {
            acc.get("accountType") for acc in linked_accounts
        }

        self.log(
            f"{Fore.CYAN+Style.BRIGHT}Login   :{Style.RESET_ALL}"
            f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
        )

        return True
        
    async def process_auth_verify(self, private_key: str, address: str, proxy_url=None):
        auth_nonce = await self.auth_nonce(address, proxy_url)
        if not auth_nonce: return False

        nonce = auth_nonce.get("nonce")

        message = self.generate_constructor_msg(address, nonce)

        verify = await self.auth_verify(private_key, address, message, proxy_url)
        if not verify: return False

        self.accounts[address]["tokens"]["constructor"] = verify.get("token")

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

        await asyncio.sleep(3)

        return True
    
    async def process_perform_transfer(self, private_key: str, address: str):
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Token    :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} X1T {Style.RESET_ALL}"
        )
        recipient = self.generate_random_recipient()
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Recipient:{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {recipient} {Style.RESET_ALL}"
        )
        balance = await self.get_token_balance(address)
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} X1T {Style.RESET_ALL}"
        )

        if balance is None:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Failed to Fetch X1T Token Balance {Style.RESET_ALL}"
            )
            return False

        amount = Decimal(str(balance)) * self.SEND_PERCENT / Decimal(100)
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Amount   :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {amount} X1T ({self.SEND_PERCENT}%) {Style.RESET_ALL}"
        )

        transfer = await self.perform_transfer(private_key, address, recipient, amount)
        if not transfer: return False

        block_number = transfer["block_number"]
        tx_hash = transfer["tx_hash"]
        explorer = self.API_URL["explorer"]

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
            f"{Fore.WHITE+Style.BRIGHT} {explorer}{tx_hash} {Style.RESET_ALL}"
        )

        await asyncio.sleep(3)

        return True
    
    async def process_perform_swap(self, private_key: str, address: str, proxy_url=None):
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Pairs    :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} X1T to USDT {Style.RESET_ALL}"
        )

        pools = await self.pool_by_tokens(address, proxy_url)
        if not pools: return False

        balance = await self.get_token_balance(address)
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} X1T {Style.RESET_ALL}"
        )

        if balance is None:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Failed to Fetch X1T Token Balance {Style.RESET_ALL}"
            )
            return False

        amount = Decimal(str(balance)) * self.SWAP_PERCENT / Decimal(100)
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Amount   :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {amount} X1T ({self.SWAP_PERCENT}%) {Style.RESET_ALL}"
        )

        swap = await self.perform_swap(private_key, address, pools, amount)
        if not swap: return False

        block_number = swap["block_number"]
        tx_hash = swap["tx_hash"]
        explorer = self.API_URL["explorer"]

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
            f"{Fore.WHITE+Style.BRIGHT} {explorer}{tx_hash} {Style.RESET_ALL}"
        )

        await asyncio.sleep(3)

        return True
    
    async def process_perform_add_liquidity(self, private_key: str, address: str, proxy_url=None):
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Pools    :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} X1T/USDT {Style.RESET_ALL}"
        )

        pools = await self.pool_by_tokens(address, proxy_url)
        if not pools: return False

        self.log(f"{Fore.BLUE+Style.BRIGHT}   Balance  :{Style.RESET_ALL}")

        x1t_balance = await self.get_token_balance(address)
        self.log(
            f"{Fore.GREEN+Style.BRIGHT}      1. {Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT}{x1t_balance} X1T{Style.RESET_ALL}"
        )

        if x1t_balance is None:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Failed to Fetch X1T Token Balance {Style.RESET_ALL}"
            )
            return False

        usdt_balance = await self.get_token_balance(address, self.CONTRACT_ADDRESS["USDT"])
        self.log(
            f"{Fore.GREEN+Style.BRIGHT}      2. {Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT}{usdt_balance} USDT{Style.RESET_ALL}"
        )
        
        if usdt_balance is None:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Failed to Fetch USDT Token Balance {Style.RESET_ALL}"
            )
            return False
        
        self.log(f"{Fore.BLUE+Style.BRIGHT}   Amount   :{Style.RESET_ALL}")
        self.log(
            f"{Fore.GREEN+Style.BRIGHT}      1. {Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT}{self.LIQUIDITY_AMOUNT} X1T{Style.RESET_ALL}"
        )
        
        if x1t_balance < self.LIQUIDITY_AMOUNT:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Insufficient X1T Token Balance {Style.RESET_ALL}"
            )
            return False

        add_lp = await self.perform_add_liquidity(private_key, address, pools, usdt_balance)
        if not add_lp: return False

        block_number = add_lp["block_number"]
        tx_hash = add_lp["tx_hash"]
        explorer = self.API_URL["explorer"]

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
            f"{Fore.WHITE+Style.BRIGHT} {explorer}{tx_hash} {Style.RESET_ALL}"
        )

        await asyncio.sleep(3)

        return True
    
    async def process_perform_deploy_token(self, private_key: str, address: str, proxy_url=None):
        if not await self.process_auth_verify(private_key, address, proxy_url):
            return False
        
        token_params = self.generate_token_params()
        token_name = token_params["name"]
        token_symbol = token_params["symbol"]
        premint = token_params["premintAmount"]

        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Name     :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {token_name} {Style.RESET_ALL}"
        )
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Symbol   :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {token_symbol} {Style.RESET_ALL}"
        )
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Premint  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {premint} {token_symbol} {Style.RESET_ALL}"
        )

        balance = await self.get_token_balance(address)
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Balance  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} X1T {Style.RESET_ALL}"
        )

        if balance is None:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Failed to Fetch X1T Token Balance {Style.RESET_ALL}"
            )
            return False

        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Amount   :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {self.DEPLOY_AMOUNT} X1T {Style.RESET_ALL}"
        )

        if balance <= self.DEPLOY_AMOUNT:
            self.log(
                f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} Insufficient X1T Token Balance {Style.RESET_ALL}"
            )
            return False

        deploy = await self.perform_deploy_token(private_key, address, token_params)
        if not deploy: return False

        token_address = deploy["token_address"]
        block_number = deploy["block_number"]
        tx_hash = deploy["tx_hash"]
        explorer = self.API_URL["explorer"]

        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
            f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
        )
        self.log(
            f"{Fore.BLUE+Style.BRIGHT}   Address  :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {token_address} {Style.RESET_ALL}"
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

        if not await self.save_contracts(address, token_name, token_address, proxy_url):
            return False

        await asyncio.sleep(3)

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
            requirements = quest.get("requirements")
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

                if requirements:
                    linked_types = self.accounts[address].get("linked_types", set())
                    skip_reason = None

                    if requirements.get("linked_twitter") and "x" not in linked_types:
                        skip_reason = "X (Twitter) account not linked"
                    elif requirements.get("linked_discord") and "discord" not in linked_types:
                        skip_reason = "Discord account not linked"

                    if skip_reason:
                        self.log(
                            f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                            f"{Fore.YELLOW+Style.BRIGHT} Skipped - {skip_reason} {Style.RESET_ALL}"
                        )
                        continue

            elif periodicity == "daily":
                if is_completed_today:
                    self.log(
                        f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Already Completed {Style.RESET_ALL}"
                    )
                    continue

            if type in ["nomis", "symbiosis"]:
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT}   Status   :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Skipped {Style.RESET_ALL}"
                )
                continue

            elif type == "faucet":
                if not await self.process_request_faucet(address, proxy_url): continue

            elif type == "transfer":
                if not await self.process_perform_transfer(private_key, address): continue

            elif type == "swap":
                if not await self.process_perform_swap(private_key, address, proxy_url): continue

            elif type == "liquidity":
                if not await self.process_perform_add_liquidity(private_key, address, proxy_url): continue

            elif type == "tc":
                if not await self.process_perform_deploy_token(private_key, address, proxy_url): continue

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
                            "user_agent": random.choice(self.USER_AGENTS),
                            "tokens": {}
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
        sys.exit(0)