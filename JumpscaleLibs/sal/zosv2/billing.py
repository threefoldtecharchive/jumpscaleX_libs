from stellar_sdk.exceptions import BadRequestError

# TFT_ISSUER on production
TFT_ISSUER_PROD = "GBOVQKJYHXRR3DX6NOX2RRYFRCUMSADGDESTDNBDS6CDVLGVESRTAC47"
# TFT_ISSUER on testnet
TFT_ISSUER_TEST = "GA47YZA3PKFUZMPLQ3B5F2E3CJIB57TGGU7SPCQT2WAEYKN766PWIMB3"
ASSET_CODE = "TFT"


class Billing:
    def payout_farmers(self, client, reservation_response):
        """
        payout farmer based on the resources per node used
        :param client: stellar wallet client
        :type client: j.clients.stellar
        :param reservation_response: reservation create response
        :type reservation_response: tfgrid.workloads.reservation.create.1
        """
        asset = None
        if client.network == "TEST":
            asset = ASSET_CODE + ":" + TFT_ISSUER_TEST
        else:
            asset = ASSET_CODE + ":" + TFT_ISSUER_PROD

        # TODO check the wallet client use the right asset to pay the reservation

        transaction_hashes = []
        reservation_id = reservation_response.reservation_id
        escrow_informations = reservation_response.escrow_information
        total_amount = sum([d.total_amount for d in reservation_response.escrow_information.details])
        total_amount = total_amount / 10e6
        escrow_address = reservation_response.escrow_information.address
        try:
            txhash = client.transfer(escrow_address, total_amount, asset=asset, memo_text=str(reservation_id))
            transaction_hashes.append(txhash)
        except BadRequestError as e:
            raise e

        return transaction_hashes
