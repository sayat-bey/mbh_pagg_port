from netmiko import ConnectHandler


#######################################################################################
# ------------------------------ classes part ----------------------------------------#
#######################################################################################


class CiscoXR:

    def __init__(self, ip, host):
        self.hostname = host
        self.ip_address = ip
        self.os_type = "cisco_xr"
        self.ssh_conn = None

        self.connection_status = True           # failed connection status, False if connection fails
        self.connection_error_msg = None        # connection error message

        self.show_platform_log = None
        self.show_inf_summary_log = None
        self.show_inf_description_log = None
        self.uplink = 0

        self.description_all = []
        self.description_exc_updown = []
        self.description_short = []

        self.platform = {"slot_zero": "N/A",                 # A9K-MPA-20X1GE
                         "slot_one": "N/A",                  # A9K-MPA-2X10GE
                         "slot_two": "BUILT_IN_4x10GE",
                         "0/FT0/SP": "N/A",
                         "0/PM0/0/SP": "N/A",
                         "0/PM0/1/SP": "N/A",
                         }

        self.tengig = {"total": None,
                       "up": None,
                       "down": None,
                       "admin down": None,
                       "total_description": 0,
                       "down_description": 0}

        self.gig = {"total": None,
                    "up": None,
                    "down": None,
                    "admin down": None,
                    "total_description": 0,
                    "down_description": 0}

        self.show_errors = {"show_platform": 0,
                            "show_inf_summary": 0,
                            "show_inf_description": 0}

    def connect(self, myusername, mypassword):
        self.ssh_conn = ConnectHandler(device_type=self.os_type,
                                       ip=self.ip_address,
                                       username=myusername,
                                       password=mypassword)

    def disconnect(self):
        self.ssh_conn.disconnect()

    def show_platform(self):
        self.show_platform_log = self.ssh_conn.send_command(r"admin show platform")

    def show_inf_summary(self):
        self.show_inf_summary_log = self.ssh_conn.send_command(r"show interfaces summary")

    def show_inf_description(self):
        self.show_inf_description_log = self.ssh_conn.send_command(r"show interfaces description")

    def reset(self):
        self.connection_status = True
        self.connection_error_msg = None
        self.show_platform_log = None
        self.show_inf_summary_log = None
        self.show_inf_description_log = None
