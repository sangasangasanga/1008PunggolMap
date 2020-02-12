# vim:ts=4:sw=4:sts=4:et 
   2  # -*- coding: utf-8 -*- 
   3  """ 
   4  IGraph library. 
   5   
   6  @undocumented: deprecated, _graphmethod, _add_proxy_methods, _layout_method_wrapper, 
   7                 _3d_version_for 
   8  """ 
   9   
  10  from __future__ import with_statement 
  11   
  12  __license__ = u""" 
  13  Copyright (C) 2006-2012  Tamás Nepusz <ntamas@gmail.com> 
  14  Pázmány Péter sétány 1/a, 1117 Budapest, Hungary 
  15   
  16  This program is free software; you can redistribute it and/or modify 
  17  it under the terms of the GNU General Public License as published by 
  18  the Free Software Foundation; either version 2 of the License, or 
  19  (at your option) any later version. 
  20   
  21  This program is distributed in the hope that it will be useful, 
  22  but WITHOUT ANY WARRANTY; without even the implied warranty of 
  23  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
  24  GNU General Public License for more details. 
  25   
  26  You should have received a copy of the GNU General Public License 
  27  along with this program; if not, write to the Free Software 
  28  Foundation, Inc.,  51 Franklin Street, Fifth Floor, Boston, MA 
  29  02110-1301 USA 
  30  """ 
  31   
  32  # pylint: disable-msg=W0401 
  33  # W0401: wildcard import 
  34  from igraph._igraph import * 
  35  from igraph.clustering import * 
  36  from igraph.cut import * 
  37  from igraph.configuration import Configuration 
  38  from igraph.drawing import * 
  39  from igraph.drawing.colors import * 
  40  from igraph.datatypes import * 
  41  from igraph.formula import * 
  42  from igraph.layout import * 
  43  from igraph.matching import * 
  44  from igraph.statistics import * 
  45  from igraph.summary import * 
  46  from igraph.utils import * 
  47  from igraph.version import __version__, __version_info__ 
  48   
  49  import os 
  50  import math 
  51  import gzip 
  52  import sys 
  53  import operator 
  54   
  55  from collections import defaultdict 
  56  from itertools import izip 
  57  from shutil import copyfileobj 
  58  from warnings import warn 
  59   
  60 -def deprecated(message): 
  61      """Prints a warning message related to the deprecation of some igraph 
  62      feature.""" 
  63      warn(message, DeprecationWarning, stacklevel=3) 
  64   
  65  # pylint: disable-msg=E1101 
  66 -class Graph(GraphBase): 
  67      """Generic graph. 
  68   
  69      This class is built on top of L{GraphBase}, so the order of the 
  70      methods in the Epydoc documentation is a little bit obscure: 
  71      inherited methods come after the ones implemented directly in the 
  72      subclass. L{Graph} provides many functions that L{GraphBase} does not, 
  73      mostly because these functions are not speed critical and they were 
  74      easier to implement in Python than in pure C. An example is the 
  75      attribute handling in the constructor: the constructor of L{Graph} 
  76      accepts three dictionaries corresponding to the graph, vertex and edge 
  77      attributes while the constructor of L{GraphBase} does not. This extension 
  78      was needed to make L{Graph} serializable through the C{pickle} module. 
  79      L{Graph} also overrides some functions from L{GraphBase} to provide a 
  80      more convenient interface; e.g., layout functions return a L{Layout} 
  81      instance from L{Graph} instead of a list of coordinate pairs. 
  82   
  83      Graphs can also be indexed by strings or pairs of vertex indices or vertex 
  84      names.  When a graph is indexed by a string, the operation translates to 
  85      the retrieval, creation, modification or deletion of a graph attribute: 
  86   
  87        >>> g = Graph.Full(3) 
  88        >>> g["name"] = "Triangle graph" 
  89        >>> g["name"] 
  90        'Triangle graph' 
  91        >>> del g["name"] 
  92   
  93      When a graph is indexed by a pair of vertex indices or names, the graph 
  94      itself is treated as an adjacency matrix and the corresponding cell of 
  95      the matrix is returned: 
  96   
  97        >>> g = Graph.Full(3) 
  98        >>> g.vs["name"] = ["A", "B", "C"] 
  99        >>> g[1, 2] 
 100        1 
 101        >>> g["A", "B"] 
 102        1 
 103        >>> g["A", "B"] = 0 
 104        >>> g.ecount() 
 105        2 
 106   
 107      Assigning values different from zero or one to the adjacency matrix will 
 108      be translated to one, unless the graph is weighted, in which case the 
 109      numbers will be treated as weights: 
 110   
 111        >>> g.is_weighted() 
 112        False 
 113        >>> g["A", "B"] = 2 
 114        >>> g["A", "B"] 
 115        1 
 116        >>> g.es["weight"] = 1.0 
 117        >>> g.is_weighted() 
 118        True 
 119        >>> g["A", "B"] = 2 
 120        >>> g["A", "B"] 
 121        2 
 122        >>> g.es["weight"] 
 123        [1.0, 1.0, 2] 
 124      """ 
 125   
 126      # Some useful aliases 
 127      omega = GraphBase.clique_number 
 128      alpha = GraphBase.independence_number 
 129      shell_index = GraphBase.coreness 
 130      cut_vertices = GraphBase.articulation_points 
 131      blocks = GraphBase.biconnected_components 
 132      evcent = GraphBase.eigenvector_centrality 
 133      vertex_disjoint_paths = GraphBase.vertex_connectivity 
 134      edge_disjoint_paths = GraphBase.edge_connectivity 
 135      cohesion = GraphBase.vertex_connectivity 
 136      adhesion = GraphBase.edge_connectivity 
 137   
 138      # Compatibility aliases 
 139      shortest_paths_dijkstra = GraphBase.shortest_paths 
 140      subgraph = GraphBase.induced_subgraph 
 141   
 142 -    def __init__(self, *args, **kwds): 
 143          """__init__(n=0, edges=None, directed=False, graph_attrs=None, 
 144          vertex_attrs=None, edge_attrs=None) 
 145   
 146          Constructs a graph from scratch. 
 147   
 148          @keyword n: the number of vertices. Can be omitted, the default is 
 149            zero. Note that if the edge list contains vertices with indexes 
 150            larger than or equal to M{m}, then the number of vertices will 
 151            be adjusted accordingly. 
 152          @keyword edges: the edge list where every list item is a pair of 
 153            integers. If any of the integers is larger than M{n-1}, the number 
 154            of vertices is adjusted accordingly. C{None} means no edges. 
 155          @keyword directed: whether the graph should be directed 
 156          @keyword graph_attrs: the attributes of the graph as a dictionary. 
 157          @keyword vertex_attrs: the attributes of the vertices as a dictionary. 
 158            Every dictionary value must be an iterable with exactly M{n} items. 
 159          @keyword edge_attrs: the attributes of the edges as a dictionary. Every 
 160            dictionary value must be an iterable with exactly M{m} items where 
 161            M{m} is the number of edges. 
 162          """ 
 163          # Pop the special __ptr keyword argument 
 164          ptr = kwds.pop("__ptr", None) 
 165   
 166          # Set up default values for the parameters. This should match the order 
 167          # in *args 
 168          kwd_order = ( 
 169              "n", "edges", "directed", "graph_attrs", "vertex_attrs", 
 170              "edge_attrs" 
 171          ) 
 172          params = [0, [], False, {}, {}, {}] 
 173   
 174          # Is there any keyword argument in kwds that we don't know? If so, 
 175          # freak out. 
 176          unknown_kwds = set(kwds.keys()) 
 177          unknown_kwds.difference_update(kwd_order) 
 178          if unknown_kwds: 
 179              raise TypeError("{0}.__init__ got an unexpected keyword argument {1!r}".format( 
 180                  self.__class__.__name__, unknown_kwds.pop() 
 181              )) 
 182   
 183          # If the first argument is a list or any other iterable, assume that 
 184          # the number of vertices were omitted 
 185          args = list(args) 
 186          if len(args) > 0 and hasattr(args[0], "__iter__"): 
 187              args.insert(0, params[0]) 
 188   
 189          # Override default parameters from args 
 190          params[:len(args)] = args 
 191   
 192          # Override default parameters from keywords 
 193          for idx, k in enumerate(kwd_order): 
 194              if k in kwds: 
 195                  params[idx] = kwds[k] 
 196   
 197          # Now, translate the params list to argument names 
 198          nverts, edges, directed, graph_attrs, vertex_attrs, edge_attrs = params 
 199   
 200          # When the number of vertices is None, assume that the user meant zero 
 201          if nverts is None: 
 202              nverts = 0 
 203   
 204          # When 'edges' is None, assume that the user meant an empty list 
 205          if edges is None: 
 206              edges = [] 
 207   
 208          # When 'edges' is a NumPy array or matrix, convert it into a memoryview 
 209          # as the lower-level C API works with memoryviews only 
 210          try: 
 211              from numpy import ndarray, matrix 
 212              if isinstance(edges, (ndarray, matrix)): 
 213                  edges = numpy_to_contiguous_memoryview(edges) 
 214          except ImportError: 
 215              pass 
 216   
 217          # Initialize the graph 
 218          if ptr: 
 219              GraphBase.__init__(self, __ptr=ptr) 
 220          else: 
 221              GraphBase.__init__(self, nverts, edges, directed) 
 222   
 223          # Set the graph attributes 
 224          for key, value in graph_attrs.iteritems(): 
 225              if isinstance(key, (int, long)): 
 226                  key = str(key) 
 227              self[key] = value 
 228          # Set the vertex attributes 
 229          for key, value in vertex_attrs.iteritems(): 
 230              if isinstance(key, (int, long)): 
 231                  key = str(key) 
 232              self.vs[key] = value 
 233          # Set the edge attributes 
 234          for key, value in edge_attrs.iteritems(): 
 235              if isinstance(key, (int, long)): 
 236                  key = str(key) 
 237              self.es[key] = value 
 238   
 239 -    def add_edge(self, source, target, **kwds): 
 240          """add_edge(source, target, **kwds) 
 241   
 242          Adds a single edge to the graph. 
 243   
 244          Keyword arguments (except the source and target arguments) will be 
 245          assigned to the edge as attributes. 
 246   
 247          @param source: the source vertex of the edge or its name. 
 248          @param target: the target vertex of the edge or its name. 
 249   
 250          @return: the newly added edge as an L{Edge} object. Use 
 251              C{add_edges([(source, target)])} if you don't need the L{Edge} 
 252              object and want to avoid the overhead of creating t. 
 253          """ 
 254          eid = self.ecount() 
 255          self.add_edges([(source, target)]) 
 256          edge = self.es[eid] 
 257          for key, value in kwds.iteritems(): 
 258              edge[key] = value 
 259          return edge 
 260   
 261 -    def add_edges(self, es): 
 262          """add_edges(es) 
 263   
 264          Adds some edges to the graph. 
 265   
 266          @param es: the list of edges to be added. Every edge is represented 
 267            with a tuple containing the vertex IDs or names of the two 
 268            endpoints. Vertices are enumerated from zero. 
 269          """ 
 270          return GraphBase.add_edges(self, es) 
 271   
 272 -    def add_vertex(self, name=None, **kwds): 
 273          """add_vertex(name=None, **kwds) 
 274   
 275          Adds a single vertex to the graph. Keyword arguments will be assigned 
 276          as vertex attributes. Note that C{name} as a keyword argument is treated 
 277          specially; if a graph has C{name} as a vertex attribute, it allows one 
 278          to refer to vertices by their names in most places where igraph expects 
 279          a vertex ID. 
 280   
 281          @return: the newly added vertex as a L{Vertex} object. Use 
 282              C{add_vertices(1)} if you don't need the L{Vertex} object and want 
 283              to avoid the overhead of creating t. 
 284          """ 
 285          vid = self.vcount() 
 286          self.add_vertices(1) 
 287          vertex = self.vs[vid] 
 288          for key, value in kwds.iteritems(): 
 289              vertex[key] = value 
 290          if name is not None: 
 291              vertex["name"] = name 
 292          return vertex 
 293   
 294 -    def add_vertices(self, n): 
 295          """add_vertices(n) 
 296   
 297          Adds some vertices to the graph. 
 298   
 299          @param n: the number of vertices to be added, or the name of a single 
 300            vertex to be added, or a sequence of strings, each corresponding to the 
 301            name of a vertex to be added. Names will be assigned to the C{name} 
 302            vertex attribute. 
 303          """ 
 304          if isinstance(n, basestring): 
 305              # Adding a single vertex with a name 
 306              m = self.vcount() 
 307              result = GraphBase.add_vertices(self, 1) 
 308              self.vs[m]["name"] = n 
 309              return result 
 310          elif hasattr(n, "__iter__"): 
 311              m = self.vcount() 
 312              if not hasattr(n, "__len__"): 
 313                  names = list(n) 
 314              else: 
 315                  names = n 
 316              result = GraphBase.add_vertices(self, len(names)) 
 317              self.vs[m:]["name"] = names 
 318              return result 
 319          return GraphBase.add_vertices(self, n) 
 320   
 321 -    def adjacent(self, *args, **kwds): 
 322          """adjacent(vertex, mode=OUT) 
 323   
 324          Returns the edges a given vertex is incident on. 
 325   
 326          @deprecated: replaced by L{Graph.incident()} since igraph 0.6 
 327          """ 
 328          deprecated("Graph.adjacent() is deprecated since igraph 0.6, please use " 
 329                     "Graph.incident() instead") 
 330          return self.incident(*args, **kwds) 
 331   
 332 -    def as_directed(self, *args, **kwds): 
 333          """as_directed(*args, **kwds) 
 334   
 335          Returns a directed copy of this graph. Arguments are passed on 
 336          to L{Graph.to_directed()} that is invoked on the copy. 
 337          """ 
 338          copy = self.copy() 
 339          copy.to_directed(*args, **kwds) 
 340          return copy 
 341   
 342 -    def as_undirected(self, *args, **kwds): 
 343          """as_undirected(*args, **kwds) 
 344   
 345          Returns an undirected copy of this graph. Arguments are passed on 
 346          to L{Graph.to_undirected()} that is invoked on the copy. 
 347          """ 
 348          copy = self.copy() 
 349          copy.to_undirected(*args, **kwds) 
 350          return copy 
 351   
 352 -    def delete_edges(self, *args, **kwds): 
 353          """Deletes some edges from the graph. 
 354   
 355          The set of edges to be deleted is determined by the positional and 
 356          keyword arguments. If any keyword argument is present, or the 
 357          first positional argument is callable, an edge 
 358          sequence is derived by calling L{EdgeSeq.select} with the same 
 359          positional and keyword arguments. Edges in the derived edge sequence 
 360          will be removed. Otherwise the first positional argument is considered 
 361          as follows: 
 362   
 363            - C{None} - deletes all edges 
 364            - a single integer - deletes the edge with the given ID 
 365            - a list of integers - deletes the edges denoted by the given IDs 
 366            - a list of 2-tuples - deletes the edges denoted by the given 
 367              source-target vertex pairs. When multiple edges are present 
 368              between a given source-target vertex pair, only one is removed. 
 369          """ 
 370          if len(args) == 0 and len(kwds) == 0: 
 371              raise ValueError("expected at least one argument") 
 372          if len(kwds)>0 or (hasattr(args[0], "__call__") and \ 
 373                  not isinstance(args[0], EdgeSeq)): 
 374              edge_seq = self.es(*args, **kwds) 
 375          else: 
 376              edge_seq = args[0] 
 377          return GraphBase.delete_edges(self, edge_seq) 
 378   
 379   
 380 -    def indegree(self, *args, **kwds): 
 381          """Returns the in-degrees in a list. 
 382   
 383          See L{degree} for possible arguments. 
 384          """ 
 385          kwds['mode'] = IN 
 386          return self.degree(*args, **kwds) 
 387   
 388 -    def outdegree(self, *args, **kwds): 
 389          """Returns the out-degrees in a list. 
 390   
 391          See L{degree} for possible arguments. 
 392          """ 
 393          kwds['mode'] = OUT 
 394          return self.degree(*args, **kwds) 
 395   
 396 -    def all_st_cuts(self, source, target): 
 397          """\ 
 398          Returns all the cuts between the source and target vertices in a 
 399          directed graph. 
 400   
 401          This function lists all edge-cuts between a source and a target vertex. 
 402          Every cut is listed exactly once. 
 403   
 404          @param source: the source vertex ID 
 405          @param target: the target vertex ID 
 406          @return: a list of L{Cut} objects. 
 407   
 408          @newfield ref: Reference 
 409          @ref: JS Provan and DR Shier: A paradigm for listing (s,t)-cuts in 
 410            graphs. Algorithmica 15, 351--372, 1996. 
 411          """ 
 412          return [Cut(self, cut=cut, partition=part) 
 413                  for cut, part in izip(*GraphBase.all_st_cuts(self, source, target))] 
 414   
 415 -    def all_st_mincuts(self, source, target, capacity=None): 
 416          """\ 
 417          Returns all the mincuts between the source and target vertices in a 
 418          directed graph. 
 419   
 420          This function lists all minimum edge-cuts between a source and a target 
 421          vertex. 
 422   
 423          @param source: the source vertex ID 
 424          @param target: the target vertex ID 
 425          @param capacity: the edge capacities (weights). If C{None}, all 
 426            edges have equal weight. May also be an attribute name. 
 427          @return: a list of L{Cut} objects. 
 428   
 429          @newfield ref: Reference 
 430          @ref: JS Provan and DR Shier: A paradigm for listing (s,t)-cuts in 
 431            graphs. Algorithmica 15, 351--372, 1996. 
 432          """ 
 433          value, cuts, parts = GraphBase.all_st_mincuts(self, source, target, capacity) 
 434          return [Cut(self, value, cut=cut, partition=part) 
 435                  for cut, part in izip(cuts, parts)] 
 436   
 437 -    def biconnected_components(self, return_articulation_points=False): 
 438          """\ 
 439          Calculates the biconnected components of the graph. 
 440   
 441          @param return_articulation_points: whether to return the articulation 
 442            points as well 
 443          @return: a L{VertexCover} object describing the biconnected components, 
 444            and optionally the list of articulation points as well 
 445          """ 
 446          if return_articulation_points: 
 447              trees, aps = GraphBase.biconnected_components(self, True) 
 448          else: 
 449              trees = GraphBase.biconnected_components(self, False) 
 450   
 451          clusters = [] 
 452          for tree in trees: 
 453              cluster = set() 
 454              for edge in self.es[tree]: 
 455                  cluster.update(edge.tuple) 
 456              clusters.append(sorted(cluster)) 
 457          clustering = VertexCover(self, clusters) 
 458   
 459          if return_articulation_points: 
 460              return clustering, aps 
 461          else: 
 462              return clustering 
 463      blocks = biconnected_components 
 464   
 465 -    def cohesive_blocks(self): 
 466          """cohesive_blocks() 
 467   
 468          Calculates the cohesive block structure of the graph. 
 469   
 470          Cohesive blocking is a method of determining hierarchical subsets of graph 
 471          vertices based on their structural cohesion (i.e. vertex connectivity). 
 472          For a given graph G, a subset of its vertices S is said to be maximally 
 473          k-cohesive if there is no superset of S with vertex connectivity greater 
 474          than or equal to k. Cohesive blocking is a process through which, given a 
 475          k-cohesive set of vertices, maximally l-cohesive subsets are recursively 
 476          identified with l > k. Thus a hierarchy of vertex subsets is obtained in 
 477          the end, with the entire graph G at its root. 
 478   
 479          @return: an instance of L{CohesiveBlocks}. See the documentation of 
 480            L{CohesiveBlocks} for more information. 
 481          @see: L{CohesiveBlocks} 
 482          """ 
 483          return CohesiveBlocks(self, *GraphBase.cohesive_blocks(self)) 
 484   
 485 -    def clusters(self, mode=STRONG): 
 486          """clusters(mode=STRONG) 
 487   
 488          Calculates the (strong or weak) clusters (connected components) for 
 489          a given graph. 
 490   
 491          @param mode: must be either C{STRONG} or C{WEAK}, depending on the 
 492            clusters being sought. Optional, defaults to C{STRONG}. 
 493          @return: a L{VertexClustering} object""" 
 494          return VertexClustering(self, GraphBase.clusters(self, mode)) 
 495      components = clusters 
 496   
 497 -    def degree_distribution(self, bin_width = 1, *args, **kwds): 
 498          """degree_distribution(bin_width=1, ...) 
 499   
 500          Calculates the degree distribution of the graph. 
 501   
 502          Unknown keyword arguments are directly passed to L{degree()}. 
 503   
 504          @param bin_width: the bin width of the histogram 
 505          @return: a histogram representing the degree distribution of the 
 506            graph. 
 507          """ 
 508          result = Histogram(bin_width, self.degree(*args, **kwds)) 
 509          return result 
 510   
 511 -    def dyad_census(self, *args, **kwds): 
 512          """dyad_census() 
 513   
 514          Calculates the dyad census of the graph. 
 515   
 516          Dyad census means classifying each pair of vertices of a directed 
 517          graph into three categories: mutual (there is an edge from I{a} to 
 518          I{b} and also from I{b} to I{a}), asymmetric (there is an edge 
 519          from I{a} to I{b} or from I{b} to I{a} but not the other way round) 
 520          and null (there is no connection between I{a} and I{b}). 
 521   
 522          @return: a L{DyadCensus} object. 
 523          @newfield ref: Reference 
 524          @ref: Holland, P.W. and Leinhardt, S.  (1970).  A Method for Detecting 
 525            Structure in Sociometric Data.  American Journal of Sociology, 70, 
 526            492-513. 
 527          """ 
 528          return DyadCensus(GraphBase.dyad_census(self, *args, **kwds)) 
 529   
 530 -    def get_adjacency(self, type=GET_ADJACENCY_BOTH, attribute=None, \ 
 531              default=0, eids=False): 
 532          """Returns the adjacency matrix of a graph. 
 533   
 534          @param type: either C{GET_ADJACENCY_LOWER} (uses the lower 
 535            triangle of the matrix) or C{GET_ADJACENCY_UPPER} 
 536            (uses the upper triangle) or C{GET_ADJACENCY_BOTH} 
 537            (uses both parts). Ignored for directed graphs. 
 538          @param attribute: if C{None}, returns the ordinary adjacency 
 539            matrix. When the name of a valid edge attribute is given 
 540            here, the matrix returned will contain the default value 
 541            at the places where there is no edge or the value of the 
 542            given attribute where there is an edge. Multiple edges are 
 543            not supported, the value written in the matrix in this case 
 544            will be unpredictable. This parameter is ignored if 
 545            I{eids} is C{True} 
 546          @param default: the default value written to the cells in the 
 547            case of adjacency matrices with attributes. 
 548          @param eids: specifies whether the edge IDs should be returned 
 549            in the adjacency matrix. Since zero is a valid edge ID, the 
 550            cells in the matrix that correspond to unconnected vertex 
 551            pairs will contain -1 instead of 0 if I{eids} is C{True}. 
 552            If I{eids} is C{False}, the number of edges will be returned 
 553            in the matrix for each vertex pair. 
 554          @return: the adjacency matrix as a L{Matrix}. 
 555          """ 
 556          if type != GET_ADJACENCY_LOWER and type != GET_ADJACENCY_UPPER and \ 
 557            type != GET_ADJACENCY_BOTH: 
 558              # Maybe it was called with the first argument as the attribute name 
 559              type, attribute = attribute, type 
 560              if type is None: 
 561                  type = GET_ADJACENCY_BOTH 
 562   
 563          if eids: 
 564              result = Matrix(GraphBase.get_adjacency(self, type, eids)) 
 565              result -= 1 
 566              return result 
 567   
 568          if attribute is None: 
 569              return Matrix(GraphBase.get_adjacency(self, type)) 
 570   
 571          if attribute not in self.es.attribute_names(): 
 572              raise ValueError("Attribute does not exist") 
 573   
 574          data = [[default] * self.vcount() for _ in xrange(self.vcount())] 
 575   
 576          if self.is_directed(): 
 577              for edge in self.es: 
 578                  data[edge.source][edge.target] = edge[attribute] 
 579              return Matrix(data) 
 580   
 581          if type == GET_ADJACENCY_BOTH: 
 582              for edge in self.es: 
 583                  source, target = edge.tuple 
 584                  data[source][target] = edge[attribute] 
 585                  data[target][source] = edge[attribute] 
 586          elif type == GET_ADJACENCY_UPPER: 
 587              for edge in self.es: 
 588                  data[min(edge.tuple)][max(edge.tuple)] = edge[attribute] 
 589          else: 
 590              for edge in self.es: 
 591                  data[max(edge.tuple)][min(edge.tuple)] = edge[attribute] 
 592   
 593          return Matrix(data) 
 594   
 595 -    def get_adjacency_sparse(self, attribute=None): 
 596          """Returns the adjacency matrix of a graph as scipy csr matrix. 
 597          @param attribute: if C{None}, returns the ordinary adjacency 
 598            matrix. When the name of a valid edge attribute is given 
 599            here, the matrix returned will contain the default value 
 600            at the places where there is no edge or the value of the 
 601            given attribute where there is an edge. 
 602          @return: the adjacency matrix as a L{scipy.sparse.csr_matrix}.""" 
 603          try: 
 604              from scipy.sparse import csr_matrix 
 605          except ImportError: 
 606              raise ImportError('You should install scipy package in order to use this function') 
 607   
 608          edges = self.get_edgelist() 
 609          if attribute is None: 
 610              weights = [1] * len(edges) 
 611          else: 
 612              if attribute not in self.es.attribute_names(): 
 613                  raise ValueError("Attribute does not exist") 
 614   
 615              weights = self.es[attribute] 
 616   
 617          N = self.vcount() 
 618          sparse_matrix = csr_matrix((weights, zip(*edges)), shape=(N, N)) 
 619   
 620          if not self.is_directed(): 
 621              sparse_matrix = sparse_matrix + sparse_matrix.T 
 622              di = np.diag_indices(len(edges)) 
 623              sparse_matrix[di] /= 2 
 624          return sparse_matrix 
 625   
 626 -    def get_adjlist(self, mode=OUT): 
 627          """get_adjlist(mode=OUT) 
 628   
 629          Returns the adjacency list representation of the graph. 
 630   
 631          The adjacency list representation is a list of lists. Each item of the 
 632          outer list belongs to a single vertex of the graph. The inner list 
 633          contains the neighbors of the given vertex. 
 634   
 635          @param mode: if L{OUT}, returns the successors of the vertex. If 
 636            L{IN}, returns the predecessors of the vertex. If L{ALL}, both 
 637            the predecessors and the successors will be returned. Ignored 
 638            for undirected graphs. 
 639          """ 
 640          return [self.neighbors(idx, mode) for idx in xrange(self.vcount())] 
 641   
 642 -    def get_adjedgelist(self, *args, **kwds): 
 643          """get_adjedgelist(mode=OUT) 
 644   
 645          Returns the incidence list representation of the graph. 
 646   
 647          @deprecated: replaced by L{Graph.get_inclist()} since igraph 0.6 
 648          @see: Graph.get_inclist() 
 649          """ 
 650          deprecated("Graph.get_adjedgelist() is deprecated since igraph 0.6, " 
 651                     "please use Graph.get_inclist() instead") 
 652          return self.get_inclist(*args, **kwds) 
 653   
 654 -    def get_all_simple_paths(self, v, to=None, cutoff=-1, mode=OUT): 
 655          """get_all_simple_paths(v, to=None, mode=OUT) 
 656   
 657          Calculates all the simple paths from a given node to some other nodes 
 658          (or all of them) in a graph. 
 659   
 660          A path is simple if its vertices are unique, i.e. no vertex is visited 
 661          more than once. 
 662   
 663          Note that potentially there are exponentially many paths between two 
 664          vertices of a graph, especially if your graph is lattice-like. In this 
 665          case, you may run out of memory when using this function. 
 666   
 667          @param v: the source for the calculated paths 
 668          @param to: a vertex selector describing the destination for the calculated 
 669            paths. This can be a single vertex ID, a list of vertex IDs, a single 
 670            vertex name, a list of vertex names or a L{VertexSeq} object. C{None} 
 671            means all the vertices. 
 672          @param cutoff: maximum length of path that is considered. If negative, 
 673            paths of all lengths are considered. 
 674          @param mode: the directionality of the paths. L{IN} means to calculate 
 675            incoming paths, L{OUT} means to calculate outgoing paths, L{ALL} means 
 676            to calculate both ones. 
 677          @return: all of the simple paths from the given node to every other 
 678            reachable node in the graph in a list. Note that in case of mode=L{IN}, 
 679            the vertices in a path are returned in reversed order! 
 680          """ 
 681          paths = self._get_all_simple_paths(v, to, cutoff, mode) 
 682          prev = 0 
 683          result = [] 
 684          for index, item in enumerate(paths): 
 685              if item < 0: 
 686                  result.append(paths[prev:index]) 
 687                  prev = index+1 
 688          return result 
 689   
 690 -    def get_inclist(self, mode=OUT): 
 691          """get_inclist(mode=OUT) 
 692   
 693          Returns the incidence list representation of the graph. 
 694   
 695          The incidence list representation is a list of lists. Each 
 696          item of the outer list belongs to a single vertex of the graph. 
 697          The inner list contains the IDs of the incident edges of the 
 698          given vertex. 
 699   
 700          @param mode: if L{OUT}, returns the successors of the vertex. If 
 701            L{IN}, returns the predecessors of the vertex. If L{ALL}, both 
 702            the predecessors and the successors will be returned. Ignored 
 703            for undirected graphs. 
 704          """ 
 705          return [self.incident(idx, mode) for idx in xrange(self.vcount())] 
 706   
 707 -    def gomory_hu_tree(self, capacity=None, flow="flow"): 
 708          """gomory_hu_tree(capacity=None, flow="flow") 
 709   
 710          Calculates the Gomory-Hu tree of an undirected graph with optional 
 711          edge capacities. 
 712   
 713          The Gomory-Hu tree is a concise representation of the value of all the 
 714          maximum flows (or minimum cuts) in a graph. The vertices of the tree 
 715          correspond exactly to the vertices of the original graph in the same order. 
 716          Edges of the Gomory-Hu tree are annotated by flow values.  The value of 
 717          the maximum flow (or minimum cut) between an arbitrary (u,v) vertex 
 718          pair in the original graph is then given by the minimum flow value (i.e. 
 719          edge annotation) along the shortest path between u and v in the 
 720          Gomory-Hu tree. 
 721   
 722          @param capacity: the edge capacities (weights). If C{None}, all 
 723            edges have equal weight. May also be an attribute name. 
 724          @param flow: the name of the edge attribute in the returned graph 
 725            in which the flow values will be stored. 
 726          @return: the Gomory-Hu tree as a L{Graph} object. 
 727          """ 
 728          graph, flow_values = GraphBase.gomory_hu_tree(self, capacity) 
 729          graph.es[flow] = flow_values 
 730          return graph 
 731   
 732 -    def is_named(self): 
 733          """is_named() 
 734   
 735          Returns whether the graph is named, i.e., whether it has a "name" 
 736          vertex attribute. 
 737          """ 
 738          return "name" in self.vertex_attributes() 
 739   
 740 -    def is_weighted(self): 
 741          """is_weighted() 
 742   
 743          Returns whether the graph is weighted, i.e., whether it has a "weight" 
 744          edge attribute. 
 745          """ 
 746          return "weight" in self.edge_attributes() 
 747   
 748 -    def maxflow(self, source, target, capacity=None): 
 749          """maxflow(source, target, capacity=None) 
 750   
 751          Returns a maximum flow between the given source and target vertices 
 752          in a graph. 
 753   
 754          A maximum flow from I{source} to I{target} is an assignment of 
 755          non-negative real numbers to the edges of the graph, satisfying 
 756          two properties: 
 757   
 758              1. For each edge, the flow (i.e. the assigned number) is not 
 759                 more than the capacity of the edge (see the I{capacity} 
 760                 argument) 
 761   
 762              2. For every vertex except the source and the target, the 
 763                 incoming flow is the same as the outgoing flow. 
 764   
 765          The value of the flow is the incoming flow of the target or the 
 766          outgoing flow of the source (which are equal). The maximum flow 
 767          is the maximum possible such value. 
 768   
 769          @param capacity: the edge capacities (weights). If C{None}, all 
 770            edges have equal weight. May also be an attribute name. 
 771          @return: a L{Flow} object describing the maximum flow 
 772          """ 
 773          return Flow(self, *GraphBase.maxflow(self, source, target, capacity)) 
 774   
 775 -    def mincut(self, source=None, target=None, capacity=None): 
 776          """mincut(source=None, target=None, capacity=None) 
 777   
 778          Calculates the minimum cut between the given source and target vertices 
 779          or within the whole graph. 
 780   
 781          The minimum cut is the minimum set of edges that needs to be removed to 
 782          separate the source and the target (if they are given) or to disconnect the 
 783          graph (if neither the source nor the target are given). The minimum is 
 784          calculated using the weights (capacities) of the edges, so the cut with 
 785          the minimum total capacity is calculated. 
 786   
 787          For undirected graphs and no source and target, the method uses the 
 788          Stoer-Wagner algorithm. For a given source and target, the method uses the 
 789          push-relabel algorithm; see the references below. 
 790   
 791          @param source: the source vertex ID. If C{None}, the target must also be 
 792            C{None} and the calculation will be done for the entire graph (i.e. 
 793            all possible vertex pairs). 
 794          @param target: the target vertex ID. If C{None}, the source must also be 
 795            C{None} and the calculation will be done for the entire graph (i.e. 
 796            all possible vertex pairs). 
 797          @param capacity: the edge capacities (weights). If C{None}, all 
 798            edges have equal weight. May also be an attribute name. 
 799          @return: a L{Cut} object describing the minimum cut 
 800          """ 
 801          return Cut(self, *GraphBase.mincut(self, source, target, capacity)) 
 802   
 803 -    def st_mincut(self, source, target, capacity=None): 
 804          """st_mincut(source, target, capacity=None) 
 805   
 806          Calculates the minimum cut between the source and target vertices in a 
 807          graph. 
 808   
 809          @param source: the source vertex ID 
 810          @param target: the target vertex ID 
 811          @param capacity: the capacity of the edges. It must be a list or a valid 
 812            attribute name or C{None}. In the latter case, every edge will have the 
 813            same capacity. 
 814          @return: the value of the minimum cut, the IDs of vertices in the 
 815            first and second partition, and the IDs of edges in the cut, 
 816            packed in a 4-tuple 
 817          """ 
 818          return Cut(self, *GraphBase.st_mincut(self, source, target, capacity)) 
 819   
 820 -    def modularity(self, membership, weights=None): 
 821          """modularity(membership, weights=None) 
 822   
 823          Calculates the modularity score of the graph with respect to a given 
 824          clustering. 
 825   
 826          The modularity of a graph w.r.t. some division measures how good the 
 827          division is, or how separated are the different vertex types from each 
 828          other. It's defined as M{Q=1/(2m)*sum(Aij-ki*kj/(2m)delta(ci,cj),i,j)}. 
 829          M{m} is the number of edges, M{Aij} is the element of the M{A} 
 830          adjacency matrix in row M{i} and column M{j}, M{ki} is the degree of 
 831          node M{i}, M{kj} is the degree of node M{j}, and M{Ci} and C{cj} are 
 832          the types of the two vertices (M{i} and M{j}). M{delta(x,y)} is one iff 
 833          M{x=y}, 0 otherwise. 
 834   
 835          If edge weights are given, the definition of modularity is modified as 
 836          follows: M{Aij} becomes the weight of the corresponding edge, M{ki} 
 837          is the total weight of edges adjacent to vertex M{i}, M{kj} is the 
 838          total weight of edges adjacent to vertex M{j} and M{m} is the total 
 839          edge weight in the graph. 
 840   
 841          @param membership: a membership list or a L{VertexClustering} object 
 842          @param weights: optional edge weights or C{None} if all edges are 
 843            weighed equally. Attribute names are also allowed. 
 844          @return: the modularity score 
 845   
 846          @newfield ref: Reference 
 847          @ref: MEJ Newman and M Girvan: Finding and evaluating community 
 848            structure in networks. Phys Rev E 69 026113, 2004. 
 849          """ 
 850          if isinstance(membership, VertexClustering): 
 851              if membership.graph != self: 
 852                  raise ValueError("clustering object belongs to another graph") 
 853              return GraphBase.modularity(self, membership.membership, weights) 
 854          else: 
 855              return GraphBase.modularity(self, membership, weights) 
 856   
 857 -    def path_length_hist(self, directed=True): 
 858          """path_length_hist(directed=True) 
 859   
 860          Returns the path length histogram of the graph 
 861   
 862          @param directed: whether to consider directed paths. Ignored for 
 863            undirected graphs. 
 864          @return: a L{Histogram} object. The object will also have an 
 865            C{unconnected} attribute that stores the number of unconnected 
 866            vertex pairs (where the second vertex can not be reached from 
 867            the first one). The latter one will be of type long (and not 
 868            a simple integer), since this can be I{very} large. 
 869          """ 
 870          data, unconn = GraphBase.path_length_hist(self, directed) 
 871          hist = Histogram(bin_width=1) 
 872          for i, length in enumerate(data): 
 873              hist.add(i+1, length) 
 874          hist.unconnected = long(unconn) 
 875          return hist 
 876   
 877 -    def pagerank(self, vertices=None, directed=True, damping=0.85, 
 878                   weights=None, arpack_options=None, implementation="prpack", 
 879                   niter=1000, eps=0.001): 
 880          """Calculates the Google PageRank values of a graph. 
 881   
 882          @param vertices: the indices of the vertices being queried. 
 883            C{None} means all of the vertices. 
 884          @param directed: whether to consider directed paths. 
 885          @param damping: the damping factor. M{1-damping} is the PageRank value 
 886            for nodes with no incoming links. It is also the probability of 
 887            resetting the random walk to a uniform distribution in each step. 
 888          @param weights: edge weights to be used. Can be a sequence or iterable 
 889            or even an edge attribute name. 
 890          @param arpack_options: an L{ARPACKOptions} object used to fine-tune 
 891            the ARPACK eigenvector calculation. If omitted, the module-level 
 892            variable called C{arpack_options} is used. This argument is 
 893            ignored if not the ARPACK implementation is used, see the 
 894            I{implementation} argument. 
 895          @param implementation: which implementation to use to solve the 
 896            PageRank eigenproblem. Possible values are: 
 897              - C{"prpack"}: use the PRPACK library. This is a new 
 898                implementation in igraph 0.7 
 899              - C{"arpack"}: use the ARPACK library. This implementation 
 900                was used from version 0.5, until version 0.7. 
 901              - C{"power"}: use a simple power method. This is the 
 902                implementation that was used before igraph version 0.5. 
 903          @param niter: The number of iterations to use in the power method 
 904            implementation. It is ignored in the other implementations 
 905          @param eps: The power method implementation will consider the 
 906            calculation as complete if the difference of PageRank values between 
 907            iterations change less than this value for every node. It is 
 908            ignored by the other implementations. 
 909          @return: a list with the Google PageRank values of the specified 
 910            vertices.""" 
 911          if arpack_options is None: 
 912              arpack_options = _igraph.arpack_options 
 913          return self.personalized_pagerank(vertices, directed, damping, None,\ 
 914                                            None, weights, arpack_options, \ 
 915                                            implementation, niter, eps) 
 916   
 917 -    def spanning_tree(self, weights=None, return_tree=True): 
 918          """Calculates a minimum spanning tree for a graph. 
 919   
 920          @param weights: a vector containing weights for every edge in 
 921            the graph. C{None} means that the graph is unweighted. 
 922          @param return_tree: whether to return the minimum spanning tree (when 
 923            C{return_tree} is C{True}) or to return the IDs of the edges in 
 924            the minimum spanning tree instead (when C{return_tree} is C{False}). 
 925            The default is C{True} for historical reasons as this argument was 
 926            introduced in igraph 0.6. 
 927          @return: the spanning tree as a L{Graph} object if C{return_tree} 
 928            is C{True} or the IDs of the edges that constitute the spanning 
 929            tree if C{return_tree} is C{False}. 
 930   
 931          @newfield ref: Reference 
 932          @ref: Prim, R.C.: I{Shortest connection networks and some 
 933            generalizations}. Bell System Technical Journal 36:1389-1401, 1957. 
 934          """ 
 935          result = GraphBase._spanning_tree(self, weights) 
 936          if return_tree: 
 937              return self.subgraph_edges(result, delete_vertices=False) 
 938          return result 
 939   
 940 -    def transitivity_avglocal_undirected(self, mode="nan", weights=None): 
 941          """Calculates the average of the vertex transitivities of the graph. 
 942   
 943          In the unweighted case, the transitivity measures the probability that 
 944          two neighbors of a vertex are connected. In case of the average local 
 945          transitivity, this probability is calculated for each vertex and then 
 946          the average is taken. Vertices with less than two neighbors require 
 947          special treatment, they will either be left out from the calculation 
 948          or they will be considered as having zero transitivity, depending on 
 949          the I{mode} parameter. The calculation is slightly more involved for 
 950          weighted graphs; in this case, weights are taken into account according 
 951          to the formula of Barrat et al (see the references). 
 952   
 953          Note that this measure is different from the global transitivity 
 954          measure (see L{transitivity_undirected()}) as it simply takes the 
 955          average local transitivity across the whole network. 
 956   
 957          @param mode: defines how to treat vertices with degree less than two. 
 958            If C{TRANSITIVITY_ZERO} or C{"zero"}, these vertices will have zero 
 959            transitivity. If C{TRANSITIVITY_NAN} or C{"nan"}, these vertices 
 960            will be excluded from the average. 
 961          @param weights: edge weights to be used. Can be a sequence or iterable 
 962            or even an edge attribute name. 
 963   
 964          @see: L{transitivity_undirected()}, L{transitivity_local_undirected()} 
 965          @newfield ref: Reference 
 966          @ref: Watts DJ and Strogatz S: I{Collective dynamics of small-world 
 967            networks}. Nature 393(6884):440-442, 1998. 
 968          @ref: Barrat A, Barthelemy M, Pastor-Satorras R and Vespignani A: 
 969            I{The architecture of complex weighted networks}. PNAS 101, 3747 (2004). 
 970            U{http://arxiv.org/abs/cond-mat/0311416}. 
 971          """ 
 972          if weights is None: 
 973              return GraphBase.transitivity_avglocal_undirected(self, mode) 
 974   
 975          xs = self.transitivity_local_undirected(mode=mode, weights=weights) 
 976          return sum(xs) / float(len(xs)) 
 977   
 978 -    def triad_census(self, *args, **kwds): 
 979          """triad_census() 
 980   
 981          Calculates the triad census of the graph. 
 982   
 983          @return: a L{TriadCensus} object. 
 984          @newfield ref: Reference 
 985          @ref: Davis, J.A. and Leinhardt, S.  (1972).  The Structure of 
 986            Positive Interpersonal Relations in Small Groups.  In: 
 987            J. Berger (Ed.), Sociological Theories in Progress, Volume 2, 
 988            218-251. Boston: Houghton Mifflin. 
 989          """ 
 990          return TriadCensus(GraphBase.triad_census(self, *args, **kwds)) 
 991   
 992      # Automorphisms 
 993 -    def count_automorphisms_vf2(self, color=None, edge_color=None, 
 994              node_compat_fn=None, edge_compat_fn=None): 
 995          """Returns the number of automorphisms of the graph. 
 996   
 997          This function simply calls C{count_isomorphisms_vf2} with the graph 
 998          itself. See C{count_isomorphisms_vf2} for an explanation of the 
 999          parameters. 
1000   
1001          @return: the number of automorphisms of the graph 
1002          @see: Graph.count_isomorphisms_vf2 
1003          """ 
1004          return self.count_isomorphisms_vf2(self, color1=color, color2=color, 
1005                  edge_color1=edge_color, edge_color2=edge_color, 
1006                  node_compat_fn=node_compat_fn, edge_compat_fn=edge_compat_fn) 
1007   
1008 -    def get_automorphisms_vf2(self, color=None, edge_color=None, 
1009              node_compat_fn=None, edge_compat_fn=None): 
1010          """Returns all the automorphisms of the graph 
1011   
1012          This function simply calls C{get_isomorphisms_vf2} with the graph 
1013          itself. See C{get_isomorphisms_vf2} for an explanation of the 
1014          parameters. 
1015   
1016          @return: a list of lists, each item containing a possible mapping 
1017            of the graph vertices to itself according to the automorphism 
1018          @see: Graph.get_isomorphisms_vf2 
1019          """ 
1020          return self.get_isomorphisms_vf2(self, color1=color, color2=color, 
1021                  edge_color1=edge_color, edge_color2=edge_color, 
1022                  node_compat_fn=node_compat_fn, edge_compat_fn=edge_compat_fn) 
1023   
1024      # Various clustering algorithms -- mostly wrappers around GraphBase 
1025 -    def community_fastgreedy(self, weights=None): 
1026          """Community structure based on the greedy optimization of modularity. 
1027   
1028          This algorithm merges individual nodes into communities in a way that 
1029          greedily maximizes the modularity score of the graph. It can be proven 
1030          that if no merge can increase the current modularity score, the 
1031          algorithm can be stopped since no further increase can be achieved. 
1032   
1033          This algorithm is said to run almost in linear time on sparse graphs. 
1034   
1035          @param weights: edge attribute name or a list containing edge 
1036            weights 
1037          @return: an appropriate L{VertexDendrogram} object. 
1038   
1039          @newfield ref: Reference 
1040          @ref: A Clauset, MEJ Newman and C Moore: Finding community structure 
1041            in very large networks. Phys Rev E 70, 066111 (2004). 
1042          """ 
1043          merges, qs = GraphBase.community_fastgreedy(self, weights) 
1044   
1045          # qs may be shorter than |V|-1 if we are left with a few separated 
1046          # communities in the end; take this into account 
1047          diff = self.vcount() - len(qs) 
1048          qs.reverse() 
1049          if qs: 
1050              optimal_count = qs.index(max(qs)) + diff + 1 
1051          else: 
1052              optimal_count = diff 
1053   
1054          return VertexDendrogram(self, merges, optimal_count, 
1055                  modularity_params=dict(weights=weights)) 
1056   