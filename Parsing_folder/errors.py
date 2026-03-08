

class error_handeling:
    madatory_keys = ["WIDTH", "HEIGHT", "ENTRY",
                     "EXIT", "OUTPUT_FILE", "PERFECT"]

    @classmethod
    def check_mandatory_keys(cls, config):
        """
        this function tries to find all the mandatory
        keys inside the file and raise a valueError if one
        of them is missing
        """
        if "WIDTH" not in config.keys():
            raise ValueError("WIDTH key missing")
        if "HEIGHT" not in config.keys():
            raise ValueError("HEIGHT key missing")
        if "ENTRY" not in config.keys():
            raise ValueError("ENTRY key missing")
        if "EXIT" not in config.keys():
            raise ValueError("EXIT key missing")
        if "OUTPUT_FILE" not in config.keys():
            raise ValueError("OUTPUT_FILE key missing")
        if "PERFECT" not in config.keys():
            raise ValueError("PERFECT key missing")

    @classmethod
    def check_mandatory_values(cls, config):
        """
        this function tries to find all the mandatory
        values inside the file and raise a valueError if one
        of them is not the required one or missing
        """
        for key, value in config.items():
            if key == "WIDTH":
                try:
                    int(value)
                except ValueError:
                    raise ValueError(f"Invalid Width value: {value}")

            elif key == "HEIGHT":
                try:
                    int(value)
                except ValueError:
                    raise ValueError(f"Invalid Height value: {value}")

            elif key == "ENTRY":
                try:
                    value1, value2 = value.split(",")
                    int(value1)
                    int(value2)
                except ValueError:
                    raise ValueError(f"Invalid Entry values {value}")

            elif key == "EXIT":
                try:
                    value1, value2 = value.split(",")
                    int(value1)
                    int(value2)
                except ValueError:
                    raise ValueError(f"Invalid Exit values {value}")

            elif key == "OUTPUT_FILE":
                str1, str2 = value.split(".")
                if ((len(str1) <= 0 or len(str2) <= 0) or
                        (not value.endswith(".txt"))):
                    raise ValueError(f"Invalid output file {value}")

            elif key == "PERFECT":
                if value != "True" and value != "False":
                    raise ValueError(f"Invalid Perfect value {value}")

    @classmethod
    def check_boundries(cls, config):
        pass

    @classmethod
    def check_added_keys(cls, config):
        """
        this function tries check the added keys if they have the
        key-value format
        """
        try:
            for key, value in config.items():
                if key not in cls.madatory_keys:
                    if not key or not value:
                        raise ValueError("Added keys should "
                                         "contain key-value format")
        except ValueError:
            raise ValueError("Added keys should "
                             "contain key-value format")
