from scripts.helpful_scripts import get_account
from brownie import interface, config, network

def main():
    get_weth()

def get_weth():
    account = get_account()
    weth = interface.WethInterface(config["networks"][network.show_active()]["weth_token"])
    tx = weth.deposit({"from": account, "value": 0.1*10**18,"allow_revert":True})
    amount = weth.balanceOf(account)
    tx.wait(1)
    print(f"Receved {amount} WETH!!!")


