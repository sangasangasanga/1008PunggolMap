import csv
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_pydot import write_dot
import pydotplus
import os

class Vertex:
    def __init__(self, node, lon, lat):
        self.id = node
        self.adjacent = {}
        self.lon = lon
        self.lat = lat

    def __str__(self):
        return str(self.id) + ' adjacent: ' + str([x.id for x in self.adjacent])

    def add_neighbor(self, neighbor, weight=0):
        self.adjacent[neighbor] = weight

    def get_connections(self):
        return self.adjacent.keys()

    def get_id(self):
        return self.id
    def get_lon(self):
        return self.lon
    def get_lat(self):
        return self.lat
    def get_weight(self, neighbor):
        return self.adjacent[neighbor]

class Graph:
    def __init__(self):
        self.vert_dict = {}
        self.num_vertices = 0

    def __iter__(self):
        return iter(self.vert_dict.values())

    def add_vertex(self, node, lon, lat):
        self.num_vertices = self.num_vertices + 1
        new_vertex = Vertex(node, lon, lat)
        self.vert_dict[node] = new_vertex
        return new_vertex

    def get_vertex(self, n):
        if n in self.vert_dict:
            return self.vert_dict[n]
        else:
            return None

    def add_edge(self, frm, to, cost = 0):
        if frm not in self.vert_dict:
            self.add_vertex(frm)
        if to not in self.vert_dict:
            self.add_vertex(to)

        self.vert_dict[frm].add_neighbor(self.vert_dict[to], cost)

    def get_vertices(self):
        return self.vert_dict.keys()






os.environ["PATH"] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin/'
g = nx.DiGraph(directed=True)
adjlist = Graph()
with open('URTY.csv', 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_cnt = 0

    for row in csv_reader:  # loop to add all nodes with their lon and lat
        if line_cnt == 0:
            line_cnt += 1
        else:
            g.add_node(row[0], pos=(float(row[2]), float(row[1])))
            adjlist.add_vertex(row[0], row[2], row[1])

with open('URTY.csv', 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_cnt = 0
    for row in csv_reader:
        if line_cnt == 0:
            line_cnt += 1
        else:
            for i in range(3, len(row), 3):
                if (row[i] or row [i + 1]) != "":
                    g.add_weighted_edges_from([(row[0], row[i + 1], float(row[i]))])
                    adjlist.add_edge(row[0], row[i + 1], float(row[i]))



labels = nx.get_edge_attributes(g, 'weight')
pos = nx.get_node_attributes(g, 'pos')
nx.draw(g, pos, with_labels=True, arrows=True, node_size=10, node_color='black', edge_color='red',
        connectionstyle='arc3, rad =0.2')
nx.draw_networkx_edge_labels(g, pos, edge_labels=labels, alpha=0.5, width=10)
plt.show()

for v in adjlist:
    for w in v.get_connections():
        vid = v.get_id()
        wid = w.get_id()
        print('( %s , %s, %3d)' % (vid, wid, v.get_weight(w)))

for v in adjlist:
    print('adjlist.vert_dict[%s]=%s' % (v.get_id(), adjlist.vert_dict[v.get_id()]))
#write_dot(g,'test.dot')
#export = pydotplus.graph_from_dot_file('test.dot')
#export.write_svg('test.svg') # generate graph in svg.