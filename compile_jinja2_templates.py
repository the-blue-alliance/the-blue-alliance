from template_engine import jinja2_engine

path = 'templates_jinja2_compiled.zip'
print "Compiling jinja2 templates to: {}".format(path)
jinja2_engine.get_jinja_env(force_filesystemloader=True).compile_templates(
    path, ignore_errors=False)
print "Compilation complete!"
