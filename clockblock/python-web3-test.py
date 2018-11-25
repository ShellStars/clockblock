from web3.auto import w3
from web3 import Web3
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
print(web3.eth.accounts)
print(web3.fromWei(web3.eth.getBalance('0x3aBd140fB042CEa695C323886b0873421e5F5109'),'ether'))