
def autodoc_skip_member(app, what, name, obj, skip, options):
    if what == 'class' and skip and name in ('__init__',) and obj.__doc__:
        return False
    else:
        return skip

def setup(app):
    app.connect('autodoc-skip-member', autodoc_skip_member)
