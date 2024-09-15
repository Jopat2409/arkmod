import json

class ModDatabase:

    def __init__(self, mod_path: str) -> None:
        self.fp = mod_path
        with open(self.fp, "r") as f:
            self.data = json.load(f)

    def write_data(self) -> None:
        with open(self.fp, "w+") as f:
            json.dump(self.data, f, indent=2)

    def create_mod(self, mod_name: str, mod_dir: str, default_maps: list[str]) -> None:
        print(default_maps)
        self.data["Mods"].append({
            "ModDir": mod_dir,
            "Maps": default_maps,
            "Title": mod_name,
			"Description": "",
			"PreviewImage": "",
			"Visibility": "Public",
			"ChangeNotes": "",
			"ItemSeamId": "",
			"GUID": "",
			"Tags": ""
        })
        self.write_data()

