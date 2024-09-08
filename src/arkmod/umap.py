from io import BufferedReader

def read_int(f):
    return int.from_bytes(f.read(4), 'little')

def read_int128(f):
    return int.from_bytes

def read_string(f, bytes=False):
    len_ = read_int(f)
    str_bytes = f.read(len_)
    return str_bytes if bytes else str_bytes.split(b"\x00")[0].decode('utf-8')

def read_custom_export(f):
    pass

class GenericTable:

    def __init__(self, f: BufferedReader, read_one: callable):
        self.length = read_int(f)
        self.offset = read_int(f)

        self.read_entry = read_one

        self.data = []
        self.byte_data = None

    def read_bytes(self, f, entry_length: int) -> None:
        if self.byte_data:
            return self.byte_data
        f.seek(self.offset)
        self.byte_data = f.read(self.length * entry_length)
        return self.byte_data

    def read(self, f) -> None:
        if self.data:
            return self.data
        f.seek(self.offset)
        self.data = [self.read_entry(f) for _ in range(self.length)]
        return self.data

    def __repr__(self) -> str:
        return str(self.data)

class ArkImport:

    BYTESIZE = 28

    def __init__(self, f: BufferedReader, nametable: GenericTable):

        self.names = nametable

        self.offset = f.tell()
        self.package_name = read_int(f)
        self.unknwon_2 = read_int(f)

        self.class_name = read_int(f)
        self.unknown_1 = read_int(f)
        self.parent_name = read_int(f)
        self.object_name = read_int(f)
        self.export_reference = read_int(f)


    def name(self, index) -> str:
        if not index:
            return None
        return self.names.data[index]

    def __repr__(self) -> str:
        return f"""
                ArkImport [{self.offset}](
                    Class: {self.name(self.class_name)},
                    Package: {self.name(self.package_name)},
                    Object: {self.name(self.object_name)},
                    Parent: {self.parent_name},
                    reference: {self.export_reference},
                    Unknown1: {self.unknown_1},
                    Unknown2: {self.unknwon_2}
                )"""

class ArkExport:

    BYTESIZE = 68

    def __init__(self, f: BufferedReader, nametable: GenericTable) -> None:
        self.names = nametable
        self.mystical_flags = read_int(f)
        self.tests = [read_int(f) for _ in range(16)]

        self.object_name = self.tests[2]
        self.object_index = self.tests[3]
        self.size = self.tests[5]
        self.offset = self.tests[6]

    def name(self, index) -> str:
        if not index:
            return None

        if index >= len(self.names.data):
            return str(index)

        return self.names.data[index]

    def get_object_name(self) -> str:
        return f"{self.name(self.object_name)}_{self.object_index or 0}"

    def __repr__(self) -> str:
        return f"""
                ArkExport(
                    Export UUID: {self.name(self.mystical_flags)},
                    Object Name: {self.get_object_name()}
                    Offset: {self.offset},
                    Size: {self.size}
                    Unknowns: {self.tests}
                )
                """
                    #{[f'Test{i}: {self.name(data)}' for i,data in enumerate(self.tests)]},

class UmapHeader:
    """Parses a header from a .umap file
    """

    def __init__(self, f: BufferedReader) -> None:
        assert read_int(f) == Umap.UMAP_MAGIC_NUMBER

        self.pkg_version = read_int(f)
        self.licencee_version = read_int(f)

        f.seek(41)
        self.name_table = GenericTable(f, read_one=read_string)

        self.export_table = GenericTable(f, read_one=lambda x: ArkExport(x, self.name_table))
        self.import_table = GenericTable(f, read_one=lambda x: ArkImport(x, self.name_table))


class UmapActor:

    def __init__(self, export_data: ArkExport, f: BufferedReader) -> None:
        self.components = {}
        f.seek(export_data.offset)

        print(f"Loading {export_data.get_object_name()} data {export_data.offset}")
        print(export_data.names.data)

        # Read components
        while(f.tell() - export_data.offset < export_data.size):

            comp = export_data.name(read_int(f))
            # Padding
            _ = read_int(f)
            comp_type = export_data.name(read_int(f))
            _ = read_int(f)
            if comp_type == "BoolProperty":
                _ = read_int(f)
                _ =read_int(f)
                self.components.update({comp: True})
                value = bool.from_bytes(f.read(1))
            else:
                value = export_data.name(read_int(f))
            print(f"{comp}: {comp_type}: {value}")



class Umap:

    UMAP_MAGIC_NUMBER = 2653586369

    def __init__(self, level: str) -> None:

        with open(level, "rb") as f:
            self.header = UmapHeader(f)

            self.names = self.header.name_table.read(f)

            self.imports = self.header.import_table.read(f)
            self.exports: list[ArkExport] = self.header.export_table.read(f)

            print(f"obj: {[e for e in self.imports]}")

            self.bulk_data = self.load_level_data(f)

    def load_level_data(self, f: BufferedReader):
        data = []

        for i in self.exports:
            name = i.get_object_name()
            if "Gen2_cave_1_volume" in name:
                actor = UmapActor(i, f)

def dump_umap_import_exports(path: str) -> None:

    name = path.split('\\')[-1].split('.')[0]

    with open(path, "rb") as f:
        header = UmapHeader(f)

        with open(f"{name}_imports.umap", "wb") as imports:
            imports.write(header.import_table.read_bytes(f, entry_length=ArkImport.BYTESIZE))

        with open(f"{name}_exports.umap", "wb") as exports:
            exports.write(header.export_table.read_bytes(f, entry_length=ArkExport.BYTESIZE))



if __name__ == "__main__":
    test = Umap("..\\..\\tests\\ATM_Gen2_Cave.umap")
    #dump_umap_import_exports("..\\..\\tests\\ATM_Gen2_Cave.umap")
