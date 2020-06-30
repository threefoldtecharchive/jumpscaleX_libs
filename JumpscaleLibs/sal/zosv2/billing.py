from stellar_sdk.exceptions import BadRequestError
from decimal import Decimal

# TFT_ISSUER on production
TFT_ISSUER_PROD = "GBOVQKJYHXRR3DX6NOX2RRYFRCUMSADGDESTDNBDS6CDVLGVESRTAC47"
# TFT_ISSUER on testnet
TFT_ISSUER_TEST = "GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3"
ASSET_CODE = "TFT"


class InsufficientFunds(Exception):
    pass


class MissingTrustLine(Exception):
    pass


class Billing:
    def payout_farmers(self, client, reservation_response):
        """
        payout farmer based on the resources per node used
        :param client: stellar wallet client
        :type client: j.clients.stellar
        :param reservation_response: reservation create response
        :type reservation_response: tfgrid.workloads.reservation.create.1
        """
        # TODO check the wallet client use the right asset to pay the reservation

        transaction_hashes = []
        reservation_id = reservation_response.reservation_id
        asset = reservation_response.escrow_information.asset
        total_amount = sum([d.total_amount for d in reservation_response.escrow_information.details])
        escrow_address = reservation_response.escrow_information.address

        total_amount_dec = Decimal(total_amount) / Decimal(1e7)
        total_amount = "{0:f}".format(total_amount_dec)

        escrow_address = reservation_response.escrow_information.address
        for balance in client.get_balance().balances:
            if f"{balance.asset_code}:{balance.asset_issuer}" == asset:
                if total_amount_dec > Decimal(balance.balance):
                    raise InsufficientFunds(f"Wallet {client.name} does not have enough funds to pay for {total_amount_dec:0f} {asset}")
                break
        else:
            raise MissingTrustLine(f"Wallet {client.name} does not have a valid trustline to pay for {asset}")
        try:
            txhash = client.transfer(escrow_address, total_amount, asset=asset, memo_text=str(reservation_id))
            transaction_hashes.append(txhash)
        except BadRequestError as e:
            raise e

        return transaction_hashes
