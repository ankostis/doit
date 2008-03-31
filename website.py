"""dodo file create website html files"""

import glob

from docutils.core import publish_parts
from mako import lookup, template


# generate API docs.
def task_epydoc():
    srcFiles = glob.glob("lib/doit/*.py")
    return {'action':"epydoc --config epydoc.config",
            'dependencies': srcFiles}


###### helper functions #####################

def rst2body(rstFile,bodyFile):
    """convert reStructured file to html and extract only the body of the html.

    @param rstFile: input rst file path
    @param bodyFile: output htmlt body file path
    """
    input = open(rstFile)
    try:
        rst = input.read()
    finally:
        input.close()
        
    output = open(bodyFile,"w")
    output.write(publish_parts(rst,writer_name='html')['body'])
    output.close()
    return True


def mako2html(bodyFile,htmlFile):
    mylookup = lookup.TemplateLookup(directories=['.'])
    mytemplate = template.Template("""
      <%%include file="doc/templates/header.txt"/> 
      <%%include file="%s"/> 
      """% bodyFile, 
      lookup=mylookup)

    output = open(htmlFile,"w")
    output.write(mytemplate.render())
    output.close()    
    return True



########## build site ####################

rstPath = "doc/"
tempPath = "doc/temp/" 
htmlPath = "doc/html/"
templatePath = "doc/templates/"
docFiles = [f[4:-4] for f in glob.glob('doc/*.txt')]

baseTemplate = templatePath + "base.mako"


def task_rst():
    for rst in docFiles:                
        source = rstPath + rst + ".txt"
        target = tempPath + rst + ".html"
        yield {'action':rst2body,
               'name':source,
               'args':[source, target],
               'dependencies':[source],
               'targets':[target]}


def task_html():
    for body in docFiles:
        source = tempPath + body + ".html"
        target = htmlPath + body + ".html"
        yield {'action':mako2html,
               'name':source,
               'args':[source, target],
               'dependencies':[source],
               'targets':[target]}
