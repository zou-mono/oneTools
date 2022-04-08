from UICore import filegdbapi


class GeoDatabase(filegdbapi.Geodatabase):
    m_layers = []

    def __init__(self):
        super(GeoDatabase, self).__init__()
        self.table = filegdbapi.Table()

    def __OpenFGDBTables(self, layers):

    # def GetLayer(self, n):
