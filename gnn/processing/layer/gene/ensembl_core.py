class EnsCore:



    def __init__(self):
        pass



    def regulatory_url(self, start, end, coord_sys):
        return f"https://rest.ensembl.org/overlap/region/homo_sapiens/chr{coord_sys}:{start}-{end}?feature=regulatory"