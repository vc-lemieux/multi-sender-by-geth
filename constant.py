from config import *
from web3 import Web3


ETH_GAS_LIMIT = 100000  # 100000: testing mode, 1000000: production mode
ETH_GAS_MIN_LIMIT = 21000

if USING_TEST_NET:
    ETH_TOKEN_LIST = {'YFI': "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6",
                      'USDT': "0x3a9cC319b11c2dD10063EBb49aDa320A543055E2",
                      'WBTC': "0x6255F4Cdb6c08bcdA4cb7220ec71040D55e4F49f",
                      'ETH': ''}
else:
    ETH_TOKEN_LIST = {'YFI': "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e",
                      'USDT': "0xdac17f958d2ee523a2206206994597c13d831ec7",
                      'WBTC': "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
                      'ETH': ''}

if USING_TEST_NET:
    ETH_WEB3 = Web3(Web3.HTTPProvider(WEB3_ENDPOINT))
    ABI_ENDPOINT = 'https://api-goerli.etherscan.io/api?module=contract&action=getabi&address='
else:
    ETH_WEB3 = Web3()
    ABI_ENDPOINT = 'https://api.etherscan.io/api?module=contract&action=getabi&address='

ETH_CONTRACT_ABI = {}
ETH_TOKENS_INFO = {}
for token in ETH_TOKEN_LIST.keys():
    data = {'decimals': 0, 'contract': ETH_TOKEN_LIST[token]}
    ETH_TOKENS_INFO[token] = data
ETH_LIMIT_WAIT_TIME = 36000
ETH_GAS_URL = 'https://ethgasstation.info/api/ethgasAPI.json?api-key=' + GAS_TOKEN
