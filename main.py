import time
import requests
import json
from hexbytes import HexBytes
from constant import *



def get_eth_limit(gas_price=0, gas_limit=ETH_GAS_LIMIT):
    try:
        if gas_price == 0:
            gas_price = get_gas_price(ETH_GAS_LEVEL)
        gwei = gas_price * gas_limit
        return gwei / pow(10, 9)
    except Exception as e:
        print("ethereum:get_eth_limit:" + str(e))
        return 0.34


def get_eth_balance(wallet_address):
    try:
        eth_balance = ETH_WEB3.eth.getBalance(wallet_address)
        eth_balance = ETH_WEB3.fromWei(eth_balance, 'ether')
        return float(eth_balance)
    except Exception as e:
        print("get_eth_balance:" + str(e))
        return 0


def get_contract_abi(contract_addr):
    while True:
        try:
            try:
                abi = ETH_CONTRACT_ABI[contract_addr]
                return abi
            except Exception as e:
                print("get_contract_abi:" + str(e))
                if USING_TEST_NET:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
                    response = requests.get('%s%s' % (ABI_ENDPOINT, contract_addr), headers=headers)
                else:
                    response = requests.get('%s%s' % (ABI_ENDPOINT, contract_addr))
                response_json = response.json()
                abi_json = json.loads(response_json['result'])
                result = json.dumps(abi_json)
                ETH_CONTRACT_ABI[contract_addr] = result
                return result
        except Exception as e:
            print("get_contract_abi: contract: " + contract_addr + " " + str(e))
            time.sleep(0.1)


def get_gas_price(level):
    while True:
        try:
            res = requests.get(ETH_GAS_URL).json()
            return int(res[level] / 10)
        except Exception as e:
            print("get_gas_price:" + str(e))
            time.sleep(1)


def get_token_balance(wallet_address, token='YFI'):
    try:
        if token == 'ETH':
            return get_eth_balance(wallet_address)
        contract_address = ETH_TOKEN_LIST[token]
        contract_abi = get_contract_abi(contract_address)
        contract_addr = Web3.toChecksumAddress(contract_address)
        contract = ETH_WEB3.eth.contract(contract_addr, abi=contract_abi)
        decimals = get_decimals_token(token)
        token_balance = contract.functions.balanceOf(
            ETH_WEB3.toChecksumAddress(wallet_address)).call() / pow(10, decimals)
        return float(token_balance)
    except Exception as e:
        print(token + ":get_token_balance:" + str(e))
        return 0


def get_decimals_token(token='YFI'):
    try:
        if ETH_TOKENS_INFO[token]['decimals'] == 0:
            if token == 'ETH':
                ETH_TOKENS_INFO[token]['decimals'] = 18
            else:
                contract_addr = Web3.toChecksumAddress(ETH_TOKEN_LIST[token])
                contract_abi = get_contract_abi(ETH_TOKEN_LIST[token])
                contract = ETH_WEB3.eth.contract(contract_addr, abi=contract_abi)
                ETH_TOKENS_INFO[token]['decimals'] = contract.functions.decimals().call()
        return ETH_TOKENS_INFO[token]['decimals']
    except Exception as e:
        print(token + ":get_decimals_token:" + str(e))
        return ETH_TOKENS_INFO[token]['decimals']


def transfer_eth(source_address, source_private_key, dest_address, amount, gas_limit, gas_price, wait=False):
    result = {'code': -1, 'tx': None, 'message': ''}
    try:
        eth_balance = get_eth_balance(source_address)
        eth_limit = gas_limit * gas_price / pow(10, 9)

        if eth_balance < amount + eth_limit:
            result['code'] = -3
            result['message'] = 'not enough money'
            result['tx'] = None
            return result

        # ---------- sign and do transaction ---------- #
        signed_txn = ETH_WEB3.eth.account.signTransaction(dict(
                        nonce=ETH_WEB3.eth.getTransactionCount(source_address),
                        gasPrice=ETH_WEB3.toWei(gas_price, 'gwei'),
                        gas=gas_limit,
                        to=dest_address,
                        value=ETH_WEB3.toWei(amount, 'ether')
                      ), private_key=source_private_key)
        txn_hash = ETH_WEB3.eth.sendRawTransaction(signed_txn.rawTransaction)

        # @FIXME ----- check if transaction is success ----- #
        if wait is True:
            txn_receipt = ETH_WEB3.eth.waitForTransactionReceipt(txn_hash, ETH_LIMIT_WAIT_TIME)
            if txn_receipt is None or 'status' not in txn_receipt or txn_receipt['status'] != 1 or 'transactionIndex' not in txn_receipt:
                result['code'] = -4
                result['message'] = 'waiting failed'
                result['tx'] = txn_hash.hex()
                return result
        result['code'] = 0
        result['message'] = ''
        result['tx'] = txn_hash.hex()
        return result
    except Exception as e:
        print("transfer_eth:" + str(e))
        result['code'] = -2
        result['message'] = str(e)
        result['tx'] = None
        return result


