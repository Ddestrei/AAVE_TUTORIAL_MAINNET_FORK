from scripts.helpful_scripts import get_account
from brownie import network, config, interface
from brownie.network import gas_price, gas_limit
from brownie.network.gas.strategies import LinearScalingStrategy
from scripts.get_weth import get_weth
from web3 import Web3

gas_strategy = LinearScalingStrategy("10 gwei", "200 gwei", 1.125)
gas_price(gas_strategy)
gas_limit("1000000")

AMOUNT = Web3.toWei(0.1, "ether")


def main():
    account = get_account()

    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork"]:
        get_weth()

    lending_pool = get_lending_pool()
    print(lending_pool)

    approve_erc20(AMOUNT, lending_pool.address, erc20_address, account)

    print("Depositing...")

    tx = lending_pool.deposit(
        erc20_address,
        AMOUNT,
        account.address,
        0,
        {"from": account, "allow_revert": True},
    )
    tx.wait(1)
    print("Deposited!!!")

    available_borrow_eth, total_dept_eth = get_borrowable_data(lending_pool, account)
    link_eth_price = get_asset_price(
        config["networks"][network.show_active()]["eth_dai_price_feed"]
    )
    amount_dai_to_borrow = (available_borrow_eth * 0.95) / link_eth_price
    print(f"We are goint to borrow {amount_dai_to_borrow}")
    link_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        link_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account, "allow_revert": True},
    )
    borrow_tx.wait(1)
    print("We borrowed some DAI!!!")
    get_borrowable_data(lending_pool, account)
    repay_all(Web3.toWei(amount_dai_to_borrow, "ether"), lending_pool, account)


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print("You just repay all mayby!!!")


def get_asset_price(link_eth_price_address):
    link_eth_price_feed = interface.AggregatorV3Interface(link_eth_price_address)
    latest_price = link_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"DAI/ETH price is {converted_latest_price}")
    return float(converted_latest_price)


def get_borrowable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_dept_eth,
        available_borrow_eth,
        current_liguidation_treshhold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_dept_eth = Web3.fromWei(total_dept_eth, "ether")
    print(f"total_collateral_eth = {total_collateral_eth}")
    print(f"available_borrow_eth = {available_borrow_eth}")
    print(f"total_dept_eth = {total_dept_eth}")
    return (float(available_borrow_eth), float(total_dept_eth))


def approve_erc20(amount, spender, erc20_address, account):
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account, "allow_revert": True})
    tx.wait(1)
    print("Approved!!!")
    return tx


def get_lending_pool():
    lending_pool_address_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool"]
    )
    lending_pool_address = lending_pool_address_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
