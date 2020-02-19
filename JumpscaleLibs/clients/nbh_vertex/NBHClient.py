import requests
from Jumpscale import j

from . import errors


JSConfigBase = j.baseclasses.object_config


def get_error_string(errval):
    for m in dir(errors):
        res = getattr(errors, m)
        if res == errval:
            return m
    return ""


def raise_if_error(data):
    error_string = ""
    if isinstance(data, str) or isinstance(data, int):
        error_string = get_error_string(str(data))
        if error_string:
            raise j.exceptions.RuntimeError(error_string)


class NBHClient(JSConfigBase):
    _SCHEMATEXT = """
    @url = jumpscale.nbh.client
    name** = "main"
    username = "" (S)
    password_ = "" (S)
    service_url = "" (S)
    """

    def _init(self, **kwargs):
        if not self.username or not self.password_:
            raise j.exceptions.Input("Need to specify both username and password_ to use the client")

        if not self.service_url:
            raise j.exceptions.Input("Need to specify the url to use the client")

        self._session = requests.session()

    def _request(self, endpoint, params):
        url = "{}/{}".format(self.service_url, endpoint)
        resp = self._session.get(url, params=params)

        resp.raise_for_status()

        resp_json = resp.json()
        data = j.data.serializers.json.loads(resp_json["d"])
        raise_if_error(data)
        return data

    def login(self):
        params = {"username": self.username, "password": self.password_}
        response = self._request("BackofficeLogin", params)
        raise_if_error(response["UserId"])
        return response

    def change_password(self, old_password, new_password, confirm_newpassword):
        """The ChangePassword operation is used to change the logged in Dealer password with new one

        :param old_password: dealer's old password
        :type old_password: string
        :param new_password: dealer's new password
        :type new_password: string
        :param confirm_newpassword: dealer's new password
        :type confirm_newpassword: string
        :return: true for success
        :rtype: bool
        """
        self.login()
        params = {"OldPW": old_password, "NewPW": new_password, "ConfirmNewPW": confirm_newpassword}
        return self._request("ChangePassword", params)

    def create_client(
        self,
        parent_id,
        first_name,
        second_name,
        third_name,
        last_name,
        username,
        password,
        phone,
        fax,
        mobile,
        tel_pw,
        pob,
        country,
        email,
        address,
        readonly_login,
        forcechange_password,
    ):
        """The CreateClient operation is used to initialize new client under the specific given parent ID.

        :param parent_id: Parent Identifier  which the new client will be under it
        :type parent_id: int
        :param first_name: client first name
        :type first_name: string
        :param second_name: client second name
        :type second_name: string
        :param third_name: client third name
        :type third_name: string
        :param last_name: client last name
        :type last_name: string
        :param username: username for the new client
        :type username: string
        :param password: password for the new client
        :type password: string
        :param phone: client phone number
        :type phone: string
        :param fax: client fax number
        :type fax: string
        :param mobile: client mobile number
        :type mobile: string
        :param tel_pw: client telephone password
        :type tel_pw: string
        :param pob: post office box
        :type pob: string
        :param country: client country
        :type country: string
        :param email: client email
        :type email: string
        :param address: client address
        :type address: string
        :param readonly_login: indicates if the client will only monitor the trades or not
        :type readonly_login: bool
        :param forcechange_password: indicates if the client will have to change the password after first login or not
        :type forcechange_password: bool
        :return: client identifier
        :rtype: int
        """
        self.login()
        params = {
            "ParentID": parent_id,
            "FirstName": first_name,
            "SecondName": second_name,
            "ThirdName": third_name,
            "LastName": last_name,
            "Username": username,
            "Password": password,
            "Phone": phone,
            "Fax": fax,
            "Mobile": mobile,
            "TelPW": tel_pw,
            "POB": pob,
            "Country": country,
            "Email": email,
            "Address": address,
            "ReadOnlyLogin": readonly_login,
            "ForceChangePassword": forcechange_password,
        }
        return self._request("CreateClient", params)

    def get_client_by_id(self, client_id):
        """The GetClientByID operation is used to get client information for a given client number.

        :param client_id: client number to get its information
        :type client_id: int
        :return: client information
        :rtype: dict
        """
        self.login()
        params = {"ClientID": client_id}
        response = self._request("GetClientByID", params)
        raise_if_error(response["ClientID"])

        return response

    def update_client_info(
        self,
        client_id,
        first_name,
        second_name,
        third_name,
        last_name,
        username,
        password,
        phone,
        fax,
        mobile,
        tel_pw,
        pob,
        country,
        email,
        address,
        readonly_login,
        forcechange_password,
    ):
        """The UpdateClientInfo operation is used to update information for a specific given client number.

        :param clinet_id: client number to be updated
        :type client_id: int
        :param first_name: client first name
        :type first_name: string
        :param second_name: client second name
        :type second_name: string
        :param third_name: client third name
        :type third_name: string
        :param last_name: client last name
        :type last_name: string
        :param username: username for the new client
        :type username: string
        :param password: password for the new client
        :type password: string
        :param phone: client phone number
        :type phone: string
        :param fax: client fax number
        :type fax: string
        :param mobile: client mobile number
        :type mobile: string
        :param tel_pw: client telephone password
        :type tel_pw: string
        :param pob: post office box
        :type pob: string
        :param country: client country
        :type country: string
        :param email: client email
        :type email: string
        :param address: client address
        :type address: string
        :param readonly_login: indicates if the client will only monitor the trades or not
        :type readonly_login: bool
        :param forcechange_password: indicates if the client will have to change the password after first login or not
        :type forcechange_password: bool
        :return: client identifier
        :rtype: int
        """
        self.login()
        params = {
            "ClientID": client_id,
            "FirstName": first_name,
            "SecondName": second_name,
            "ThirdName": third_name,
            "LastName": last_name,
            "Username": username,
            "Password": password,
            "Phone": phone,
            "Fax": fax,
            "Mobile": mobile,
            "TelPW": tel_pw,
            "POB": pob,
            "Country": country,
            "Email": email,
            "Address": address,
            "ReadOnlyLogin": readonly_login,
            "ForceChangePassword": forcechange_password,
        }
        return self._request("UpdateClientInfo", params)

    def create_account(
        self, client_id, account_id, account_type, is_demo, is_locked, dont_liquidate, is_margin, userdefined_date
    ):
        """CreateAccount operation is used to initialize new account at specific account type for the given client username.

        :param client_id: client ID to whom you want to create account for
        :type client_id: int
        :param account_id: initialized account number, 0 means generate ID automatically
        :type account_id: int
        :param account_type: creation account type. 1 for normal account type, 2 for coverage account type.
        :type account_type: int
        :param is_demo: to indicate if the account is demo or not
        :type is_demo: bool
        :param is_locked: to indicate if the account will be locked
        :type is_locked: bool
        :param dont_liquidate: don't liquidate when reach Liquidation Point
        :type dont_liquidate:  bool
        :param is_margin: to indicate if the account is margin account or not
        :type is_margin: bool
        :param user_defined_date: trade open time, defaults to "" which means now
        :type user_defined_date: str in format DD/MM/yyyy HH:mm:ss, optional
        :return: account number
        :rtype: int
        """
        self.login()
        params = {
            "ParentID": client_id,
            "AccountID": account_id,
            "AccountType": account_type,
            "IsDemo": is_demo,
            "IsLocked": is_locked,
            "DontLiquidate": dont_liquidate,
            "IsMargin": is_margin,
            "UserDefined": userdefined_date,
        }
        return self._request("CreateAccount", params)

    def get_account_by_id(self, account_id):
        """ GetAccountByID operation is used to get information about the given account number

        :param account_id: account id
        :type account_id: int
        """
        self.login()
        response = self._request("GetAccountByID", {"AccountId": account_id})
        raise_if_error(response["AccountID"])

        return response

    def get_client_ids(self, parent_id):
        self.login()
        response = self._request("GetClientsIDs", {"ParentID": parent_id})
        if len(response) == 1:
            raise_if_error(response[0])

        return response

    def get_accounts_ids(self, client_id):
        """The GetAccountsIDs operation is used to get the list of account/s Id/s  which are related to a given client number.

        :param client_id: valid client identifier
        :type client_id: int
        :return: list of account ids
        :rtype: list
        """
        self.login()
        params = {"ClientID": client_id}
        response = self._request("GetAccountsIDs", params)
        if len(response) == 1:
            raise_if_error(response[0])

        return response

    def account_info_report(self, client_id, is_paging=False):
        """The AccountInfoReport operation is used to get the account information report that shows the information for all accounts under the given client number.

        :param client_id: valid client identifier
        :type client_id: int
        :param is_paging: indicates that you're calling to get the remaining records. First call must be false, next must be true.
        :type is_paging: bool, optional
        :return: list of accounts info report
        :rtype: list
        """
        self.login()
        params = {"ClientID": client_id, "isPaging": is_paging}
        response = self._request("AccountInfoReport", params)
        if response and len(response) == 1:
            raise_if_error(response[0]["ClientID"])

        return response

    def account_status_report(self, client_id, account_type, is_paging=False):
        """The AccountInfoReport operation is used to get the account information report that shows the information for all accounts under the given client number.

        :param client_id: valid client identifier
        :type client_id: int
        :param account_type: type of account. 1 for Normal account, 2 for Coverage.
        :type account_type: int
        :param is_paging: indicates that you're calling to get the remaining records. First call must be false, next must be true.
        :type is_paging: bool, optional
        :return: list of accounts status report
        :rtype: list
        """
        self.login()
        params = {"ClientID": client_id, "AccountType": account_type, "isPaging": is_paging}
        response = self._request("AccountStatusReport", params)
        if response and len(response) == 1:
            raise_if_error(response[0]["ClientID"])
        return response

    def get_account_stmt(self, account_id, from_date, to_date):
        """The GetAccountStatement operation returns the given account statement between the starting date and ending date.

        :param account_id: id of the account to generate the statement for
        :type account_id: int
        :param from_date: starting date for account statement query. Must be in DD/MM/YYYY format.
        :type from_date: str
        :param to_date: ending date for account statement query. Must be in DD/MM/YYYY format.
        :type to_date: str
        """
        self.login()
        params = {"AccountID": account_id, "FromDate": from_date, "ToDate": to_date}
        response = self._request("GetAccountStmt", params)
        if response and len(response) == 2:
            raise_if_error(response[0])
        return response

    def new_position(self, account_id, buy_or_sell, amount, symbol_id, price, note="", user_defined_date=""):
        """The NewPosition operation is used to open a new position on specific a symbol for the given account number.

        :param account_id: valid account identifier to open position for
        :type account_id: int
        :param buy_or_sell: the open position type, 1 for buy and -1 for sell
        :type buy_or_sell: int
        :param amount: position lots value
        :type amount: int
        :param symbol_id: trade symbol identifier
        :type symbol_id: int
        :param price: open trade price value
        :type price: int
        :param note: string used to mark the open position, defaults to ""
        :type note: str, optional
        :param user_defined_date: trade open time, defaults to "" which means now
        :type user_defined_date: str in format DD/MM/yyyy HH:mm:ss, optional
        :return: the new position ticket number
        :rtype: [type]
        """
        self.login()
        params = {
            "AccountID": account_id,
            "BuySell": buy_or_sell,
            "Amount": amount,
            "SymbolID": symbol_id,
            "Price": price,
            "note": note,
            "UserDefinedData": user_defined_date,
        }
        return self._request("NewPosition", params)

    def close_position(
        self, account_id, ticket_id, amount, price, ref_ask_price, ref_bid_price, commission, user_defined_date=""
    ):
        """The ClosePosition operation is used to close the position that belongs to the given account number

        :param account_id: valid account identifier to open position for
        :type account_id: int
        :param ticket_id: the position number to be closed
        :type ticket_id: int
        :param amount: position amount to be closed
        :type amount: int
        :param price: at price value to close position on it
        :type price: int
        :param ref_ask_price: ask price value for the Reference Symbol
        :type ref_ask_price: int
        :param ref_bid_price: bid Price value for the reference Symbol
        :type ref_bid_price: int
        :param commission: the commision value to be used when closing the position
        :type commission: int
        :param user_defined_date: trade open time, defaults to "" which means now
        :type user_defined_date: str in format DD/MM/yyyy HH:mm:ss, optional
        :return: closed ticket number
        :rtype: int
        """
        self.login()
        params = {
            "AccountID": account_id,
            "TicketID": ticket_id,
            "Amount": amount,
            "Price": price,
            "RefAskPrice": ref_ask_price,
            "RefBidPrice": ref_bid_price,
            "Comm": commission,
            "UserDefinedDate": user_defined_date,
        }
        return self._request("ClosePosition", params)

    def detailed_openpositions_report(self, client_id, account_type, symbol_id=0, position_type=0, is_paging=False):
        """The DetailedOpenPositionsReport operation is used to get detailed open positions report that shows the open position details for all accounts
        under the given client number.

        :param client_id: valid client identifier to get report for
        :type client_id: int
        :param account_type: type of account to get account status report for. 1 for Normal Account, 2 for Coverage Account.
        :type account_type: int
        :param symbol_id: The report will show the open position detailed  for this symbol ID. Defaults to 0 means for all Symbol.
        :type symbol_id: int
        :param position_type: The report will shows the net open position details for this type. 0 for all, 1 for buy type, -1 for sell type. Defaults to 0.
        :type position_type: int
        :param is_paging: indicates that you're calling to get the remaining records. First call must be false, next must be true.
        :type is_paging: bool, optional
        :return: list of open positions
        :rtype: list
        """
        client = self.login()
        params = {
            "ClientID": client_id,
            "AccountType": account_type,
            "SymbolID": symbol_id,
            "PositionType": position_type,
            "isPaging": is_paging,
        }
        response = self._request("DetailedOpenPositionsReport", params)
        if response and len(response) == 1:
            raise_if_error(response[0]["ClientID"])

        return response

    def get_mw_symbols(self):
        """The GetMWSymbols operation is used to get market watch symbol setting
        :return:
        :rtype:
        """
        return self._request("GetMWSymbols", {})

    def get_mw_new_tick(self):
        """The GetMWNewTick operation is used to get the market watch symbol data if changed and returns a list of symbols
        which holds all symbols with their corresponding Bid/Ask, High/Low.
        :return:
        :rtype:
        """
        return self._request("GetMWNewTick", {})