def transfer_token(source_address, source_private_key, dest_address, amount, gas_limit, gas_price, token='YFI', wait=False):
    result = {'code': -1, 'tx': None, 'message': ''}
    try:
        # ---------- get contract object ---------- #
        contract_addr = Web3.toChecksumAddress(ETH_TOKEN_LIST[token])
        contract_abi = get_contract_abi(ETH_TOKEN_LIST[token])
        contract = ETH_WEB3.eth.contract(contract_addr, abi=contract_abi)
        decimals = get_decimals_token(token)
        # ---------- check source wallet balance ---------- #
        source_balance = contract.functions.balanceOf(source_address).call()
        print(token + ':transfer_token : balance:' + str(source_balance) + " amount:" + str(amount) + ' decimals:' + str(decimals))
        if source_balance < amount * pow(10, decimals):
            result['code'] = -3
            result['message'] = 'not enough money'
            result['tx'] = None
            return result
        gwei = gas_price * gas_limit
        required_gas = gwei / pow(10, 9)
        if get_eth_balance(source_address) < required_gas:
            result['code'] = -4
            result['message'] = 'not enough gas'
            result['tx'] = None
            return result
        # ---------- make transaction hash object ---------- #
        tx_hash = contract.functions.transfer(dest_address, int(amount * pow(10, decimals))).buildTransaction({
            'chainId': 1,
            'gasPrice': ETH_WEB3.toWei(gas_price, 'gwei'),
            'gas': gas_limit,
            'nonce': ETH_WEB3.eth.getTransactionCount(source_address),
        })

        # ---------- sign and do transaction ---------- #
        signed_txn = ETH_WEB3.eth.account.signTransaction(tx_hash, private_key=source_private_key)
        txn_hash = ETH_WEB3.eth.sendRawTransaction(signed_txn.rawTransaction)
        if wait is True:
            txn_receipt = ETH_WEB3.eth.waitForTransactionReceipt(txn_hash, ETH_LIMIT_WAIT_TIME)
            if txn_receipt is None or 'status' not in txn_receipt or txn_receipt['status'] != 1 or 'transactionIndex' not in txn_receipt:
                result['code'] = -5
                result['message'] = 'waiting failed'
                result['tx'] = txn_hash.hex()
                return result
        result['code'] = 0
        result['message'] = ''
        result['tx'] = txn_hash.hex()
        return result
    except Exception as e:
        print(token + ":transfer_token:" + str(e))
        result['code'] = -2
        result['message'] = str(e)
        result['tx'] = None
        return result


def send_multi_addresses():
    gas_price = get_gas_price(ETH_GAS_LEVEL)
    for item in DESTINATION_AMOUNT:
        key = list(item.keys())[0]
        value = list(item.values())[0]
        try:
            if SOURCE_PRIVATE == '' or SOURCE_ADDRESS == '':
                print(
                    SEND_TOKEN + ":send_multi_addresses: source address or private key doesn't defined")
                continue
            if key.find('test') >= 0:
                print(
                    SEND_TOKEN + ':send_multi_addresses: source_private:' + SOURCE_PRIVATE + ', test_dest_address:' + key + ', amount:' + str(
                        value) + ', gas_price:' + str(gas_price))
                continue
            print(SEND_TOKEN + ':send_multi_addresses: source_private:' + SOURCE_PRIVATE + ', dest_address:' + key + ', amount:' + str(
                value) + ', gas_price:' + str(gas_price))
            if SEND_TOKEN == 'ETH':
                res = transfer_eth(SOURCE_ADDRESS, HexBytes(SOURCE_PRIVATE), key, value, ETH_GAS_MIN_LIMIT, gas_price, True)
                if res['code'] != 0:
                    print(SEND_TOKEN + ':send_multi_addresses:' + res['message'])
                else:
                    print(SEND_TOKEN + ':send_multi_addresses: tx:' + res['tx'])
            else:
                res = transfer_token(SOURCE_ADDRESS, HexBytes(SOURCE_PRIVATE), key, value, ETH_GAS_LIMIT, gas_price, SEND_TOKEN)
                if res['code'] != 0:
                    print(SEND_TOKEN + ':send_multi_addresses:' + res['message'])
                else:
                    print(SEND_TOKEN + ':send_multi_addresses: tx:' + res['tx'])
            time.sleep(0.1)
        except Exception as e:
            print("send_multi_addresses:" + str(e))
            time.sleep(1)


if __name__ == '__main__':
    send_multi_addresses()
