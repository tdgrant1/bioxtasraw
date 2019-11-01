# -*- coding: utf-8 -*-
#
# BioXTAS RAW documentation build configuration file, created by
# sphinx-quickstart on Thu Aug 10 11:22:37 2017.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
on_rtd = os.environ.get('READTHEDOCS') == 'True'
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.mathjax']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'
tutorial = 'tutorial'
manual = 'manual'
win_install = 'install/win_install'
mac_install = 'install/mac_install'
linux_install = 'install/linux_install'

# General information about the project.
project = u'BioXTAS RAW'
copyright = u'2017-2019, Jesse B. Hopkins'
author = u'Jesse B. Hopkins'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = u'1.6.3'
# The full version, including alpha/beta/rc tags.
release = u'1.6.3'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

if on_rtd:
    html_theme = 'default'
else:
    html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    'description':'SAXS data analysis software',
}
if html_theme == 'alabaster':
    html_theme_options['fixed_sidebar'] = False
    html_theme_options['sidebar_collapse'] = True
    html_theme_options['show_related'] = True

if html_theme == 'alabaster':
    html_sidebars = {
        '**': [
            'about.html',
            'navigation.html',
            'relations.html',
            'searchbox.html',
            # 'donate.html',
        ]
    }

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'BioXTASRAWdoc'


# -- Options for LaTeX output ---------------------------------------------

preamble = r"""

\ifdefined\fancyhf\pagestyle{normal}\fi

"""

tableofcontents = r"""
\pagenumbering{roman}%
\pagestyle{plain}%
\begingroup
  \tableofcontents
\endgroup
% before resetting page counter, let's do the right thing.
\clearpage
\pagenumbering{arabic}%

"""

latex_elements = {
    'classoptions': ',openany,oneside',
    'preamble': preamble,
    'tableofcontents': tableofcontents,
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
if on_rtd:
    latex_documents = [
        (master_doc, 'BioXTASRAW.tex', u'BioXTAS RAW Documentation',
            u'Jesse B. Hopkins', 'manual'),
    ]
else:
    latex_documents = [
        # (master_doc, 'BioXTASRAW.tex', u'BioXTAS RAW Documentation',
        #     u'Jesse B. Hopkins', 'manual'),
        (tutorial, 'raw_tutorial.tex', u'BioXTAS RAW Tutorial',
            u'Jesse B. Hopkins', 'howto'),
        (manual, 'raw_manual.tex', u'BioXTAS RAW Manual',
            u'Jesse B. Hopkins', 'manual'),
        (win_install, 'win_install.tex', u'BioXTAS RAW Windows Install Instructions',
            u'Jesse B. Hopkins', 'howto' ),
        (mac_install, 'mac_install.tex', u'BioXTAS RAW Mac Install Instructions',
            u'Jesse B. Hopkins', 'howto'),
        (linux_install, 'linux_install.tex', u'BioXTAS RAW Linux Install Instructions',
            u'Jesse B. Hopkins', 'howto'),
    ]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'bioxtasraw', u'BioXTAS RAW Documentation',
     [author], 1),
    ]


# The name of an image file (relative to this directory) to place at the top of
# the title page.
#
# latex_logo = 'tutorial/images/raw_mainplot.png'
latex_logo = ''


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'BioXTASRAW', u'BioXTAS RAW Documentation',
     author, 'BioXTASRAW', 'One line description of project.',
     'Miscellaneous'),
]



# -- Options for Epub output ----------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


