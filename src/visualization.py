import html
from pyvis.network import Network

COLORS = {'IES':'#2563eb','Curso':'#8b5cf6','OfertaCurso':'#ea580c','Municipio':'#059669','UF':'#0d9488','Trecho':'#db2777','Documento':'#64748b'}

def render_graph(context):
    net = Network(height='570px',width='100%',directed=True,bgcolor='#f8fafc',font_color='#172033',cdn_resources='in_line')
    for node in context['nodes']:
        name = node['name']
        net.add_node(node['id'],label=name[:44]+('…' if len(name)>44 else ''),
            title=html.escape(f"{node['kind']}: {name}\nID: {node['key']}\nFonte: {node['source']}"),
            color=COLORS.get(node['kind'],'#94a3b8'),size=12+80*node['pagerank'])
    for edge in context['edges']:
        net.add_edge(edge['source'],edge['target'],title=html.escape(edge['type']),label=edge['type'],color='#cbd5e1')
    net.set_options('''{"physics":{"solver":"forceAtlas2Based","stabilization":{"iterations":160}},"interaction":{"hover":true,"navigationButtons":true},"edges":{"font":{"size":8},"smooth":false},"nodes":{"font":{"size":11}}}''')
    return net.generate_html(notebook=False)
