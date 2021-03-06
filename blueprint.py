#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging as log
import importlib

from globe import Globe as globe

class Blueprint():

    def __init__(self, config={}):

        self.variable = config.get('variable', tuple())
        self.snippet = config.get('snippet', "")
        self.dependency = config.get('dependency',"")
        self.factor = config.get('factor',{})
        self.macro = config.get('macro',"")

    def get_factor(self, **kwargs):
        factors = {}
        for (fac, (facmethod, var)) in self.factor.items():
            if not var in self.variable:
                log.error("No such variable '%s'" % var)
                continue

            if not var in kwargs:
                log.critical("Variable '%s' not provided" % var)
                raise ValueError
            
            if facmethod.startswith('$'):
                factors[fac] = FacMethod.find(facmethod[1:],kwargs[var])
            elif facmethod == '':
                factors[fac] = kwargs[var]
            else:
                log.error("External factor method not implemented") #TODO: 外部生成要素方法
                continue
        return factors

    def get_fragment(self, **kwargs):
        factors = self.get_factor(**kwargs)
        fragment = ""

        try:
            fragment = self.snippet.format_map(factors)
        except KeyError as err:
            log.critical("Factor and snippet not matching, lacking key '%s'"%str(err))

        return fragment

    def do_macro(self, **kwargs):
        if self.macro.startswith('$'):
            Macro.find(self.macro[1:])(self.get_factor(**kwargs))
            return
        elif self.macro == '':
            log.debug("No macro.")
            return
        else:
            log.error("External macro method not implemented") #TODO: 外部宏
            return

    def to_dict(self):
        dict_blueprint = {
        'variable': self.variable,
        'dependency': self.dependency,
        'factor': self.factor,
        'snippet': self.snippet,
        'macro': self.macro
        }
        return dict_blueprint
class FacMethod(): # 要素生成相关方法
    @staticmethod
    def find(facMethod, arg=None):
        strutil = importlib.import_module("util").StrUtil
        try:
            if arg == "": arg = "untitled"
            FacMethod.method = strutil.__dict__[facMethod]
            return FacMethod.method(arg)
        except KeyError:
            log.error("No such built-in forging method '%s'" % facMethod)
            return lambda string: string

class Macro():  # 执行宏的方法
    @staticmethod
    def find(macro):
        if macro == "inkscape":
            inkscape = importlib.import_module("inkscape_control")
            return inkscape.create
        else:
            log.error("No such built-in macro '%s'" % macro)
            return lambda factors: None

def default(): # 默认蓝图
    default_dependency = r'''\usepackage{import}
\usepackage{float}
\usepackage{pdfpages}
%\usepackage{transparent}
\usepackage{xcolor}

\newcommand{\incfig}[1]{%
    \def\svgwidth{\columnwidth}
    \import{./figures/}{#1.pdf_tex}
}
%\pdfsuppresswarningpagegroup=1
%在中文的ctex被xelatex编译的环境下注释掉的项会出错;但是如果你使用pdflatex可以加上.
%程序会自动给你创建(如果没有的话)图片存放目录figures.
'''

    default_snippet = r'''\begin{{figure}}[ht]
    \centering
    \incfig{{{fileName}}}
    \caption{{{caption}}}
    \label{{fig:{label}}}
\end{{figure}}
'''

    default_blueprint = Blueprint({
        'variable': ('name',),
        'dependency': default_dependency,
        'factor': {
            'caption': ('$caption', 'name'),
            'fileName': ('$fileName', 'name'),
            'label': ('$label', 'name')
        },
        'snippet': default_snippet,
        'macro': '$inkscape'
    })

    globe.blueprint = default_blueprint
    log.info("Default blueprint loaded")

def show_blueprint():
    if globe.blueprint == None:
        log.critical("No blueprint loaded!")
        return

    text_dependency = globe.blueprint.dependency
    if text_dependency == None: text_dependency = r"% No dependency"

    field_dependency = globe.ui['field']['dependency']
    field_dependency.hinting = False
    field_dependency.content = text_dependency
    log.debug(field_dependency.content)

def export_blueprint(path):
    if globe.blueprint == None:
        log.critical("No blueprint loaded!")
        return
    
    dict_blueprint = globe.blueprint.to_dict()
    dict_blueprint['type'] = 'WW-BLUEPRINT'
    log.debug(dict_blueprint)

    with open(path, "w", encoding="utf-8") as file_blueprint:
        json.dump(dict_blueprint, file_blueprint, ensure_ascii=False, indent=4)
    
    log.info("Blueprint exported at {}".format(path))

def import_blueprint(path):
    with open(path, "r", encoding="utf-8") as file_blueprint:
        dict_blueprint = json.load(file_blueprint)

    try:
        if dict_blueprint.get('type') == 'WW-BLUEPRINT':
            globe.blueprint = Blueprint(dict_blueprint)
            show_blueprint()
        else:
            return -1
    except:
        return -1
    else:
        return 0