# Stellar client and wallet

## Create a new wallet

```python
# valid types for network: STD and TEST, by default it is set to STD
wallet = j.clients.tfchain.new('my_wallet', network='TEST')
# available as `j.clients.stellar.my_wallet` from now on
```

## restore a wallet from a secret

```python
# valid types for network: STD and TEST, by default it is set to STD
wallet = j.clients.tfchain.new('my_wallet', network='TEST', secret='S.....')
# available as `j.clients.stellar.my_wallet` from now on
```

## Trustlines

As an example, add a trustline to TFT:GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3 (TFT on testnet):

``` python
wallet.add_trustline('TFT','GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3')
```

and remove it again:

``` python
wallet.delete_trustline('TFT','GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3')
```

## Transferring assets

Send 1000 TFT to another address:

```python
j.clients.stellar.my_wallet.transfer('<destination address>',"1000", asset="TFT:GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3")
```

Send 1000 TFT to another address but time locked until within 10 minutes:

```python
j.clients.stellar.issuerwallet.transfer(j.clients.stellar.testwallet.address,"1000", asset="TFT:GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3", locked_until=time.time()+10*60)
```

## checking the balance of an account

```python
JSX> j.clients.stellar.testwallet.get_balance()
```
