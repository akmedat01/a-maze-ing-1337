from typing import Any, Dict


class Parsing:
    @classmethod
    def read_file(cls, filename: str) -> Dict[str, str]:
        config = {}
        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    key, value = line.split("=", 1)
                    config[key] = value
                except ValueError:
                    raise ValueError("Added keys should"
                                     "contain key-value format")
        return config

    @classmethod
    def parse_config(cls, config: Dict[str, str]) -> Dict[str, Any]:
        width = int(config["WIDTH"])
        height = int(config["HEIGHT"])

        entry_col, entry_row = map(int, config["ENTRY"].split(","))
        exit_col, exit_row = map(int, config["EXIT"].split(","))

        output_file = config["OUTPUT_FILE"]
        perfect_str = config["PERFECT"]
        if perfect_str == "True":
            perfect = True
        else:
            perfect = False
        output = {
            "width": width,
            "height": height,
            "entry": (entry_row, entry_col),
            "exit": (exit_row, exit_col),
            "output": output_file,
            "perfect": perfect
        }
        if "SEED" in config:
            output.update({"seed": config["seed"]})
        if "ALGO" in config:
            output.update({"algo": config["algo"]})
        return output
