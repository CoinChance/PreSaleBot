

class TokenData:
    def __init__(self):
        self.status = False
        self.live_status = False
        self.name = None
        self.symbol = None
        self.web = None
        self.twitter = None
        self.telegram = None
        self.token_address = None
        self.supply = None
        #self.pool_address = None
        self.soft_cap = None
        self.start_time = None
        self.end_time = None
        self.lockup_time = None
        self.rate = None
        self.raised = None
        self.chain = None

    @staticmethod
    def pinksale_adapter(data_dict):
        token_data = TokenData()
        try:
            token_data.live_status = True if 'Sale live' in data_dict.get('Status', '') else False
            token_data.status = True 
            token_data.name = data_dict.get('Name', 'Not Available')
            token_data.symbol = data_dict.get('Symbol', 'Not Available')
            token_data.token_address = data_dict.get('Address', 'Not Available')
            token_data.supply = data_dict.get('Total supply', 'Not Available')
            token_data.soft_cap = data_dict.get('SoftCap', 'Not Available')
            token_data.start_time = data_dict.get('Start time', 'Not Available')
            token_data.end_time = data_dict.get('End time', 'Not Available')
            token_data.lockup_time = data_dict.get('Liquidity Lockup Time', 'Not Available')
            token_data.rate = data_dict.get('Current Rate', 'Not Available')
            token_data.raised = data_dict.get('Current raised', 'Not Available')
            token_data.chain = data_dict.get('Chain', 'Not Available')

            token_data.twitter = data_dict.get('Twitter', 'Not Available')
            token_data.telegram = data_dict.get('Telegram', 'Not Available')
            token_data.web = data_dict.get('Website', 'Not Available')
        except Exception as e:
            print(f"An error occurred while populating token data: {e}")
            # If an error occurs, set token_data status to False
            token_data.status = False
        return token_data

    @staticmethod
    def solanapad_adapter(data_dict):
        token_data = TokenData()
        try:
            token_data.live_status = True if 'Sale live' in data_dict.get('Status', '') else False
            token_data.status = True 
            token_data.name = data_dict.get('Name', 'Not Available')
            token_data.symbol = data_dict.get('Symbol', 'Not Available')
            token_data.token_address = data_dict.get('Address', 'Not Available')
            token_data.supply = data_dict.get('Total supply', 'Not Available')
            token_data.soft_cap = data_dict.get('Soft Cap', 'Not Available')
            token_data.start_time = data_dict.get('Start Time', 'Not Available')
            token_data.end_time = data_dict.get('End Time', 'Not Available')
            token_data.lockup_time = data_dict.get('Liquidity Lockup Time', 'Not Available')
            token_data.rate = data_dict.get('Current Rate', 'Not Available')
            token_data.raised = data_dict.get('Current raised', 'Not Available')
            token_data.chain = data_dict.get('Chain', 'Not Available')

            token_data.twitter = data_dict.get('Twitter', 'Not Available')
            token_data.telegram = data_dict.get('Telegram', 'Not Available')
            token_data.web = data_dict.get('Website', 'Not Available')
        except Exception as e:
            print(f"An error occurred while populating token data: {e}")
            # If an error occurs, set token_data status to False
            token_data.status = False
        return token_data
    
