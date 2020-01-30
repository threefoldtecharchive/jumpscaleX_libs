# Stellar client and wallet

## Create a new wallet

```python
# valid types for network: STD and TEST, by default it is set to STD
wallet = j.clients.tfchain.new('my_wallet', network='TEST')
# available as `j.clients.tfchain.my_wallet` from now on
```

## restore a wallet from a secret

```python
# valid types for network: STD and TEST, by default it is set to STD
wallet = j.clients.tfchain.new('my_wallet', network='TEST', secret='S.....')
# available as `j.clients.tfchain.my_wallet` from now on
```

## Trustlines

For example, add a trustline to TFT:GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3 (TFT on testnet):

``` python
wallet.add_trustline('TFT,'GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3')
```

and remove it again:

``` python
wallet.delete_trustline('TFT','GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3')
```
