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
j.clients.stellar.my_wallet.transfer('<destination address>',"1000", asset="TFT:GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3", locked_until=time.time()+10*60)

'AAAAAAbKy5zVPcXiRCYKwpv6SkIXXJRCV97nwH9PtRniy+7fAAAAZAADNQcAAAADAAAAAQAAAABeQs2iAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAAAAAAAAAAAAAAAAAAB4svu3wAAAEAE6w7jduF+Vx0zwKTlLkxCSaogT/q3nyso1VowS0tL6mLFJ0/+afCe4dbubvzXy9AuBbaF9h0vgslESCey0IcB'
```
The returned value is the unlocktransaction

## checking the balance of an account

```python
JSX> j.clients.stellar.my_wallet.get_balance()
Balances
  1000.0000000 TFT:GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3
  9999.9999900 XLM
Locked balances:
 - Escrow account GADMVS442U64LYSEEYFMFG72JJBBOXEUIJL55Z6AP5H3KGPCZPXN6MHD with unknown unlockhashes ['TDTGRL5ZDC6JLYP2GCSFRQONSH7JP7BA4HKFHO2UMLTLBXOQZN2AHXGY']
- 1000.0000000 TFT:GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3
- 3.9999600 XLM
```

after adding the unlock transaction:

```python
JSX> j.clients.stellar.my_wallet.set_unlock_transaction('AAAAAAbKy5zVPcXiRCYKwpv6SkIXXJRCV97nwH9PtRniy+7fAAAAZAADNQcAAAADAAAAAQAAAABeQs2iAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAAAAAAAAAAAAAAAAAAB4svu3wAAAEAE6w7jduF+Vx0zwKTlLkxCSaogT/q3nyso1VowS0tL6mLFJ0/+afCe4dbubvzXy9AuBbaF9h0vgslESCey0IcB')
JSX> j.clients.stellar.my_wallet.get_balance()
Balances
  1000.0000000 TFT:GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3
  9999.9999900 XLM
Locked balances:
 - Locked until February 11 2020 15:52:02 on escrow account GADMVS442U64LYSEEYFMFG72JJBBOXEUIJL55Z6AP5H3KGPCZPXN6MHD
- 1000.0000000 TFT:GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3
- 3.9999600 XLM

```

## claim locked funds

When the proper unlock transaction is added to the wallet, the funds can be claimed

```python
JSX> j.clients.stellar.my_wallet.set_unlock_transaction('AAAAAAbKy5zVPcXiRCYKwpv6SkIXXJRCV97nwH9PtRniy+7fAAAAZAADNQcAAAADAAAAAQAAAABeQs2iAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAABAAAAAQAAAAEAAAABAAAAAQAAAAEAAAAAAAAAAAAAAAAAAAAB4svu3wAAAEAE6w7jduF+Vx0zwKTlLkxCSaogT/q3nyso1VowS0tL6mLFJ0/+afCe4dbubvzXy9AuBbaF9h0vgslESCey0IcB')
JSX> j.clients.stellar.my_wallet.claim_locked_funds()
JSX> j.clients.stellar.my_wallet.get_balance()
Balances
  2000.0000000 TFT:GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3
  10003.9999100 XLM
```
