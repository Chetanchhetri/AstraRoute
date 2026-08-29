import osmium

class MergeHandler(osmium.SimpleHandler):
    def __init__(self, writer):
        super().__init__()
        self.writer = writer

    def node(self, n):
        self.writer.add_node(n)

    def way(self, w):
        self.writer.add_way(w)

    def relation(self, r):
        self.writer.add_relation(r)

# Create writer for output merged PBF file
writer = osmium.SimpleWriter('ne_full.osm.pbf')

# Initialize handler and process both files
handler = MergeHandler(writer)
handler.apply_file('eastern-zone-260826.osm.pbf')
handler.apply_file('north-eastern-zone-260826.osm.pbf')

writer.close()
print("Successfully merged into ne_full.osm.pbf!")